from irhrs.attendance.api.v1.permissions import AttendanceReportPermission


class AttendanceReportPermissionMixin:
    permission_classes = [AttendanceReportPermission]

    def has_user_permission(self):
        if self.request.query_params.get("supervisor"):
            return self.request.query_params.get("supervisor") == str(
                self.request.user.id)
        return False


class HROnlyAttendanceReportPermissionMixin(AttendanceReportPermissionMixin):
    def has_user_permission(self):
        return False
