from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from rest_framework.filters import SearchFilter

from irhrs.attendance.constants import CONFIRMED
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin
from irhrs.core.utils.common import validate_permissions, get_today
from irhrs.core.utils.filters import OrderingFilterMap, FilterMapBackend
from irhrs.core.utils.subordinates import find_immediate_subordinates, \
    find_subordinates_excluding_self
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.hris.api.v1.permissions import ViewPayrollReportPermission
from irhrs.payroll.api.v1.serializers.EmployeeMetricsReport import EmployeeMetricsReportSerializer, \
    EmployeeMetricHeadingReportSettingSerializer
from irhrs.payroll.api.v1.views.reports import ReportSettingViewSetMixin
from irhrs.payroll.models import OrganizationPayrollConfig
from irhrs.payroll.models.EmployeeMetricsSetting import EmployeeMetricHeadingReportSetting
from irhrs.permission.constants.permissions import PAYROLL_REPORT_PERMISSION, \
    PAYROLL_SETTINGS_PERMISSION,GENERATE_PAYROLL_PERMISSION,PAYROLL_READ_ONLY_PERMISSIONS

User = get_user_model()


class EmployeeMetricsReportViewSet(ListViewSetMixin,
                                   BackgroundExcelExportMixin, OrganizationMixin):
    queryset = User.objects.all()
    serializer_class = EmployeeMetricsReportSerializer
    permission_classes = [ViewPayrollReportPermission]
    filter_backends = [SearchFilter, OrderingFilterMap, FilterMapBackend]
    search_fields = ('first_name', 'middle_name', 'last_name', 'username')
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name'),
        'username': 'username',
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'job_title': 'detail__job_title__slug',
        'employment_level': 'detail__employment_level__slug',
        'employment_type': 'detail__employment_status__slug'
    }
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'job_title': 'detail__job_title__slug',
        'employment_level': 'detail__employment_level__slug',
        'employment_type': 'detail__employment_status__slug',
    }

    export_type = "Employee Metrics Report"
    notification_permissions = [PAYROLL_REPORT_PERMISSION]

    def get_export_fields(self):
        export_fields = {
            "User": "full_name",
            "Username": "username",
            "Job Title": "detail.job_title",
            "Division": "detail.division",
            "Branch": "detail.branch",
            "Employment Level": "detail.employment_level",
            "Employment Type": "detail.employment_status",
        }
        setting_headings = EmployeeMetricHeadingReportSetting.objects.filter(
            organization=self.organization
        ).first()
        if setting_headings:
            choice_headings = setting_headings.headings
            setting_heading_title = [' '.join(word.capitalize() for word in item.split('_')) for
                                     item in choice_headings]
            export_fields.update(dict(zip(setting_heading_title, choice_headings)))
        return export_fields

    def get_serializer(self, *args, **kwargs):
        mandatory_fields = ['id', 'full_name', 'username', 'profile_picture', 'cover_picture',
                            'division', 'job_title', 'email', 'employee_level', 'branch',
                            'employment_type']
        setting_headings = EmployeeMetricHeadingReportSetting.objects.filter(
                                                                    organization=self.organization
                                                                    ).first()
        choice_headings = getattr(setting_headings, "headings", None)
        if choice_headings:
            mandatory_fields = mandatory_fields + choice_headings

        kwargs.setdefault('fields', mandatory_fields)
        return super().get_serializer(*args, **kwargs)


    @property
    def from_date(self):
        from_date = self.request.query_params.get('start_date')
        if not from_date:
            from_date = get_today() - timedelta(days=30)
            from_date = from_date.strftime('%Y-%m-%d')
        return from_date

    @property
    def to_date(self):
        to_date = self.request.query_params.get('end_date')
        if not to_date:
            to_date = get_today().strftime('%Y-%m-%d')
        return to_date

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode == "hr" and validate_permissions(
            self.request.user.get_hrs_permissions(
                self.get_organization()
            ),
            PAYROLL_REPORT_PERMISSION
        ):
            return mode
        elif mode == "supervisor":
            return mode
        return 'user'

    def check_permissions(self, request):
        if self.mode == 'supervisor':
            return len(find_subordinates_excluding_self(self.request.user.id)) > 0
        return super().check_permissions(request)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            detail__organization=self.organization
        )
        selected_employees = self.request.query_params.get('selected_employees', '').split(',')
        selected_employees = set(map(int,filter(str.isdigit,selected_employees)))
        if self.request.query_params.get('is_current') == 'false':
            queryset = queryset.past()
        else:
            queryset = queryset.current()
        from_date = datetime.strptime(self.from_date, '%Y-%m-%d').date()
        to_date = datetime.strptime(self.to_date, '%Y-%m-%d').date()
        _base_filter = {
            'overtime_entries__timesheet__timesheet_for__gte': from_date,
            'overtime_entries__timesheet__timesheet_for__lte': to_date
        }
        if self.mode == 'hr':
            qs = self.annotate_overtime(queryset, _base_filter)
            if selected_employees:
                return qs.filter(id__in=selected_employees)
            return qs
        elif self.mode == 'supervisor':
            subordinates = find_subordinates_excluding_self(self.request.user.id)
            if selected_employees:
                subordinates = subordinates.intersection(selected_employees)
            subordinate_queryset = queryset.filter(id__in=subordinates)
            return self.annotate_overtime(subordinate_queryset, _base_filter)
        else:
            return self.permission_denied(self.request,
                                          "You do not permission to perform this action.")

    def get_extra_export_data(self):
        export_dict = super().get_extra_export_data()
        serializer_context = self.get_serializer_context()
        serializer_context.pop('view', None)
        serializer_context.pop('request', None)
        export_dict.update({
            'prepare_export_object_context': {'serializer_context': serializer_context}
        })
        return export_dict
    @staticmethod
    def prepare_export_object(obj, **kwargs):
        attributes_to_update = ('working_days',
                                'total_days', 'worked_days', 'absent_days', 'leave_days',
                                'leave_days_on_workdays', 'unpaid_leave_days',
                                'paid_days', 'days_deduction_from_penalty',
                                'holiday_count', 'leave_paid_days', 'offday_count',
                                'worked_on_offday_holiday', 'worked_hour',
                                'total_claimed'
                                )
        data = EmployeeMetricsReportSerializer(instance=obj,
                                               context=kwargs.get('serializer_context'),
                                               fields=attributes_to_update).data

        for attribute in attributes_to_update:
            setattr(obj, attribute, data.get(attribute, None))

        return obj

    @classmethod
    def annotate_overtime(cls, data, _base_filter):
        return data.annotate(
            total_confirmed=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(
                    **_base_filter
                ) & Q(overtime_entries__claim__status=CONFIRMED),
            ),
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        include_holiday_offday = False
        payroll_config = OrganizationPayrollConfig.objects.filter(
            organization=self.get_organization()
        ).first()
        if payroll_config:
            include_holiday_offday = payroll_config.include_holiday_offday_in_calculation
        context.update({"from_date": self.from_date, "to_date": self.to_date,
                        "include_holiday_offday": include_holiday_offday,
                        "organization": self.get_organization()})
        return context


class EmployeeMetricHeadingReportSettingViewSet(ReportSettingViewSetMixin):
    serializer_class = EmployeeMetricHeadingReportSettingSerializer
    queryset = EmployeeMetricHeadingReportSetting.objects.all()

    @property
    def mode(self):
        mode = self.request.query_params.get("as", "user")
        if mode == "hr" and validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
                    PAYROLL_SETTINGS_PERMISSION,
                    GENERATE_PAYROLL_PERMISSION,
                    PAYROLL_REPORT_PERMISSION,
                    PAYROLL_READ_ONLY_PERMISSIONS,
        ):
            return mode
        elif mode == "supervisor":
            return mode
        return "user"

    def check_permissions(self, request):
        if self.mode == "supervisor":
            return len(find_immediate_subordinates(self.request.user.id)) > 0
        return super().check_permissions(request)
