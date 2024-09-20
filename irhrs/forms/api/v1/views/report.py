from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import filters, status
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Count, Q, Case, When, F, SlugField
from rest_framework.decorators import action
from irhrs.questionnaire.models.helpers import (
    CHECKBOX,
    RADIO,
    FILE_UPLOAD,
    MULTIPLE_CHOICE_GRID,
    CHECKBOX_GRID
)
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from openpyxl.writer.excel import save_virtual_workbook

from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin,
    ListViewSetMixin,
)
from irhrs.core.utils.common import validate_permissions
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.utils.common import get_today
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.forms.api.v1.permission import FormReportsPermission
from irhrs.forms.api.v1.serializers.report import (
    IndividualFormSummaryQuestionAnswerSerializer,
    AnonymousFormSummaryQuestionAnswerSerializer,
    UserFormIndividualQuestionAnswerPaginatedSerializer,
    AnonymousFormIndividualQuestionAnswerSerializer
)
from irhrs.forms.utils.reports import (
    transform_aggregation,
    create_form_report
)
from irhrs.questionnaire.models.helpers import (
    SHORT,
    LONG,
    FILE_UPLOAD,
    DATE,
    TIME,
    DURATION,
    DATE_TIME,
    DATE_WITHOUT_YEAR,
    DATE_TIME_WITHOUT_YEAR,
)
from irhrs.forms.models import (
    Form,
    UserForm,
    FormQuestion,
    UserFormAnswerSheet,
    UserFormIndividualQuestionAnswer,
    AnonymousFormIndividualQuestionAnswer,
    AnonymousFormAnswerSheet,
)
from irhrs.permission.constants.permissions import FORM_CAN_VIEW_FORM_REPORT

User = get_user_model()


class FormReportViewSet(
        OrganizationMixin,
        ListViewSetMixin,
        BackgroundExcelExportMixin
):
    queryset = User.objects.all()
    serializer_class = DummySerializer
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        FilterMapBackend
    )
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'job_title': 'detail__job_title__slug',
        'employee_level': 'detail__employment_level__slug',
        'gender': 'detail__gender',
        'job_type': 'form_assignments__user__detail__employment_status__slug',
    }
    search_fields = ['first_name', 'middle_name', 'last_name']

    def get_request_answer_for_choice_field(self):
        final_result = []
        if any(self.request_answer):
            for choice in self.request_answer:
                final_result.append({
                    "title": choice,
                    "is_correct": True
                })
        else:
            choices = self.question.question.all_answer_choices.all()
            for choice in choices:
                final_result.append({
                    "title": choice.title,
                    "is_correct": False
                })
        return final_result

    def get_request_answer_for_file_upload(self):
        final_result = []
        if any(self.request_answer):
            file_name = self.request_answer[0]
            final_result.append({"saved_file_name_only": file_name})
        else:
            final_result.append({"file_name": "", "file_url": ""})
        return final_result

    def get_request_answer_for_grid_type(self):
        return self.request_answer

    def get_default_query_format(self):
        if any(self.request_answer):
            return self.request_answer
        else:
            return [""]

    def get_formatted_request_answer_for_query(self):
        answer_choice = self.question.question.answer_choices
        answer_choices_map = {
            CHECKBOX: self.get_request_answer_for_choice_field,
            RADIO: self.get_request_answer_for_choice_field,
            FILE_UPLOAD: self.get_request_answer_for_file_upload,
            MULTIPLE_CHOICE_GRID: self.get_request_answer_for_grid_type,
            CHECKBOX_GRID: self.get_request_answer_for_grid_type,
        }
        if not self.request_answer:
            return []

        get_query_format_function = answer_choices_map.get(answer_choice)
        if get_query_format_function:
            return get_query_format_function()
        else:
            return self.get_default_query_format()


    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'return_users':
            form_id = self.kwargs.get('form_id')
            self.question = get_object_or_404(
                FormQuestion.objects.all(),
                pk=self.kwargs.get("question_id")
            )
            question_type = self.question.question.answer_choices
            if question_type in [MULTIPLE_CHOICE_GRID, CHECKBOX_GRID]:
                self.request_answer = self.request.data
            else:
                self.request_answer = [self.request.data.get("answers")]

            form = get_object_or_404(
                queryset=Form.objects.filter(organization=self.organization),
                is_anonymously_fillable=False,
                pk=form_id
            )

            request_answer = self.get_formatted_request_answer_for_query()
            fil = dict(
                answer_sheets__is_approved=True,
                answer_sheets__individual_question_answers__question=self.question,
                answer_sheets__form=form,
                answer_sheets__individual_question_answers__answers__contains=request_answer
            )
            form_fill_date = self.request.query_params.get("form_fill_date")
            if form_fill_date:
                fil.update({
                    'answer_sheets__individual_question_answers__created_at__date': form_fill_date
                })
            qs = qs.filter(**fil).distinct()
        return qs

    def filter_queryset(self, queryset):
        duty_station = self.request.query_params.get('duty_station',None)
        queryset = super().filter_queryset(queryset)

        if duty_station:
            queryset = queryset.filter(
                detail__organization=self.organization,
                assigned_duty_stations__isnull=False
            ).annotate(
                current_duty_station=Case(
                    When(
                        Q(
                            assigned_duty_stations__to_date=None,
                            assigned_duty_stations__from_date__lte=get_today(),
                        )|
                        Q(
                            assigned_duty_stations__from_date__lte=get_today(),
                            assigned_duty_stations__to_date__gte=get_today(),
                        ),
                        then=F('assigned_duty_stations__duty_station__slug'),
                    ),
                    output_field = SlugField(),
                )
            ).filter(
                current_duty_station__isnull=False,
                current_duty_station=duty_station
            )

        return queryset


    def check_permission_according_to_question_visibility(self, form, form_question=None):
        is_requesting_as_user = not self.request.query_params.get('as')
        is_hr = validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
            FORM_CAN_VIEW_FORM_REPORT
        )
        is_form_assigned_to_user = UserForm.objects.filter(
            form=form,
            user=self.request.user
        ).exists()

        permission_denied = True

        # for list action
        if (is_requesting_as_user and is_form_assigned_to_user) or is_hr:
            permission_denied = False

        # for detail actions
        if form_question:
            if (
                    (is_requesting_as_user and is_form_assigned_to_user) and
                    form_question.answer_visible_to_all_users
            ) or is_hr:
                permission_denied = False

        if permission_denied:
            raise PermissionDenied




    def list(self, request, *args, **kwargs):
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(organization=self.organization),
            is_anonymously_fillable=False,
            pk=form_id
        )
        self.check_permission_according_to_question_visibility(form)
        serializer_context = {
            "form": form,
            "queryset": self.filter_queryset(self.get_queryset()),
            "request": request,
            "organization": self.organization,
            "view": self
        }
        questions = FormQuestion.objects.filter(
            question_section__question_set__forms=form
        ).order_by('question_section')
        is_requesting_as_user = not self.request.query_params.get('as')
        if is_requesting_as_user:
            questions = questions.filter(answer_visible_to_all_users=True)
        page = self.paginate_queryset(questions)
        results = IndividualFormSummaryQuestionAnswerSerializer(
            page,
            many=True,
            context=serializer_context
        ).data
        return self.get_paginated_response(results)

    @action(
        detail=False, methods=['POST'],
        url_path='get-users/(?P<question_id>\d+)'
    )
    def return_users(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        USER_FIELDS = ['id', 'full_name', 'profile_picture', 'cover_picture',
                       'division', 'organization', 'job_title']
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(organization=self.organization),
            pk=form_id
        )
        form_question_id = self.kwargs.get('question_id')
        form_question = get_object_or_404(
            queryset=FormQuestion.objects.filter(
                question_section__question_set__forms=form
            ),
            pk=form_question_id
        )
        self.check_permission_according_to_question_visibility(form, form_question)
        result = {
            "users": UserThinSerializer(qs, many=True, fields=USER_FIELDS).data
        }
        return Response(result)

    @action(
        detail=False, methods=['GET'],
        url_path='list-response/(?P<question_id>\d+)'
    )
    def list_response(self, request, *args, **kwargs):
        users = self.get_queryset()
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(organization=self.organization),
            pk=form_id
        )
        form_question_id = self.kwargs.get('question_id')
        form_question = get_object_or_404(
            queryset=FormQuestion.objects.filter(
                question_section__question_set__forms=form
            ),
            pk=form_question_id
        )
        self.check_permission_according_to_question_visibility(form, form_question)
        if form_question.question.answer_choices not in [SHORT, LONG, FILE_UPLOAD]:
            raise ValidationError({
                "error": (
                    "List response currently only supports long/short text "
                    "and file upload answer types."
                )
            })
        question_answers = UserFormIndividualQuestionAnswer.objects.filter(
            answer_sheet__is_approved=True,
            answer_sheet__form=form,
            answer_sheet__user__in=users,
            question=form_question
        ).order_by('answers').values('answers')
        page = self.paginate_queryset(question_answers.distinct())
        results = []
        for qa in page:
            answer = qa['answers']
            if answer:
                results.append(qa['answers'][0])
            else:
                results.append("")
        return self.get_paginated_response(
            results
        )

    @action(
        detail=False, methods=['GET'],
        url_path='list-aggregated-response/(?P<question_id>\d+)'
    )
    def list_aggregated_response(self, request, *args, **kwargs):
        users = self.get_queryset()
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(organization=self.organization),
            pk=form_id
        )
        form_question_id = self.kwargs.get('question_id')
        form_question = get_object_or_404(
            queryset=FormQuestion.objects.filter(
                question_section__question_set__forms=form
            ),
            pk=form_question_id
        )
        self.check_permission_according_to_question_visibility(form, form_question)
        if form_question.question.answer_choices not in [
                DATE, TIME, DURATION,
                DATE_TIME, DATE_WITHOUT_YEAR,
                DATE_TIME_WITHOUT_YEAR
        ]:
            raise ValidationError({
                "error": (
                    "Aggregated list response currently only supports date and time"
                    "answer types."
                )
            })
        question_answers = UserFormIndividualQuestionAnswer.objects.filter(
            answer_sheet__is_approved=True,
            answer_sheet__form=form,
            answer_sheet__user__in=users,
            question=form_question
        )
        aggregate = question_answers.values('answers').annotate(
            count=Count('id')
        ).order_by('answers')
        page = self.paginate_queryset(aggregate.distinct())
        result = transform_aggregation(page)
        return self.get_paginated_response(
            result
        )

    def get_export_type(self):
        form_id = self.kwargs.get('form_id')
        return f"form {form_id} report"

    def get_export_fields(self):
        return {}

    @classmethod
    def get_exported_file_content(cls, data, title, columns, extra_content,
                                  description=None, **kwargs):
        form = extra_content.get('form')
        users = extra_content.get('users')
        # @TODO: refactor using contexts instead of passing many arguments
        form_fill_date = extra_content.get('form_fill_date')
        request_details = {
            "is_user": extra_content.get('is_user'),
            "is_hr": extra_content.get('is_hr')
        }
        wb = create_form_report(form, users, form_fill_date, request_details)
        return ContentFile(save_virtual_workbook(wb))

    def get_extra_export_data(self):
        data = super().get_extra_export_data()
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(organization=self.organization),
            pk=form_id
        )
        self.check_permission_according_to_question_visibility(form)
        is_requesting_as_user = not self.request.query_params.get('as')
        is_form_assigned_to_user = UserForm.objects.filter(
            form=form,
            user=self.request.user
        ).exists()
        users = self.filter_queryset(self.get_queryset())
        form_fill_date = self.request.query_params.get("form_fill_date")
        data.update({
            'form': form,
            'users': users,
            'form_fill_date': form_fill_date,
            'is_user': is_requesting_as_user,
            'is_hr': validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                FORM_CAN_VIEW_FORM_REPORT
            )
        })
        return data


class AnonymousFormReportViewSet(
        OrganizationMixin,
        ListViewSetMixin,
):
    """ Assign forms to users """

    queryset = User.objects.all()
    permission_classes = [FormReportsPermission]
    serializer_class = DummySerializer

    def list(self, request, *args, **kwargs):
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(
                organization=self.organization,
                is_anonymously_fillable=True
            ),
            pk=form_id
        )
        questions = FormQuestion.objects.filter(
            question_section__question_set__forms=form
        ).order_by('question_section')
        serializer_context = {
            "form": form,
            "request": request,
            "organization": self.organization,
            "view": self
        }
        page = self.paginate_queryset(questions)
        results = AnonymousFormSummaryQuestionAnswerSerializer(
            page,
            many=True,
            context=serializer_context
        ).data
        return self.get_paginated_response(results)

    @action(
        detail=False, methods=['GET'],
        url_path='list-response/(?P<question_id>\d+)'
    )
    def list_response(self, request, *args, **kwargs):
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(
                organization=self.organization,
                is_anonymously_fillable=True
            ),
            pk=form_id
        )
        form_question_id = self.kwargs.get('question_id')
        form_question = get_object_or_404(
            queryset=FormQuestion.objects.filter(
                question_section__question_set__forms=form
            ),
            pk=form_question_id
        )
        if form_question.question.answer_choices not in [SHORT, LONG, FILE_UPLOAD]:
            raise ValidationError({
                "error": (
                    "List response currently only supports long/short text "
                    "and file upload answer types."
                )
            })
        question_answers = AnonymousFormIndividualQuestionAnswer.objects.filter(
            answer_sheet__form=form,
            question=form_question
        ).order_by('answers').values('answers')
        page = self.paginate_queryset(question_answers.distinct())
        results = []
        for qa in page:
            answer = qa['answers']
            if answer:
                results.append(qa['answers'][0])
            else:
                results.append("")
        return self.get_paginated_response(
            results
        )

    @action(
        detail=False, methods=['GET'],
        url_path='list-aggregated-response/(?P<question_id>\d+)'
    )
    def list_aggregated_response(self, request, *args, **kwargs):
        form_id = self.kwargs.get('form_id')
        form = get_object_or_404(
            queryset=Form.objects.filter(organization=self.organization),
            pk=form_id
        )
        form_question_id = self.kwargs.get('question_id')
        form_question = get_object_or_404(
            queryset=FormQuestion.objects.filter(
                question_section__question_set__forms=form
            ),
            pk=form_question_id
        )
        if form_question.question.answer_choices not in [
                DATE, TIME, DURATION,
                DATE_TIME, DATE_WITHOUT_YEAR,
                DATE_TIME_WITHOUT_YEAR
        ]:
            raise ValidationError({
                "error": (
                    "Aggregated list response currently only supports date and time"
                    "answer types."
                )
            })
        question_answers = AnonymousFormIndividualQuestionAnswer.objects.filter(
            answer_sheet__form=form,
            question=form_question
        )
        aggregate = question_answers.values('answers').annotate(
            count=Count('id')
        ).order_by('answers')
        page = self.paginate_queryset(aggregate.distinct())
        result = transform_aggregation(page)
        return self.get_paginated_response(
            result
        )
