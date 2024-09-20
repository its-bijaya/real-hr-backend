from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django.utils import timezone
import dateutil.parser as dateparser

from rest_framework import serializers
from rest_framework.filters import SearchFilter

from irhrs.attendance.api.v1.permissions import AttendancePermission, AttendanceReportPermission
from irhrs.attendance.constants import CONFIRMED, UNCLAIMED, REQUESTED, \
    APPROVED, DECLINED, FORWARDED
from irhrs.core.utils.common import validate_permissions
from irhrs.export.mixins.export import BackgroundExcelExportMixin
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListViewSetMixin, PastUserFilterMixin
from irhrs.core.utils.filters import FilterMapBackend, \
    NullsAlwaysLastOrderingFilter
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION, \
    ATTENDANCE_REPORTS_PERMISSION, HRIS_REPORTS_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserFieldThinSerializer
from irhrs.attendance.utils.attendance import humanize_interval


def get_total_claimed(obj):
    return humanize_interval(obj.total_claimed)


def get_total_unclaimed(obj):
    return humanize_interval(obj.total_unclaimed)


def get_total_requested(obj):
    return humanize_interval(obj.total_requested)


def get_total_forwarded(obj):
    return humanize_interval(obj.total_forwarded)


def get_total_approved(obj):
    return humanize_interval(obj.total_approved)


def get_total_declined(obj):
    return humanize_interval(obj.total_declined)


def get_total_confirmed(obj):
    return humanize_interval(obj.total_confirmed)


class OverTimeClaimReport(
    PastUserFilterMixin, BackgroundExcelExportMixin, OrganizationMixin,
    ListViewSetMixin
):
    queryset = get_user_model().objects.all()
    permission_classes = [AttendanceReportPermission]
    serializer_class = type(
        'DynamicSerializer',
        (UserFieldThinSerializer,),
        {
            'total_claimed': serializers.SerializerMethodField(),
            'total_unclaimed': serializers.SerializerMethodField(),
            'total_requested': serializers.SerializerMethodField(),
            'total_forwarded': serializers.SerializerMethodField(),
            'total_approved': serializers.SerializerMethodField(),
            'total_declined': serializers.SerializerMethodField(),
            'total_confirmed': serializers.SerializerMethodField(),
            'get_total_claimed': staticmethod(lambda x: humanize_interval(
                x.total_claimed)),
            'get_total_unclaimed': staticmethod(lambda x: humanize_interval(
                x.total_unclaimed)),
            'get_total_requested': staticmethod(lambda x: humanize_interval(
                x.total_requested)),
            'get_total_forwarded': staticmethod(lambda x: humanize_interval(
                x.total_forwarded)),
            'get_total_approved': staticmethod(lambda x: humanize_interval(
                x.total_approved)),
            'get_total_declined': staticmethod(lambda x: humanize_interval(
                x.total_declined)),
            'get_total_confirmed': staticmethod(lambda x: humanize_interval(
                x.total_confirmed)),

        }
    )

    search_fields = (
        'first_name',
        'middle_name',
        'last_name'
    )
    filter_backends = (FilterMapBackend,
                       SearchFilter,
                       NullsAlwaysLastOrderingFilter)

    ordering_fields_map = {
        'total_claimed': 'total_claimed',
        'total_unclaimed': 'total_unclaimed',
        'total_requested': 'total_requested',
        'total_forwarded': 'total_forwarded',
        'total_approved': 'total_approved',
        'total_declined': 'total_declined',
        'total_confirmed': 'total_confirmed',
        'division': 'detail__division__slug',
        'user': (
            'first_name', 'middle_name', 'last_name'
        ),
    }

    filter_map = {
        'division': 'detail__division__slug',
        'branch': 'detail__branch__slug',
    }
    notification_permissions = [ATTENDANCE_REPORTS_PERMISSION]
    export_type = 'OverTime Claim Report'
    export_fields = {
        'User': 'full_name',
        'Division': 'detail.division',
        'Total Claimed': get_total_claimed,
        'Total Unclaimed': get_total_unclaimed,
        'Total Requested': get_total_requested,
        'Total Forwarded': get_total_forwarded,
        'Total Approved': get_total_approved,
        'Total Confirmed': get_total_confirmed,
        'Total Declined': get_total_declined,
    }

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            detail__organization=self.get_organization()
        )
        if not validate_permissions(
            self.request.user.get_hrs_permissions(self.get_organization()),
            ATTENDANCE_PERMISSION,
            ATTENDANCE_REPORTS_PERMISSION,

        ):
            queryset = queryset.filter(
                overtime_entries__user=self.request.user
            )
        if self.action == 'export':
            return queryset
        _base_filter = self.get_base_filter()
        return self.annotate_overtime(queryset, _base_filter)

    @staticmethod
    def has_user_permission():
        return False

    @classmethod
    def annotate_overtime(cls, data, _base_filter):
        return data.annotate(
            total_claimed=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(**_base_filter) & ~Q(
                    overtime_entries__claim__status=UNCLAIMED)
            ),
            total_confirmed=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(
                    **_base_filter
                ) & Q(overtime_entries__claim__status=CONFIRMED),
            ),
            total_forwarded=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(
                    **_base_filter
                ) & Q(overtime_entries__claim__status=FORWARDED),
            ),
            total_unclaimed=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(
                    **_base_filter
                ) & Q(overtime_entries__claim__status=UNCLAIMED),
            ),
            total_requested=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(
                    **_base_filter
                ) & Q(overtime_entries__claim__status=REQUESTED),
            ),
            total_approved=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(
                    **_base_filter
                ) & Q(overtime_entries__claim__status=APPROVED),
            ),
            total_declined=Sum(
                'overtime_entries__overtime_detail__claimed_overtime',
                filter=Q(
                    Q(
                        **_base_filter
                    ) & Q(
                        overtime_entries__claim__status=DECLINED
                    )
                )
            ),
        ).current().order_by()

    @classmethod
    def get_exported_file_content(cls, data, title, columns, extra_content, description=None, **kwargs):
        _base_filter = extra_content.get('_base_filter', {})

        data = cls.annotate_overtime(data, _base_filter=_base_filter)

        return super().get_exported_file_content(data, title, columns, extra_content, description, **kwargs)

    def get_extra_export_data(self):
        extra = super().get_extra_export_data()
        extra.update({
            '_base_filter': self.get_base_filter()
        })
        return extra

    def get_base_filter(self):
        _created_min = self.request.query_params.get('start_date')
        _created_max = self.request.query_params.get('end_date')
        try:
            created_min = dateparser.parse(
                _created_min) if _created_min else None
            created_max = dateparser.parse(
                _created_max) if _created_max else None
        except (TypeError, ValueError):
            created_max = None
            created_min = None
        if created_min and created_max:
            _base_filter = {
                'overtime_entries__timesheet__timesheet_for__gte': created_min.date(),
                'overtime_entries__timesheet__timesheet_for__lte': created_max.date()
            }
        else:
            current_date = timezone.now().date()
            start_of_current_month = current_date.replace(day=1)
            _base_filter = {
                'overtime_entries__timesheet__timesheet_for__gte': start_of_current_month
            }
        return _base_filter

    def get_frontend_redirect_url(self):
        return f'/admin/{self.organization.slug}/attendance/reports/overtime'
