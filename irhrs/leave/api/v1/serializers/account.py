import logging
from dateutil.relativedelta import relativedelta

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, BooleanField, ChoiceField,FloatField,IntegerField
from rest_framework.relations import PrimaryKeyRelatedField

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import DummyObject, humanize_interval
from irhrs.core.validators import validate_multiple_of_half
from irhrs.leave.api.v1.serializers.rule import LeaveRuleSerializer
from irhrs.leave.constants.model_constants import ASSIGNED, UPDATED, ALL, \
    REMOVED, ADDED, COMPENSATORY, DAYS, MONTHS, YEARS, ASSIGNED_WITH_BALANCE, TIME_OFF, CREDIT_HOUR
from irhrs.leave.models import LeaveAccount, LeaveRule, LeaveAccountHistory, \
    LeaveType, MasterSetting
from irhrs.leave.models.account import CompensatoryLeaveAccount
from irhrs.leave.utils.leave_request import is_hourly_account
from irhrs.users.api.v1.serializers.thin_serializers import (
    UserThinSerializer, UserThickSerializer
)

USER = get_user_model()


class LeaveUserSerializer(DummySerializer):
    user = UserThickSerializer()
    supervisor = UserThinSerializer(source="user.first_level_supervisor")
    can_assign = BooleanField(default=False)


class UserLeaveAssignSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LeaveAccount

    def get_fields(self):
        organization = self.context.get('organization')

        default_balance_field = FloatField(
            write_only=True, allow_null=True, min_value=0,
            required=False,
            validators=[validate_multiple_of_half]
        )
        if LeaveRule.objects.filter(
            id=self.initial_data['leave_rule'],
            leave_type__category__in=[TIME_OFF, CREDIT_HOUR]
        ).exists():
            default_balance_field=IntegerField(write_only=True, allow_null=True, min_value=0, required=False)

        return {
            "users": PrimaryKeyRelatedField(
                queryset=USER.objects.filter(
                    detail__organization=organization,
                    user_experiences__is_current=True
                ).distinct(),
                many=True,
                write_only=True
            ),
            "action": ChoiceField(
                choices=(
                    ('Assign', 'Assign'),
                    ('Remove', 'Remove')
                ),
                write_only=True
            ),
            'leave_rule': PrimaryKeyRelatedField(
                queryset=LeaveRule.objects.filter(
                    leave_type__master_setting__organization=organization
                ),
                write_only=True
            ),
            "assign_default_balance": BooleanField(write_only=True, default=False),
            'default_balance': default_balance_field,
            'remarks': CharField(write_only=True, allow_blank=True, max_length=255, required=False),
            "message": CharField(read_only=True)
        }

    def create(self, validated_data):
        leave_rule = validated_data.get('leave_rule')
        selected_users = validated_data.get('users')
        action = validated_data.get('action')
        assign_balance = {
            "default_balance": validated_data.get('default_balance', 0),
            "assign_default_balance":  validated_data.get('assign_default_balance', False),
            "remarks":  validated_data.get('remarks', "")
        }

        if action == 'Assign':
            return self.assign_users(selected_users, leave_rule, assign_balance)
        else:
            return self.remove_users(selected_users, leave_rule)

    def assign_users(self, selected_users, leave_rule, assign_balance):
        leave_type = leave_rule.leave_type
        master_setting = MasterSetting.objects.get(leave_types=leave_type)
        if master_setting:
            status = master_setting.status
            if status == 'Expired':
                raise ValidationError({
                    "master_setting": "Cannot assign user to expired master setting."
                })
        users = USER.objects.exclude(
        ).filter(
            id__in=[u.id for u in selected_users],
            **self.get_filters(
                leave_type=leave_type
            )
        )
        count = 0
        reassigned = 0
        message = 'Successfully '
        for user in users:
            try:
                account, created = LeaveAccount.objects.get_or_create(
                    user=user,
                    rule=leave_rule
                )
                assign_default_balance = assign_balance.get('assign_default_balance')
                default_balance = assign_balance.get('default_balance') if assign_default_balance else 0
                remarks = assign_balance.get('remarks') if assign_default_balance else 0
                action = ASSIGNED_WITH_BALANCE if assign_default_balance else ASSIGNED
                if created:
                    account.is_archived = False
                    account.balance = default_balance
                    account.usable_balance = default_balance
                    account.save()
                    count += 1
                    LeaveAccountHistory.objects.create(
                        account=account,
                        user=user,
                        actor=getattr(self.request, 'user', None),
                        action=action,
                        previous_balance=0,
                        previous_usable_balance=0,
                        new_balance=default_balance,
                        new_usable_balance=default_balance,
                        remarks=remarks
                    )
                else:
                    account.is_archived = False
                    reassigned += 1
                    LeaveAccountHistory.objects.create(
                        account=account,
                        user=user,
                        actor=getattr(self.request, 'user', None),
                        action=action,
                        previous_balance=account.balance,
                        previous_usable_balance=account.usable_balance,
                        new_balance=default_balance,
                        new_usable_balance=default_balance,
                        remarks=remarks
                    )
                    account.balance = default_balance
                    account.usable_balance = default_balance
                    account.save()
            except LeaveAccount.MultipleObjectsReturned:
                pass
        if reassigned > 0:
            message += f'Reassigned to {reassigned} and '
        message += f"Assigned leave to {count} users."
        return DummyObject(
            message=message
        )

    def remove_users(self, selected_users, leave_rule):
        qs = LeaveAccount.objects.filter(
            rule=leave_rule,
            user__in=selected_users,
            is_archived=False
        )
        count = 0
        for account in qs:
            account.is_archived = True
            account.save()
            count += 1
            LeaveAccountHistory.objects.create(
                account=account,
                user=account.user,
                actor=getattr(self.request, 'user', None),
                action=REMOVED,
                previous_balance=account.balance,
                previous_usable_balance=account.usable_balance,
                new_balance=account.balance,
                new_usable_balance=account.usable_balance
            )
        return DummyObject(
            message=f"Successfully removed {count} users from the rule."
        )

    def get_filters(self, leave_type):
        organization = self.context.get('organization')
        gender = leave_type.applicable_for_gender
        marital_status = leave_type.applicable_for_marital_status

        fil = {
            'detail__organization': organization,
            'user_experiences__is_current': True,
            'attendance_setting__isnull': False
        }

        if gender and gender != ALL:
            fil.update({
                'detail__gender': gender
            })

        if marital_status and marital_status != ALL:
            fil.update({
                'detail__marital_status': marital_status
            })

        return fil

    def validate(self, data):
        assign_default_balance = data.get('assign_default_balance')
        default_balance = data.get('default_balance')
        remarks = data.get('remarks')
        errors = dict()
        if not assign_default_balance and (default_balance or remarks):
            raise ValidationError(
                _("Cannot assign default value or remarks. Please check the fields again.")
            )
        if assign_default_balance and not default_balance:
            errors.update({
                "default_balance": _("This field may not be blank.")
            })
        if assign_default_balance and not remarks:
            errors.update({
                "remarks": _("This field may not be blank")
            })
        if errors:
            raise ValidationError(errors)
        return data

    @staticmethod
    def validate_users(user):
        if not user:
            raise ValidationError(
                "Please select valid users"
            )
        return user


class LeaveAccountSerializer(DynamicFieldsModelSerializer):
    rule = LeaveRuleSerializer(
        read_only=True,
        fields=(
            'id', 'name', 'is_paid', 'can_apply_half_shift',
            'require_docs', 'require_docs_for', 'can_apply_beyond_zero_balance',
            'beyond_limit'
        )
    )
    remark = serializers.CharField(max_length=600, write_only=True)
    leave_type = serializers.SerializerMethodField(read_only=True)
    visible = serializers.ReadOnlyField(
        source='rule.leave_type.visible_on_default'
    )

    class Meta:
        model = LeaveAccount
        fields = (
            'rule', 'balance', 'usable_balance', 'is_archived',
            'last_renewed', 'last_accrued', 'id', 'remark', 'leave_type',
            'visible'
        )
        read_only_fields = (
            'user', 'rule', 'last_renewed', 'last_accrued', 'id',
            'usable_balance'
        )

    def get_leave_type(self, instance):
        leave_type = instance.rule.leave_type
        return {
            'id': leave_type.id,
            'name': leave_type.name,
            'category': leave_type.category
        }

    def update(self, instance, validated_data):
        remark = validated_data.pop('remark')
        previous_balance = instance.balance
        previous_usable_balance = instance.usable_balance
        difference = instance.balance - instance.usable_balance
        instance = super().update(instance, validated_data)
        instance.usable_balance = instance.balance - difference
        instance.save()

        LeaveAccountHistory.objects.create(
            account=instance,
            user=instance.user,
            actor=getattr(self.request, 'user', None),
            action=UPDATED,
            previous_balance=previous_balance,
            previous_usable_balance=previous_usable_balance,
            new_balance=instance.balance,
            new_usable_balance=instance.usable_balance,
            remarks=remark
        )
        return instance


class LeaveAccountUpdateSerializer(LeaveAccountSerializer):
    leave_account = serializers.PrimaryKeyRelatedField(
        queryset=LeaveAccount.objects.all()
    )

    class Meta(LeaveAccountSerializer.Meta):
        fields = (
            'balance', 'remark', 'leave_account',
            'next_accrue', 'next_deduction', 'next_renew'
        )

    def validate_leave_account(self, leave_account):
        if leave_account.rule.leave_type.category == COMPENSATORY:
            raise ValidationError(
                "Editing Compensatory Leave has been deprecated."
            )
        return leave_account


class LeaveAccountListSerializer(UserThickSerializer):
    supervisor = UserThickSerializer(source='first_level_supervisor')
    employment_status = serializers.ReadOnlyField(
        source='detail.employment_status.title'
    )

    class Meta(UserThickSerializer.Meta):
        fields = UserThickSerializer.Meta.fields + [
            'supervisor', 'employment_status'
        ]


class LeaveAccountBulkUpdateSerializer(DummySerializer):
    leave_accounts = LeaveAccountUpdateSerializer(many=True)

    def create(self, validated_data):
        accounts = validated_data.get('leave_accounts')
        for account in accounts:
            instance = account.get('leave_account')
            ser = LeaveAccountSerializer(
                context=self.context,
                instance=instance,
                data=account
            )
            if ser.is_valid(raise_exception=True):
                ser.save()
        return DummyObject(**validated_data)


class LeaveAccountHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThinSerializer(fields=(
        'id', 'full_name', 'profile_picture'
    ))
    previous_balance = serializers.SerializerMethodField()
    previous_usable_balance = serializers.SerializerMethodField()
    new_balance = serializers.SerializerMethodField()
    new_usable_balance = serializers.SerializerMethodField()

    class Meta:
        model = LeaveAccountHistory
        fields = (
            'actor', 'action', 'previous_balance',
            'previous_usable_balance', 'new_balance', 'new_usable_balance',
            'remarks', 'created_at'
        )

    @staticmethod
    def get_previous_balance(history):
        if is_hourly_account(history.account):
            return humanize_interval(history.previous_balance * 60)
        return history.previous_balance

    @staticmethod
    def get_previous_usable_balance(history):
        if is_hourly_account(history.account):
            return humanize_interval(history.previous_usable_balance * 60)
        return history.previous_usable_balance

    @staticmethod
    def get_new_balance(history):
        if is_hourly_account(history.account):
            return humanize_interval(history.new_balance * 60)
        return history.new_balance

    @staticmethod
    def get_new_usable_balance(history):
        if is_hourly_account(history.account):
            return humanize_interval(history.new_usable_balance * 60)
        return history.new_usable_balance


class MigrateOldLeaveAccountSerializer(serializers.Serializer):

    def get_fields(self):
        active_setting = self.context.get('active_setting')
        expired_setting = self.context.get('expired_setting')
        # Filter old and new according to active() and expired().last() MS.
        fields = {
            'old_leave_type': PrimaryKeyRelatedField(
                queryset=LeaveType.objects.filter(
                    master_setting=expired_setting
                )
            ),
            'new_leave_type': PrimaryKeyRelatedField(
                queryset=LeaveType.objects.filter(
                    master_setting=active_setting
                )
            )
        }
        return fields


class BulkMigrateOldAccountSerializer(serializers.Serializer):

    def get_fields(self):
        return {
            'accounts_to_migrate':
                MigrateOldLeaveAccountSerializer(
                    context=self.context,
                    many=True
                )
        }

    @transaction.atomic()
    def transfer_balance(self, account, balance_to_add):
        actor = getattr(
            self.context.get('request'),
            'user',
            get_system_admin()
        )
        account_history = LeaveAccountHistory(
            account=account,
            user=account.user,
            actor=actor,
            action=ADDED,
            previous_balance=account.balance,
            previous_usable_balance=account.usable_balance,
            remarks=f'Added {balance_to_add} to leave after porting.'
        )
        account.balance = account.usable_balance = balance_to_add
        account_history.new_usable_balance = account.usable_balance
        account_history.new_balance = account.balance
        account.save()
        account_history.save()
        logger = logging.getLogger(__name__)
        logger.info(
            f"Added {balance_to_add} to {account.user} on account "
            f"{account.id} due to port by {actor}"
        )

    def port_users(self, validated_data):
        old_leave_type = validated_data.get('old_leave_type')
        new_leave_type = validated_data.get('new_leave_type')

        new_accounts = LeaveAccount.objects.filter(
            rule__leave_type=new_leave_type
        )
        old_accounts = LeaveAccount.objects.filter(
            rule__leave_type=old_leave_type
        )
        for account in new_accounts:
            identical_old_account = old_accounts.filter(
                user=account.user,
                rule__leave_type=old_leave_type
            ).first()
            if identical_old_account:
                # transfer balance
                self.transfer_balance(
                    account,
                    identical_old_account.balance  # not usable balance as the
                    # leave request will be archived and user applies again.
                )
            else:
                logger = logging.getLogger(__name__)
                logger.debug(
                    f"Ignored {account.user}'s account {account.id} due to no "
                    f"identical account in previous type."
                )
        # Port Users HERE.
        return DummyObject(**validated_data)

    def create(self, validated_data):
        accounts_to_migrate = validated_data.get('accounts_to_migrate')
        for leave_types_mapping in accounts_to_migrate:
            self.port_users(leave_types_mapping)
        return DummyObject(**validated_data)


class CompensatoryLeaveAccountSerializer(DynamicFieldsModelSerializer):
    expires_on = serializers.SerializerMethodField()

    class Meta:
        model = CompensatoryLeaveAccount
        fields = 'leave_for', 'balance_granted', 'balance_consumed', \
                 'expires_on'

    def get_expires_on(self, instance):
        rule = instance.leave_account.rule.compensatory_rule
        collapse_after = rule.collapse_after
        collapse_after_unit = rule.collapse_after_unit
        to_be_consumed_before = {
            DAYS: instance.leave_for + relativedelta(
                days=collapse_after
            ),
            MONTHS: instance.leave_for + relativedelta(
                months=collapse_after
            ),
            YEARS: instance.leave_for + relativedelta(
                years=collapse_after
            )
        }.get(collapse_after_unit)
        return to_be_consumed_before
