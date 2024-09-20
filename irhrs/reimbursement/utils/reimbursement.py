from django.contrib.auth import get_user_model
from django.utils.functional import cached_property
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.payroll import (
    SUPERVISOR,
    PENDING,
    FIRST,
    SECOND,
    THIRD,
    EMPLOYEE,
    ALL
)
from irhrs.core.utils import get_system_admin
from irhrs.reimbursement.models import (
    ExpenseApprovalSetting,
    SettlementApprovalSetting
)
from irhrs.reimbursement.models.reimbursement import AdvanceExpenseRequestApproval, \
    AdvanceExpenseCancelRequestApproval
from irhrs.reimbursement.models.settlement import SettlementApproval
from irhrs.users.api.v1.serializers.thin_serializers import UserSignatureSerializer

User = get_user_model()


class AdvanceExpenseSerializerMixin:
    @cached_property
    def approval_settings(self):
        return ExpenseApprovalSetting.objects.filter(
            organization=self.context["organization"]
        ).order_by("approval_level")

    def get_supervisors_from_supervisor_level(self, supervisor_level: str):
        supervisor_authority = [ALL, FIRST, SECOND, THIRD].index(
            supervisor_level
        )

        supervisors_qs = self.request.user.supervisors.all()

        # returns queryset of supervisors with respective authority order excluding system admin
        supervisors_id = supervisors_qs.filter(
            authority_order__in=[1, 2, 3]
            if supervisor_authority == 0
            else [supervisor_authority]
        ).exclude(supervisor=get_system_admin()).values_list("supervisor", flat=True)
        return User.objects.filter(id__in=supervisors_id)

    @cached_property
    def approvals(self):
        if not self.approval_settings:
            raise ValidationError("Approval Levels not set.")

        approvals = []

        # prior_employee_level_exists is a flag to determine if there are any
        # preceding employee_level setting in approval_settings. If there are
        # prior employee_level_settings before supervisor_level, user should
        # be able to make request regardless of whether supervisor with particular
        # authority exists or not, otherwise request should be denied.
        prior_employee_level_exists = False
        for index, approval_setting in enumerate(self.approval_settings, start=1):
            if approval_setting.approve_by == EMPLOYEE:
                users_approvers = []
                if not approval_setting.select_employee:
                    users_approvers = approval_setting.employee.all()
                prior_employee_level_exists = True

            else:
                users_approvers = self.get_supervisors_from_supervisor_level(
                    approval_setting.supervisor_level
                )
                if not (users_approvers or prior_employee_level_exists):
                    raise ValidationError({
                        "non_field_errors": "No matching supervisor found. Please contact HR."
                    })

                # if there are no user_approvers but prior employee level exists
                # go to the next approval setting without adding this approval settings
                # information to approvals list
                if not users_approvers:
                    continue

            approvals.append(
                {
                    "user": users_approvers,
                    "status": PENDING,
                    "role": EMPLOYEE if approval_setting.approve_by == EMPLOYEE else SUPERVISOR,
                    "level": index
                }
            )

        return approvals

    @cached_property
    def recipient(self):
        return self.approvals[0]['user']

    def set_approvers(self, cls, instance, selected_approvers):
        approval_level_map = dict()
        if selected_approvers:
            approval_level_map = {
                approver["approval_level"]: [approver["recipient"]]
                for approver in selected_approvers
            }
        for approval in self.approvals:
            user = approval.pop('user', [])
            approval_level = approval["level"]
            request_field_mapper = {
                SettlementApproval: "settle",
                AdvanceExpenseCancelRequestApproval: "expense_cancel"
            }
            request_field = request_field_mapper.get(cls, 'expense')

            create_data = {
                request_field: instance,
                **approval
            }
            request_approval = cls.objects.create(**create_data)

            if approval_level in approval_level_map:
                user = approval_level_map[approval_level]
            request_approval.user.set(user)

        first_approval = instance.active_approval
        instance.recipient.set(first_approval.user.all())

    @staticmethod
    def get_employee(instance):
        fields = [
            'id',
            'full_name',
            'profile_picture',
            'cover_picture',
            'job_title',
            'organization',
            'is_online',
            'is_current'
        ]
        if instance.add_signature:
            fields.append('signature')
        serializer_data = dict(fields=fields)
        return UserSignatureSerializer(
            instance=instance.employee,
            **serializer_data
        ).data

    def validate(self, attr):
        add_signature = attr.get('add_signature')
        request = self.context.get('request')
        if request and add_signature and not request.user.signature:
            raise ValidationError({
                'detail': 'Add signature within your general information.'
            })
        return super().validate(attr)

class SettlementSerializerMixin(AdvanceExpenseSerializerMixin):
    @cached_property
    def approval_settings(self):
        return SettlementApprovalSetting.objects.filter(
            organization=self.context["organization"]
        ).order_by("approval_level")
