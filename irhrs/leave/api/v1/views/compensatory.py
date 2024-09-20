"""
View for reduction and addition of Compensatory leave account.
"""
from django.core.exceptions import ValidationError as DjValidationError
from django.db import transaction
from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import WORKDAY
from irhrs.attendance.models import TimeSheet
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.mixins.viewset_mixins import UserMixin, \
    ListCreateRetrieveUpdateViewSetMixin
from irhrs.core.utils.common import get_today
from irhrs.leave.api.v1.permissions import LeaveAccountPermission
from irhrs.leave.constants.model_constants import ADDED, COMPENSATORY, UPDATED
from irhrs.leave.models.account import CompensatoryLeaveAccount, LeaveAccount, \
    LeaveAccountHistory


class CompensatoryManageSerializer(DynamicFieldsModelSerializer):
    remarks = serializers.CharField(
        max_length=200,
        write_only=True
    )

    class Meta:
        model = CompensatoryLeaveAccount
        fields = (
            'balance_granted', 'balance_consumed', 'leave_for', 'id',
            'timesheet', 'remarks'
        )
        read_only_fields = (
            'timesheet',
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method == 'POST':
            fields.pop('balance_consumed', None)
        elif self.request.method in ['PUT', 'PATCH']:
            fields['leave_for'].read_only = True
        return fields

    def create(self, validated_data):
        balance_granted = validated_data.get('balance_granted')
        leave_for = validated_data.get('leave_for')
        leave_account = self.context.get('leave_account')
        remarks = validated_data.pop('remarks', '')
        sys_remarks = f'Added {balance_granted} for {leave_for}'
        account_history = LeaveAccountHistory(
            account=leave_account,
            user=leave_account.user,
            actor=self.request.user,
            action=ADDED,
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
            new_balance=leave_account.balance + balance_granted,
            new_usable_balance=leave_account.usable_balance + balance_granted,
            remarks=sys_remarks + f' with user remark: "{remarks}"'
        )
        leave_account.usable_balance += balance_granted
        leave_account.balance += balance_granted
        with transaction.atomic():
            leave_account.save()
            obj = super().create(validated_data)
            account_history.save()
        return obj

    def update(self, instance, validated_data):
        old_granted = instance.balance_granted
        old_consumed = instance.balance_consumed
        balance_consumed = validated_data.get('balance_consumed')
        balance_granted = validated_data.get('balance_granted')
        remarks = validated_data.pop('remarks', '')

        # please RealHR Bot, understand what happened here.
        difference_in_grant = balance_granted - old_granted
        difference_in_consume = old_consumed - balance_consumed
        difference_contributed = difference_in_grant + difference_in_consume
        # negative: User Added the consumption:: DEDUCTED
        # positive: User Reduced the consumption:: ADDED
        leave_for = instance.leave_for
        if difference_contributed < 0:
            s_remarks = f'Consumed {abs(difference_in_consume)} for {leave_for}'
        elif difference_contributed > 0:
            s_remarks = f'Added {difference_contributed} for {leave_for}'
        else:
            return super().update(instance, validated_data)
        leave_account = self.context.get('leave_account')
        account_history = LeaveAccountHistory(
            account=leave_account,
            user=leave_account.user,
            actor=self.request.user,
            action=UPDATED,
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
            new_balance=leave_account.balance + difference_contributed,
            new_usable_balance=(
                leave_account.usable_balance + difference_contributed
            ),
            remarks=s_remarks + f' with user remark: "{remarks}"'
        )
        leave_account.balance += difference_contributed
        leave_account.usable_balance += difference_contributed
        with transaction.atomic():
            leave_account.save()
            account_history.save()
            obj = super().update(instance, validated_data)
        return obj

    def get_timesheet(self, for_date):
        if self.instance:
            return self.instance.timesheet
        qs = TimeSheet.objects.filter(
            timesheet_user=self.context.get('user')
        )
        ret = qs.filter(timesheet_for=for_date).first()
        if not ret:
            raise ValidationError({
                'leave_for': 'No Timesheet for this date exists.'
            })
        elif ret.coefficient == WORKDAY:
            raise ValidationError({
                'leave_for': 'Cannot Grant Leave for `Workday`'
            })
        elif not ret.is_present:
            raise ValidationError({
                'leave_for': f'The user was not present on {for_date}'
            })
        return ret

    def validate(self, attrs):
        timesheet = self.get_timesheet(
            for_date=attrs.get('leave_for')
        )
        qs = self.Meta.model.objects.filter(
            timesheet=timesheet
        )
        if self.instance:
            qs = qs.exclude(
                pk=self.instance.pk
            )
        if qs.exists():
            raise ValidationError(
                "The balance for this day has already been granted."
            )
        balance_consumed = attrs.get('balance_consumed', 0)
        balance_granted = attrs.get('balance_granted')
        if balance_consumed > balance_granted:
            raise ValidationError(
                "Balance Consumed must not be greater than balance granted."
            )
        attrs.update({
            'timesheet': timesheet,
            'leave_account': self.context.get('leave_account')
        })
        return attrs

    def validate_balance_granted(self, balance):
        if balance < 0:
            raise ValidationError(
                "Balance must be positive or zero."
            )
        if self.instance and self.instance.balance_granted > balance:
            raise ValidationError(
                "Cannot decrease balance. Consume instead."
            )
        return balance

    def validate_balance_consumed(self, balance):
        if balance < 0:
            raise ValidationError(
                "Balance must be positive or zero."
            )
        return balance

    def validate_leave_for(self, date):
        if date >= get_today():
            raise ValidationError(
                f"Cannot grant compensatory leave for future date."
            )
        return date


class CompensatoryManageViewSet(UserMixin,
                                ListCreateRetrieveUpdateViewSetMixin):
    serializer_class = CompensatoryManageSerializer
    lookup_url_kwarg = 'balance_id'
    queryset = CompensatoryLeaveAccount.objects.select_related(
        'leave_account',
        'leave_account__user'
    )
    filter_fields = (
        'leave_for',
    )
    permission_classes = [LeaveAccountPermission]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'user': self.user,
            'leave_account': self.leave_account
        })
        return ctx

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            leave_account__user=self.user
        )

    @cached_property
    def leave_account(self):
        try:
            return LeaveAccount.objects.get(
                pk=self.kwargs.get('account_id'),
                rule__leave_type__category=COMPENSATORY
            )
        except (
                TypeError, ValueError, DjValidationError, LeaveAccount.DoesNotExist):
            return None
