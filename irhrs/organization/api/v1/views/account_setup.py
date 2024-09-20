from rest_framework.response import Response
from rest_framework.views import APIView

from irhrs.attendance.models import WorkShift
from irhrs.core.mixins.viewset_mixins import OrganizationCommonsMixin, OrganizationMixin
from irhrs.leave.models import MasterSetting
from irhrs.organization.api.v1.permissions import OrganizationPermission
from irhrs.organization.models import FiscalYear, Holiday, OrganizationDivision, EmploymentStatus, EmploymentLevel, \
    EmploymentJobTitle
from irhrs.permission.constants.permissions import HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory


class OrganizationAccountSetupStatus(OrganizationCommonsMixin,
                                     OrganizationMixin, APIView
                                     ):
    # Fiscal Year
    # Leave Policies
    # Attendance Policies
    # Holidays
    # Division
    # Employment Status
    # Employment Level
    permission_classes = [permission_factory.build_permission(
        "OrganizationSetupStatus",
        allowed_to=[HAS_PERMISSION_FROM_METHOD]
    )]

    def get(self, request, *args, **kwargs):
        _filter = {
            'organization': self.get_organization()
        }
        headings = dict(
            fiscal_year=True if FiscalYear.objects.current(
                self.get_organization()
            ) else False,
            leave_policies=MasterSetting.objects.filter(
                **_filter
            ).active().exists(),
            attendance_policies=WorkShift.objects.filter(**_filter).exists(),
            holidays=Holiday.objects.filter(**_filter).exists(),
            division=OrganizationDivision.objects.filter(**_filter).exists(),
            employment_type=EmploymentStatus.objects.filter(
                **_filter
            ).exists(),
            employment_level=EmploymentLevel.objects.filter(
                **_filter
            ).exists(),
            job_title=EmploymentJobTitle.objects.filter(
                **_filter
            ).exists()
        )
        details = []
        total = len(headings)
        _pending_count = 0
        for k, v in headings.items():
            heading = " ".join(k.split('_')).title()
            if not v:
                details.append(
                    {
                        'heading': heading,
                        'status': 'Pending'
                    }
                )
                _pending_count += 1
            else:
                details.append(
                    {
                        'heading': heading,
                        'status': 'Completed'
                    }
                )

        req = {
            'total_count': total,
            'pending_count': _pending_count,
            'details': details,
        }
        return Response(req)

    def has_user_permission(self):
        return bool(
            self.request.user.switchable_organizations_pks
        )
