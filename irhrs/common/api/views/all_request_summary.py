from django.apps import apps as django_apps
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import ListViewSetMixin


class AllRequestsSummaryViewSet(ListViewSetMixin):
    """
    This is for summarized information that hits modules:
    ***
    * Leave
    * Attendance [For OT claims, and Adjustments]
    * Payroll [Not Implemented Yet]
    """
    NOT_INSTALLED_APPS = {}

    @property
    def attendance_adjustments(self):
        if django_apps.is_installed('irhrs.attendance'):
            from irhrs.attendance.models import AttendanceAdjustment
            from irhrs.attendance.constants import FORWARDED, REQUESTED
            return AttendanceAdjustment.objects.filter(
                status__in=[REQUESTED, FORWARDED],
                receiver=self.request.user
            ).count()
        self.NOT_INSTALLED_APPS.update({
            'attendance': 'The Module is not installed'
        })
        return 0

    @property
    def leave_requests(self):
        if django_apps.is_installed('irhrs.leave'):
            from irhrs.leave.models import LeaveRequest
            from irhrs.leave.constants.model_constants import REQUESTED, \
                FORWARDED
            return LeaveRequest.objects.filter(
                status__in=[REQUESTED, FORWARDED],
                recipient=self.request.user
            ).count()
        self.NOT_INSTALLED_APPS.update({
            'leave': 'The Module is not installed'
        })
        return 0

    @property
    def overtime_claims(self):
        if django_apps.is_installed('irhrs.attendance'):
            from irhrs.attendance.models import OvertimeClaim
            from irhrs.attendance.constants import FORWARDED, REQUESTED
            return OvertimeClaim.objects.filter(
                status__in=[REQUESTED, FORWARDED],
                recipient=self.request.user
            ).count()
        return 0

    @property
    def payroll_requests(self):
        if django_apps.is_installed('irhrs.payroll'):
            pass
        self.NOT_INSTALLED_APPS.update({
            'payroll': 'The Module is not installed'
        })
        return 0

    def list(self, request, *args, **kwargs):
        fields = [
            'attendance_adjustments',
            'leave_requests',
            'overtime_claims',
            'payroll_requests'
        ]
        results = {field: getattr(self, field) for field in fields}
        if self.NOT_INSTALLED_APPS:
            results.update({
                '_meta': self.NOT_INSTALLED_APPS
            })
        return Response(results)
