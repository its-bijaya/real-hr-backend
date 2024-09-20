from irhrs.attendance.api.v1.serializers.timesheet_registration_report_settings import \
    TimeSheetRegistrationReportSettingsSerializer
from irhrs.attendance.models.timesheet_report_settings import TimeSheetRegistrationReportSettings
from irhrs.core.mixins.viewset_mixins import RetrieveUpdateViewSetMixin, OrganizationCommonsMixin, \
    OrganizationMixin
from irhrs.permission.constants.permissions import ATTENDANCE_TIMESHEET_REPORT_SETTING_PERMISSION
from irhrs.permission.permission_classes import permission_factory


class TimeSheetRegistrationReportSettingsViewSet(
    OrganizationCommonsMixin,
    OrganizationMixin,
    RetrieveUpdateViewSetMixin
):
    serializer_class = TimeSheetRegistrationReportSettingsSerializer
    queryset = TimeSheetRegistrationReportSettings.objects.all()
    permission_classes = [
        permission_factory.build_permission(
            'TimeSheetRegistrationReportSettingPermission',
            allowed_to=[ATTENDANCE_TIMESHEET_REPORT_SETTING_PERMISSION]
        )
    ]

    def get_object(self):
        obj = self.get_queryset().first()
        if not obj:
            return TimeSheetRegistrationReportSettings.\
                get_default_timesheet_registration_report_settings(
                    self.get_organization()
                )
        return obj
