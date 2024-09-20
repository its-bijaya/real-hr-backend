from django_q.tasks import async_task
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.db.models import Exists, Q, OuterRef
from rest_framework import filters
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import SAFE_METHODS
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied

from irhrs.core.mixins.viewset_mixins import (
    ListCreateUpdateDestroyViewSetMixin,
    CreateViewSetMixin,
    RetrieveViewSetMixin,
    OrganizationMixin,
    OrganizationCommonsMixin
)
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.notification.utils import add_notification
from irhrs.forms.api.v1.serializers.forms import (
    WriteFormSerializer,
    RetrieveFormSerializer,
    PartialUpdateFormSerializer,
    RetrieveAnonymousFormSerializer,
    ListFormSerializer,
    ListFormSerializerForUserSerializer,
    UserFormSerializer,
    ListFormAssignmentSerializer,
)
from irhrs.forms.api.v1.serializers.setting import (
    ReadFormApprovalSettingLevelSerializer
)
from irhrs.core.utils import get_system_admin
from irhrs.forms.constants import DENIED
from irhrs.forms.utils.answer import is_form_filled_yet, get_form_queryset_for_user
from irhrs.forms.api.v1.permission import (
    FormAnonymousPermission,
    FormAssignUnassignPermission,
    FormCRUDPermission
)
from irhrs.core.utils.common import get_today
from irhrs.forms.api.v1.permission import (
    FormCRUDPermission
)
from irhrs.permission.constants.permissions import (
    FORM_PERMISSION,
    FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS,
    FORM_CAN_VIEW_AND_ACT_ON_ANONYMOUS_FORMS,
    FORM_CAN_VIEW_FORM_REPORT,
    FORM_APPROVAL_SETTING_PERMISSION,
    FORM_CAN_ASSIGN_UNASSIGN_USER_FORMS,
    FORM_READ_ONLY_PERMISSION,
    FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION
)

from irhrs.forms.models import (
    Form,
    FormQuestion,
    UserForm,
    UserFormAnswerSheet,
    AnonymousFormAnswerSheet,
)

User = get_user_model()

class FormViewSet(
        OrganizationCommonsMixin,
        OrganizationMixin,
        ModelViewSet
):
    filter_backends = [
        filters.OrderingFilter,
        OrderingFilterMap,
        FilterMapBackend,
    ]
    permission_classes = [FormCRUDPermission]
    search_fields = ('name',)
    filter_map = {
        'form_name': ('name','icontains')
    }
    ordering_fields_map = {
        'title': 'name',
        'deadline': 'deadline',
        'modified_at': 'modified_at',
    }
    queryset = Form.objects.all()
    serializer_class = WriteFormSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.user_mode == '':
            filters = dict(
                form_assignments__user=self.request.user,
                organization=self.organization,
                is_archived=False,
            )
            return get_form_queryset_for_user(qs, filters, user=self.request.user).annotate(
                show_report_icon=Exists(
                    FormQuestion.objects.filter(
                        answer_visible_to_all_users=True,
                        question_section__question_set=OuterRef('question_set')
                    )
                )
            )
        return qs.filter(organization=self.organization)

    def get_serializer_class(self):
        if self.action == "list" and self.user_mode == '':
            return ListFormSerializerForUserSerializer
        if self.action == "list":
            return ListFormSerializer
        elif self.action == "retrieve":
            return RetrieveFormSerializer
        elif self.action == "partial_update":
            return PartialUpdateFormSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"user": self.request.user})
        if self.action == 'partial_update':
            form = self.get_object()
            context.update({"form": form})
        return context


    @property
    def user_mode(self):
        _as = self.request.query_params.get('as')
        if _as == 'hr':
            is_hr = validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                FORM_QUESTION_AND_SETTING_VIEW_CREATE_UPDATE_DELETE_PERMISSION,
                FORM_CAN_VIEW_FORM_REPORT,
                FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS,
                FORM_APPROVAL_SETTING_PERMISSION,
                FORM_CAN_ASSIGN_UNASSIGN_USER_FORMS,
                FORM_CAN_VIEW_AND_ACT_ON_ANONYMOUS_FORMS
            )
            # If not is_hr and mode is hr raise permission denied directly
            if not is_hr:
                raise PermissionDenied
            return 'hr'
        return ''

    def raise_error_if_form_filled(self, instance, action):
        filled_answersheet_exists = is_form_filled_yet(form=instance)
        if filled_answersheet_exists:
            message = {
                'error': f'This form cannot be {action} '
                f'because some users have already filled it.'
            }
            raise ValidationError(message)

    def update(self, request, *args, **kwargs):
        form = self.get_object()
        if not self.action == "partial_update":
            self.raise_error_if_form_filled(instance=form, action="updated")
        is_anon_fillable_from_req = self.request.data.get('is_anonymously_fillable')
        is_archived_from_req = self.request.data.get('is_archived')
        # delete all assignments and approval settings
        # if form status is changed to anonymous
        if is_anon_fillable_from_req:
            if is_anon_fillable_from_req != form.is_anonymously_fillable:
                if is_form_filled_yet(form):
                    raise ValidationError({
                        "error": "Cannot change anonymous status if form is already filled."
                    })
                else:
                    form.form_assignments.all().delete()
                    form.form_approval_setting.all().delete()
                    form.answer_sheets.all().filter(is_draft=True).delete()

        # notify assigned users when form has been submitted
        if is_archived_from_req and not form.is_archived:
            users = User.objects.filter(
                id__in=form.form_assignments.all().values('user')
            )
            async_task(
                add_notification,
                text=(
                    f"Form '{form.name}' has been archived and no longer "
                    "requires submission."
                ),
                action=form,
                recipient=users,
                actor=get_system_admin(),
                url='/user/organization/forms'
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.raise_error_if_form_filled(instance=instance, action="deleted")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['GET'],
            serializer_class=ListFormAssignmentSerializer,
            url_path='assigned-users')
    def get_assigned_users(self, request, *args, **kwargs):
        obj = self.get_object()
        data = ListFormAssignmentSerializer(instance=obj).data
        return Response(data)

    @action(
        detail=True, methods=['GET'],
        serializer_class=ReadFormApprovalSettingLevelSerializer,
        url_path='approvals'
    )
    def get_approvals(self, request, *args, **kwargs):
        obj = self.get_object()
        data = self.get_serializer_class()(instance=obj).data
        return Response(data)


class AnonymousFormViewSet(
        OrganizationCommonsMixin,
        OrganizationMixin,
        APIView
):
    serializer_class = RetrieveAnonymousFormSerializer
    permission_classes = []
    authentication_classes = []
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        """
        Return question set for anonymous form.
        """
        is_anonymous_user = self.request.user.is_anonymous
        if not is_anonymous_user:
            raise PermissionDenied

        uuid = kwargs.get('uuid')

        form = get_object_or_404(
            queryset=Form.objects.filter(
                organization=self.organization,
                is_anonymously_fillable=True,
                is_archived=False,
            ).filter(
                Q(
                    deadline__isnull=True
                ) |
                Q(
                    deadline__gte=get_today(with_time=True)
                )
            ),
            uuid=uuid
        )
        serialized_form = RetrieveAnonymousFormSerializer(
            form,
            context={
                "request": self.request,
                "with_questions": False,
                "organization": self.organization
            }
        ).data
        return Response(serialized_form)

    @classmethod
    def get_extra_actions(cls):
        return []


class UserFormViewSet(
        OrganizationMixin,
        CreateViewSetMixin,
):
    """ Assign forms to users """
    queryset = UserForm.objects.all()
    permission_classes = [FormAssignUnassignPermission]
    serializer_class = UserFormSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        form_id = self.kwargs.get('form_id')
        context['organization'] = self.get_organization()
        context['datas'] = self.request.data.get('datas')
        context["form"] = get_object_or_404(
            Form.objects.all(),
            pk=form_id
        )
        return context
