from irhrs.leave.api.v1.permissions import LeaveReportPermission


class LeaveReportPermissionMixin:
    permission_classes = [LeaveReportPermission]

    def has_user_permission(self):
        if self.request.query_params.get("supervisor"):
            return self.request.query_params.get("supervisor") == str(
                self.request.user.id)
        return False
