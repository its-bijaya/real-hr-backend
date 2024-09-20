import os

import magic
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import filters
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.generics import get_object_or_404
from django.db.models import Q, F, Exists, OuterRef
from django.db.models.functions import Concat
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    MultipleChoiceFilter,
)

from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.mixins.viewset_mixins import (
    CreateViewSetMixin,
    ListRetrieveViewSetMixin,
    ListRetrieveUpdateViewSetMixin,
    OrganizationMixin
)
from irhrs.core.utils import get_system_admin
from irhrs.forms.api.v1.serializers.answer import (AnswerSheetStatusSerializer,
                                                   ListUserFormAnswerSheetSerializer,
                                                   ListAnonymousFormAnswerSheetSerializer,
                                                   RetrieveUserFormAnswerSheetSerializer,
                                                   RetrieveAnonymousFormAnswerSheetSerializer)
from irhrs.questionnaire.models.questionnaire import Answer, Question
from irhrs.forms.constants import APPROVED, DENIED, DRAFT, DYNAMIC_FORM_STATUS
from irhrs.core.utils.common_utils import get_users_list_from_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.forms.utils.answer import save_answer_to_db, save_files_from_answers
from irhrs.forms.tasks.notification import send_notification_if_all_users_submitted
from irhrs.forms.utils.approval import get_answer_sheets_with_annotation
from irhrs.forms.utils.answer import validate_answers
from irhrs.core.utils.common import validate_permissions
from irhrs.forms.api.v1.permission import (
    FormAnonymousReadAndActPermission,
)
from irhrs.permission.constants.permissions import (
    FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS,
    FORM_PERMISSION,
    FORM_CAN_VIEW_AND_ACT_ON_ANONYMOUS_FORMS,
    FORM_READ_ONLY_PERMISSION,
)
from irhrs.core.utils.filters import SearchFilter
from irhrs.forms.models import (
    Form,
    UserForm,
    FormAnswerSheetApproval,
    UserFormAnswerSheet,
    AnonymousFormAnswerSheet,
    AnswerSheetStatus
)
from irhrs.forms.utils.answer import save_answer
from irhrs.forms.utils.stats import get_form_approval_stats
from irhrs.forms.utils.approval import (
    get_next_approval_level,
    get_next_approvers,
    validate_approval_level,
)
from irhrs.notification.utils import add_notification
from irhrs.notification.utils import notify_organization
from irhrs.forms.utils.answer import get_form_queryset_for_user


class UserFormAnswerSheetSubmitViewSet(OrganizationMixin, CreateViewSetMixin):
    """For submitting AnswerSet of survery form."""

    serializer_class = DummySerializer

    def create(self, request, *args, **kwargs):
        form_id = self.kwargs.get('form_id')
        form_filters = dict(
            organization=self.organization,
            form_assignments__user=self.request.user,
        )
        form = get_object_or_404(
            queryset=get_form_queryset_for_user(
                filters=form_filters,
                user=self.request.user
            ),
            pk=form_id
        )
        result = save_answer(self, form)
        return Response(result, status=status.HTTP_201_CREATED)


class AnonymousFormAnswerSheetSubmitViewSet(OrganizationMixin, CreateViewSetMixin):
    """For submitting AnswerSet of survery form."""

    serializer_class = DummySerializer
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        return AnonymousFormAnswerSheet.objects.all()

    def create(self, request, *args, **kwargs):
        form_uuid = self.kwargs.get('uuid')
        form = get_object_or_404(
            queryset=Form.objects.filter(organization=self.organization),
            uuid=form_uuid,
            is_anonymously_fillable=True,
            is_archived=False
        )
        question_answer = self.request.data.get('question')
        validate_answers(question_answer)
        answer_sheet_creation = dict(
            form=form,
        )
        context = {
            "organization": self.organization,
            "form": form
        }
        answer_sheet = AnonymousFormAnswerSheet.objects.create(**answer_sheet_creation)
        question_answer = save_files_from_answers(self, question_answer)
        save_answer_to_db(context, answer_sheet, question_answer)
        notify_organization(
            text=(
                f"Form '{answer_sheet.form.name}' has been submitted "
                "by anonymous user."
            ),
            action=answer_sheet,
            organization=self.organization,
            actor=get_system_admin(),
            url=f'/admin/{self.organization.slug}/form/response',
            permissions=[
                FORM_PERMISSION,
                FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS,
                FORM_READ_ONLY_PERMISSION
            ]
        )
        result = dict(answer_sheet_id=answer_sheet.id)
        return Response(result, status=status.HTTP_201_CREATED)


class UserFormAnswerSheetFilter(FilterSet):
    status = MultipleChoiceFilter(
        choices=DYNAMIC_FORM_STATUS,
        method='get_status_in',
        field_name='final_status'
    )

    def get_status_in(self, queryset, name, value):
        if value[0].strip() == "":
            return queryset.exclude(
                form__is_archived=True,
                final_status=DRAFT
            )
        if value[0].strip() == DRAFT:
            return queryset.filter(
                form__is_archived=False,
                final_status=DRAFT
            )
        return queryset.filter(**{
            'final_status__in': value
        })

    class Meta:
        model = UserFormAnswerSheet
        fields = ['status']


class UserFormAnswerSheetViewSet(OrganizationMixin, ListRetrieveUpdateViewSetMixin):
    """For listing/retrieving answer sheet."""

    serializer_class = RetrieveUserFormAnswerSheetSerializer
    filter_backends = [
        DjangoFilterBackend,
        FilterMapBackend,
        OrderingFilterMap,
        SearchFilter,
    ]
    filter_map = {
        'form_name': ('form__name', 'icontains'),
    }
    search_fields = ('user__first_name', 'user__middle_name', 'user__last_name')
    ordering_fields_map = {
        'title': 'form__name',
        'deadline': 'form__deadline',
        'modified_at': 'modified_at',
    }
    filter_class = UserFormAnswerSheetFilter

    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        if _as == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                raise PermissionDenied
            return 'hr'
        return _as

    def get_queryset(self):
        if self.action == 'take_action':
            return get_answer_sheets_with_annotation(
                self.request.user,
            )
        if self.user_mode == 'hr':
            filters = {
                "is_draft": False,
                "form__organization": self.organization
            }
            return get_answer_sheets_with_annotation(
                self.request.user,
                filters=filters
            )
        elif self.user_mode == 'approver':
            filters = {
                "form__organization": self.organization
            }
            sheets = get_answer_sheets_with_annotation(
                self.request.user,
            )
            return sheets.filter(
                is_current_user_low_level_approver=True,
            )
        else:
            filters = {
                "user": self.request.user,
                "form__organization": self.organization
            }
            qs = get_answer_sheets_with_annotation(
                self.request.user,
                filters=filters,
            )
            return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            "request": self.request
        })
        return context

    def get_serializer_class(self):
        if self.action == "list":
            return ListUserFormAnswerSheetSerializer
        return super().get_serializer_class()

    def update(self, request, *args, **kwargs):
        answer_sheet = self.get_object()
        is_draft_from_req = self.request.data.get('is_draft')
        # dont allow to draft answers that have already been submitted
        if not answer_sheet.is_draft and is_draft_from_req:
            raise ValidationError({
                "error": "Cannot draft answers that have already been submitted."
            })
        form = request.data.update({"form": answer_sheet.form.id})
        result = save_answer(
            self,
            form=answer_sheet.form,
            answer_sheet=answer_sheet
        )
        return Response(result, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        queryset = self.get_queryset()
        form_name = self.request.query_params.get('form_name')
        search = self.request.query_params.get('search')
        if form_name:
            queryset = queryset.filter(form__name__icontains=form_name)
        if search:
            queryset = queryset.annotate(
                full_name=(Concat(
                    F('user__first_name'),
                    F('user__middle_name'),
                    F('user__last_name'),
                ))
            ).filter(full_name__icontains=search)
        stats = get_form_approval_stats(queryset)
        response.data.update({
            'stats': stats
        })
        return response

    @action(
        detail=True, methods=['POST'],
        serializer_class=AnswerSheetStatusSerializer,
        url_path='take-action'
    )
    @transaction.atomic()
    def take_action(self, request, *args, **kwargs):
        """ For approving/denying answer sheet. """
        answer_sheet = self.get_object()
        request_action = request.data.get("action")
        validate_approval_level(answer_sheet, self.request.user)
        approval_level = get_next_approval_level(
            answer_sheet=answer_sheet,
        )
        last_approval_level = approval_level
        request.data.update({
            "answer_sheet": answer_sheet.id,
            "approver": request.user.id,
            "approval_level": approval_level.id
        })
        answer_sheet_status = self.get_serializer_class()(data=request.data)
        answer_sheet_status.is_valid(raise_exception=True)
        answer_sheet_status.save()

        next_approval = get_next_approval_level(
            answer_sheet=answer_sheet,
        )
        notify_organization(
            text=(
                f"Form '{answer_sheet.form.name}' of {answer_sheet.user.full_name} "
                f"has been {request_action} by {request.user.full_name}."
            ),
            action=answer_sheet,
            actor=request.user,
            organization=self.organization,
            url=f'/admin/{self.organization.slug}/form/response',
            permissions=[
                FORM_PERMISSION,
                FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS
            ]
        )
        if not next_approval:
            if request_action == APPROVED:
                inapplicable_approval_settings = FormAnswerSheetApproval.objects.filter(
                    answer_sheet=answer_sheet,
                    approval_level__gt=last_approval_level.approval_level
                )
                if inapplicable_approval_settings.exists():
                    AnswerSheetStatus.objects.create(
                        answer_sheet=answer_sheet,
                        approver=get_system_admin(),
                        approval_level=None,
                        action=APPROVED,
                        remarks=f"Approved by system(no further approvers are applicable)."
                    )
                answer_sheet.is_approved = True
                answer_sheet.is_draft = False
                answer_sheet.save()

            add_notification(
                text=(
                    f"Form '{answer_sheet.form.name}' has been {request_action} "
                ),
                action=answer_sheet,
                recipient=answer_sheet.user,
                actor=request.user,
                url='/user/organization/forms'
            )
            send_notification_if_all_users_submitted(answer_sheet)

        if next_approval:
            answer_sheet.next_approval_level = next_approval.approval_level
            answer_sheet.save()
            next_approvers = list(get_next_approvers(answer_sheet))
            add_notification(
                text=(
                    f"Form '{answer_sheet.form.name}' has been {request_action} "
                ),
                action=answer_sheet,
                recipient=answer_sheet.user,
                actor=request.user,
                url='/user/organization/forms'
            )
            add_notification(
                text=(
                    f"Form '{answer_sheet.form.name}' of {answer_sheet.user.full_name} "
                    f"has been forwarded to you."
                ),
                action=answer_sheet,
                recipient=next_approvers,
                actor=request.user,
                url='/user/form-request'
            )
        return Response(answer_sheet_status.data)

    @action(
        detail=False, methods=['GET'],
        url_path=r'download-form-attachment'
    )
    def download_form_attachment(self, request, *args, **kwargs):
        original_file_name = request.query_params.get('file_name')
        original_file_path = request.query_params.get('file_uuid')
        attachment = Answer.objects.filter(attachment__contains=original_file_path).first()
        if not attachment:
            raise ValidationError({
                "error": "No such file found"
            })
        else:
            attachment = attachment.attachment
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(attachment.path)
        att = ContentFile(default_storage.open(attachment.path).read())
        response = HttpResponse(
            content=att,
            content_type=mime_type
        )
        response['Content-Disposition'] = f'attachment; filename={original_file_name}'
        return response

class AnonymousFormAnswerSheetViewSet(OrganizationMixin, ListRetrieveViewSetMixin):
    """For listing/retrieving answer sheet."""

    serializer_class = RetrieveAnonymousFormAnswerSheetSerializer
    permission_classes = [FormAnonymousReadAndActPermission]
    filter_backends = (
        FilterMapBackend,
        OrderingFilterMap
    )
    filter_map = {
        'form_name': ('form__name', 'icontains')
    }
    ordering_fields_map = {
        'title': 'form__name',
        'deadline': 'form__deadline',
        'modified_at': 'modified_at',
    }

    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        if _as == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                raise PermissionDenied
            return 'hr'
        return ''

    def get_queryset(self):
        return AnonymousFormAnswerSheet.objects.filter(
            form__organization=self.organization
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            "request": self.request
        })
        return context

    def get_serializer_class(self):
        if self.action == "list":
            return ListAnonymousFormAnswerSheetSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        queryset_count = self.get_queryset().count()
        stats = {
            "total": queryset_count
        }
        response.data.update({
            'stats': stats
        })
        return response
