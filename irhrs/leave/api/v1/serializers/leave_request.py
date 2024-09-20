import datetime

from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import CONFIRMED
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils import nested_getattr, get_system_admin, subordinates
from irhrs.core.utils.common import combine_aware, humanize_interval
from irhrs.core.utils.dependency import get_dependency
from irhrs.core.validators import validate_past_date
from irhrs.hris.utils import choice_field_display
from irhrs.leave.constants.model_constants import APPROVED, DENIED, REQUESTED, \
    FIRST_HALF, SECOND_HALF, DEDUCTED, ADDED, FORWARDED, FULL_DAY, EXPIRED, APPROVER, CREDIT_HOUR, \
    TIME_OFF, \
    HALF_LEAVE_CHOICES
from irhrs.leave.models import LeaveRequestHistory, LeaveAccount, \
    LeaveAccountHistory, MasterSetting
from irhrs.leave.models.request import LeaveSheet, LeaveRequestDeleteHistory, \
    LeaveRequestDeleteStatusHistory
from irhrs.leave.utils import leave_request as leave_utils, leave_sheet
from irhrs.leave.utils import balance as balance_utils
from irhrs.leave.utils.balance import (
    revert_leave_for_date,
    recalibrate_overtime_due_to_leave_updates,
    leave_approve_post_actions
)
from irhrs.leave.utils.leave_request import (
    get_appropriate_recipient,
    get_leave_request_recipient, validate_has_supervisor,
    validate_leave_occurrence,
    validate_require_experience,
    require_prior_approval, require_docs,
    validate_limit_limitation, validate_continuous_leave,
    validate_require_time_period, validate_depletion_required,
    validate_action_permission,
    test_if_overtime_is_claimed, test_if_payroll_is_generated,
    validate_holiday_inclusive, check_multi_level_approval,
    validate_minimum_maximum_range, is_hourly_account, raise_validation_if_payroll_is_generated
)
from irhrs.leave.utils.notification import send_leave_notification
from irhrs.leave.utils.timesheet import create_leave_timesheet_for_user
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.payroll.utils.generate import \
    raise_validation_error_if_payroll_in_generated_or_processing_state
from irhrs.permission.constants.permissions import LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION, \
    OFFLINE_LEAVE_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer, UserThickSerializer
from irhrs.users.models import UserSupervisor
from ....models import LeaveRequest
from ....utils.validations import raise_no_exception

User = get_user_model()


class LeaveRequestHelper:
    def make_history(self, instance, supervisor_remarks):
        instance.history.create(
            action=instance.status,
            actor=self.request.user,
            forwarded_to=instance.recipient,
            remarks=supervisor_remarks or instance.details,
            recipient_type=instance.recipient_type
        )
        send_leave_notification(leave_request=instance)

    def make_changes_to_balances(self, leave_request, as_hr=False):
        leave_account = leave_request.leave_account
        leave_account.refresh_from_db()
        account_history = LeaveAccountHistory(
            account=leave_account,
            user=leave_request.user,
            actor=getattr(self.request, 'user') or get_system_admin(),
            previous_balance=leave_account.balance,
            previous_usable_balance=leave_account.usable_balance,
            new_balance=leave_account.balance,
            new_usable_balance=leave_account.usable_balance
        )
        status = REQUESTED if as_hr else leave_request.status
        leave_category = leave_account.rule.leave_type.category
        balance_display = self.get_balance_display(leave_request.balance, leave_category)
        if status == REQUESTED:
            balance = (
                leave_account.usable_balance
                - leave_request.balance
            )
            leave_account.usable_balance = balance
            account_history.action = DEDUCTED
            account_history.new_usable_balance = balance
            account_history.remarks = (
                f"Deducted {balance_display} due to leave request on "
                f"{leave_request.start.astimezone().date()}"
            )

        elif status == APPROVED:
            # handle case when requested by ADMIN, directly approved.
            first = leave_request.history.order_by(
                'created_at'
            ).first()

            # When normal user requests a leave it's usable balance is
            # deducted from account, when admin approves later its actual
            # balance is deducted (normal scenario)

            if first and first.action == APPROVED:
                # When admin assigns a leave, its usual balance has not been
                # deducted yet therefore we have to deduct its usable balance
                # as well as actual balance
                balance = (
                    leave_account.usable_balance
                    - leave_request.balance
                )
                leave_account.usable_balance = balance
                account_history.action = DEDUCTED
                account_history.new_usable_balance = balance

            balance = (
                leave_account.balance
                - leave_request.balance
            )
            leave_account.balance = balance
            account_history.action = DEDUCTED
            account_history.new_balance = balance
            leave_start = leave_request.start.astimezone()
            account_history.remarks = (
                f"Deducted {balance_display} due to leave approval for "
                f"{leave_start.date()}"  # UTC time
            )

        elif status == DENIED:
            balance = (
                leave_account.usable_balance
                + leave_request.balance
            )
            leave_account.usable_balance = balance
            account_history.action = ADDED
            account_history.new_usable_balance = leave_account.usable_balance
            account_history.remarks = (
                f"Added {balance_display} due to leave rejection for "
                f"{leave_request.start.astimezone().date()}"
            )
        account_history.save()
        leave_account.save()

    def manage_time_sheets_and_overtime(self, instance):
        if instance.status == APPROVED:
            with transaction.atomic():
                create_leave_timesheet_for_user(instance)
            recalibrate_overtime_due_to_leave_updates(
                instance,
                self.request.user
            )

    @staticmethod
    def get_balance_display(balance, leave_category):
        if leave_category in (CREDIT_HOUR, TIME_OFF):
            return humanize_interval(balance * 60)
        return balance

    def approve_leave_request(self, instance):
        recipient, recipient_type, status = get_leave_request_recipient(instance)
        if status in [APPROVED, DENIED]:
            self.make_changes_to_balances(instance)
            # send_leave_notification(instance)
        else:
            instance.status = status
            # add_notification(
            #     text=f"Leave request by {instance.user}.",
            #     actor=instance.recipient,
            #     action=instance,
            #     recipient=recipient,
            #     url=f"/user/assessment/new-assessment"
            # )
        instance.recipient = recipient
        instance.recipient_type = recipient_type
        instance.save()


class LeaveRequestSerializer(LeaveRequestHelper, DynamicFieldsModelSerializer):
    steps = None
    user = UserThickSerializer(
        read_only=True,
        exclude_fields=['email']
    )
    created_by = UserThinSerializer(
        read_only=True,
        exclude_fields=['email']
    )
    leave_type = serializers.SerializerMethodField()
    leave_type_category = serializers.SerializerMethodField()
    permissions = serializers.ReadOnlyField()

    class Meta:
        model = LeaveRequest
        user_fields = (
            'details', 'part_of_day', 'start', 'end', 'leave_account',
            'attachment'
        )
        admin_fields = (
            'user', 'is_archived', 'status'
        )
        fields = (
            'user', 'leave_account', 'details', 'created_by', 'created_at',
            'id', 'part_of_day', 'status', 'is_archived', 'start', 'end',
            'balance', 'leave_type', 'attachment', 'permissions', 'recipient_type',
            'leave_type_category',
        )
        read_only_fields = ('balance', 'id', 'leave_type', 'recipient_type')
        extra_kwargs = {
            'attachment': {
                'required': False
            }
        }

    @staticmethod
    def _validate_no_old_leaves(user, start_timestamp, end_timestamp):
        """
        Check conflicting leaves for given range
        """
        if user.leave_requests.exclude(
            status=DENIED
        ).filter(
            Q(
                start__gte=start_timestamp,
                start__lt=end_timestamp
            )
            | Q(
                end__gt=start_timestamp,
                end__lte=end_timestamp
            )
            | Q(
                start__lte=start_timestamp,
                end__gte=end_timestamp
            )
        ).exists():
            raise ValidationError(
                "The leave for this range already exists"
            )

    @staticmethod
    def warn_before_skipping_leave_validations(
        start_timestamp,
        end_timestamp, leave_account, leave_balance, attrs, user
    ):
        """
        List of all validation to be skipped by hr and supervisor.
        List of validations are raised concurrently at same time.
        """
        leave_occurrence = raise_no_exception(
            validate_leave_occurrence, leave_account, start_timestamp
        )
        depletion_required = raise_no_exception(
            validate_depletion_required, leave_account
        )
        prior_approval = raise_no_exception(
            require_prior_approval, leave_account, start_timestamp, leave_balance
        )
        require_time_period = raise_no_exception(
            validate_require_time_period, leave_account, start_timestamp, end_timestamp
        )
        require_document = raise_no_exception(
            require_docs, leave_account, attrs.get('attachment'), leave_balance
        )
        continuous_leave = raise_no_exception(
            validate_continuous_leave, leave_account, leave_balance
        )
        limit_limitation = raise_no_exception(
            validate_limit_limitation, leave_account, leave_balance, start_timestamp.date()
        )
        payroll_generation = raise_no_exception(
            raise_validation_if_payroll_is_generated, user, start_timestamp.date()
        )
        validations = [
            leave_occurrence, depletion_required, prior_approval, require_time_period,
            require_document, continuous_leave, limit_limitation, payroll_generation
        ]
        errors = [validation for validation in validations if validation]

        if errors:
            raise ValidationError(errors)

    def on_create_validate(
        self, start_timestamp,
        end_timestamp, user, leave_account, leave_balance, attrs
    ):
        context_validation = self.context.get('bypass_validation')
        bypass_validation = context_validation.lower() if context_validation else None
        mode = self.context.get('mode')

        # checks whether supervisor has approve authority of subordinates
        supervisor_has_authority = subordinates.authority_exists(
            leave_account.user, self.request.user, 'approve'
        )

        """
        if mode == supervisor, skip `validate_can_request_assign` because this function only
        allows `hr` and `employee` to request leave but `supervisor` also needs to apply for
        offline leave of his/her subordinates
        """
        if not mode == 'supervisor':
            leave_utils.validate_can_request_assign(leave_account, self.request.user, mode)

        balance_utils.validate_sufficient_leave_balance(leave_account, leave_balance)

        timedelta = end_timestamp - start_timestamp
        if timedelta.total_seconds() <= 0 and not self.extend_to_next_day(
            user, attrs.get('start')
        ):
            # For night shift (i.e 10pm-6am) start_time is greater than end_time, so bypass this.
            raise ValidationError(
                "Start date must be smaller than end date."
            )
        self._validate_no_old_leaves(
            user,
            start_timestamp,
            end_timestamp
        )
        validate_holiday_inclusive(
            leave_account,
            start_timestamp.date(),
            end_timestamp.date()
        )

        # leave validations are skipped if user is `hr` or `supervisor`.
        if not (
            (mode == 'hr' and bypass_validation == 'true') or
            (mode == 'supervisor' and bypass_validation == 'true' and supervisor_has_authority)
        ):
            self.warn_before_skipping_leave_validations(
                start_timestamp, end_timestamp, leave_account, leave_balance, attrs, user
            )
        validate_require_experience(leave_account)
        validate_minimum_maximum_range(leave_account, leave_balance)
        # Validate if Overtime has been claimed. [HRIS-1641]
        if test_if_overtime_is_claimed(
            user,
            start_timestamp.date(), end_timestamp.date()
        ):
            raise ValidationError(
                "The overtime has been claimed for these days."
            )

    def _combine_start_end(self, validated_data, user):
        if self.request.method != 'POST':
            return validated_data

        # get start and end times for combination
        part = validated_data.get('part_of_day')
        start_date = validated_data.pop('start')
        end_date = validated_data.pop('end', None)

        start_time = validated_data.pop('start_time', None)
        end_time = validated_data.pop('end_time', None)

        if start_time:
            start = combine_aware(start_date, start_time)
        else:
            start = leave_utils.get_shift_start(user, start_date, part)

        if not end_date or part in [FIRST_HALF, SECOND_HALF]:  # Same as start if not given.
            end_date = start.date()
            # In case of extend to next day (night shift) date start.date() may result in addition
            # of 1 day. To resolve this behaviour, assign end_date to actual start_date
            diff = end_date - start_date
            if diff == datetime.timedelta(days=1):
                end_date = start_date

        if end_time:
            end = combine_aware(end_date, end_time)
        else:
            end = leave_utils.get_shift_end(user, end_date, part)

        validated_data.update({
            'start': start,
            'end': end
        })
        return validated_data

    @staticmethod
    def validate_date_and_time(attrs):
        start = attrs.get("start")
        end = attrs.get("end")
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        if start_time and not end_time:
            raise ValidationError({'end_time': 'End Time is required.'})
        if end_time and not start_time:
            raise ValidationError({'start_time': 'Start Time is required.'})
        if start and end and start > end:
            raise ValidationError("Start date must be smaller than end date.")

    def validate(self, attrs):
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.context["organization"]
        )
        self.validate_date_and_time(attrs)
        user = None
        if self.request:
            if self.request.method == 'POST':
                user = attrs.get('user')
                if not user:
                    user = self.request.user
            elif self.request.method in ['PUT', 'PATCH'] and self.instance:
                user = self.instance.user
            if not user:
                raise ValidationError(
                    f"The request could not be processed as user could not be "
                    f"determined."
                )
            validate_has_supervisor(
                status=attrs.get('status') if self.instance else REQUESTED,
                user=user,
                recipient=nested_getattr(self, 'instance.recipient')
            )
            attrs = self._combine_start_end(attrs, user)
            if self.instance:
                # handle this only if instance is passed
                validate_action_permission(
                    leave_request=self.instance,
                    status=attrs.get('status'),
                    actor=getattr(self.request, 'user', None)
                )

            if self.request.method == 'POST':
                start_timestamp = attrs.get('start')
                end_timestamp = attrs.get('end')
                leave_account = attrs.get('leave_account')
                part = attrs.get(
                    'part_of_day',
                    FULL_DAY
                )
                is_half_day = True if part in [
                    FIRST_HALF, SECOND_HALF
                ] else False
                if is_half_day and not (
                    leave_account.master_setting.half_shift_leave
                    and leave_account.rule.can_apply_half_shift
                ):
                    raise ValidationError({
                        'part_of_day': 'Half day leaves is not allowed'
                    })
                balance, steps = balance_utils.get_leave_balance(
                    start_timestamp,
                    end_timestamp,
                    user,
                    leave_account,
                    part
                )

                # create LeaveSheet with these steps
                self.steps = steps
                self.on_create_validate(
                    start_timestamp, end_timestamp,
                    user, leave_account, balance, attrs
                )
                attrs.update({
                    'user': user,
                    'recipient': get_appropriate_recipient(user),
                    'leave_rule': leave_account.rule,
                    'balance': balance
                })
                if is_hourly_account(leave_account):
                    attrs['part_of_day'] = ''
        if self.instance:
            new_status = attrs.get('status')
            if new_status == DENIED:
                # require remarks
                supervisor_remarks = attrs.get('supervisor_remarks')
                if not supervisor_remarks or supervisor_remarks == '':
                    raise ValidationError({
                        'supervisor_remarks': 'Remarks is required.'
                    })
        return attrs

    def validate_status(self, status):
        if self.instance and self.instance.status in [DENIED, APPROVED]:
            raise ValidationError({
                'status': f'The {self.instance.status} requests cannot '
                          f'be modified.'
            })
        if (
            self.instance and self.instance.recipient_type == APPROVER
            and status not in [APPROVED, DENIED]
        ):
            raise ValidationError({
                'status': 'You can approve or deny leave request as an approver.'
            })
        return status

    @staticmethod
    def extend_to_next_day(user, date):
        work_day = user.attendance_setting.work_day_for(date)
        if work_day:
            timing = work_day.timings.first()
            return timing.extends
        return False

    def create(self, validated_data, **kwargs):
        has_approvals = kwargs.get('has_approvals', False)
        instance = super().create(validated_data)
        if not has_approvals:
            self.make_history(instance, validated_data.get('details'))
            self.make_changes_to_balances(instance)
            self.after_create(instance)
        return instance

    def after_create(self, instance):
        # this method because admin has to do other things as well after create
        leave_sheet.create_leave_sheets(instance, steps=self.steps)
        instance.start = instance.start.date()
        instance.end = instance.end.date()
        self.manage_time_sheets_and_overtime(instance)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        supervisor_remarks = validated_data.get('supervisor_remarks')
        if instance.status in [DENIED, APPROVED]:
            self.approve_leave_request(instance)
        elif instance.status == FORWARDED:
            # recipient changed only when forward
            recipient, recipient_type, status = get_leave_request_recipient(instance)
            instance.recipient = recipient
            instance.recipient_type = recipient_type
            instance.save()
        self.make_history(instance, supervisor_remarks)
        self.manage_time_sheets_and_overtime(instance)
        if instance.status == APPROVED:
            leave_approve_post_actions(instance)
        return instance

    def get_fields(self):
        fields = super().get_fields()
        if self.request:
            active_master_settings = MasterSetting.objects.filter(
                organization=self.request.user.detail.organization
            ).active()
            fields.update({
                'leave_account': serializers.PrimaryKeyRelatedField(
                    queryset=LeaveAccount.objects.filter(
                        rule__leave_type__master_setting__in=active_master_settings
                    )
                )
            })
            if self.request.method == 'POST':
                fields['start_time'] = serializers.TimeField(
                    write_only=True, allow_null=True, required=False
                )
                fields['end_time'] = serializers.TimeField(
                    write_only=True, allow_null=True, required=False
                )
                fields['start'] = serializers.DateField()
                fields['end'] = serializers.DateField(
                    allow_null=True, required=False
                )
            if self.request.method == 'PUT':
                [fields.pop(field, None) for field in self.Meta.user_fields]
            if self.request.method == 'POST':
                fields.pop('status', None)
                fields.pop('is_archived', None)
        if self.instance:
            fields['supervisor_remarks'] = serializers.CharField(
                max_length=150,
                write_only=True,
                required=False,
                allow_blank=True,
                allow_null=True
            )
        return fields

    def get_leave_type(self, instance):
        return instance.leave_account.rule.leave_type.name

    def get_leave_type_category(self, instance):
        return instance.leave_account.rule.leave_type.category


class LeaveRequestActionSerializer(LeaveRequestHelper, DummySerializer):
    _APPROVE = 'approve'
    _DENY = 'deny'
    _FORWARD = 'forward'

    _ACTION_CHOICES = (
        (_APPROVE, _APPROVE),
        (_DENY, _DENY),
        (_FORWARD, _FORWARD)
    )

    _ACTION_STATUS_MAP = {
        _APPROVE: APPROVED,
        _DENY: DENIED,
        _FORWARD: FORWARDED
    }

    action = serializers.ChoiceField(choices=_ACTION_CHOICES, write_only=True)
    remark = serializers.CharField(max_length=255, write_only=True)

    @property
    def mode(self):
        return self.context['view'].mode

    @property
    def request(self):
        return self.context['request']

    def get_fields(self):
        fields = super().get_fields()
        fields['leave_request'] = serializers.PrimaryKeyRelatedField(
            queryset=self.context.get('leave_requests'),
            write_only=True
        )
        return fields

    def validate(self, attrs):
        leave_request = attrs['leave_request']
        action = attrs['action']

        if leave_request.status not in [REQUESTED, FORWARDED]:
            raise serializers.ValidationError(
                _("Can not act on already acted leave request.")
            )

        if self.mode == 'hr' and action == self._FORWARD:
            raise serializers.ValidationError({
                'action': _("HR can not forward leave request.")
            })

        elif self.mode == 'supervisor':
            if not leave_request.recipient == self.request.user:
                # FAIL SAFE
                raise serializers.ValidationError(
                    _("You are not the right recipient for this request.")
                )

            if not subordinates.authority_exists(
                leave_request.user, leave_request.recipient, action
            ):
                raise serializers.ValidationError({
                    'action': _(f"You can not {action} this request.")
                })

            if action == self._FORWARD:
                user = leave_request.user
                recipient = leave_request.recipient
                current_level = leave_utils.get_authority(
                    user, recipient
                ) or 0
                forwarded_to = leave_utils.get_appropriate_recipient(user, current_level + 1)
                if not forwarded_to:
                    raise serializers.ValidationError({
                        'action': _(f"Next recipient not found to forward this request.")
                    })
        return attrs

    def create(self, validated_data):
        instance = validated_data['leave_request']
        action = validated_data['action']
        supervisor_remarks = validated_data['remark']

        instance.status = self._ACTION_STATUS_MAP[action]
        instance.save()

        if instance.status in [DENIED, APPROVED]:
            # self.make_changes_to_balances(instance)
            # send_leave_notification(instance)
            self.approve_leave_request(instance)
        elif instance.status == FORWARDED:
            # recipient changed only when forward
            recipient, recipient_type, status = leave_utils.get_leave_request_recipient(instance)
            instance.recipient = recipient
            instance.recipient_type = recipient_type
            instance.save()

        self.make_history(instance, supervisor_remarks)
        self.manage_time_sheets_and_overtime(instance)
        if instance.status == APPROVED:
            leave_approve_post_actions(instance)
        return instance


class LeaveRequestHistorySerializer(DynamicFieldsModelSerializer):
    request = LeaveRequestSerializer(fields=(
        'user', 'leave_account', 'start', 'end'
    ))
    actor = UserThinSerializer(
        read_only=True,
        exclude_fields=['email']
    )
    forwarded_to = UserThinSerializer(
        read_only=True,
        exclude_fields=['email']
    )

    class Meta:
        model = LeaveRequestHistory
        fields = (
            'request', 'action', 'remarks', 'actor', 'forwarded_to', 'created_at', 'recipient_type'
        )
        read_only_fields = 'created_at', 'recipient_type',


class LeaveRequestDeleteStatusHistorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LeaveRequestDeleteStatusHistory
        fields = (
            'status', 'remarks'
        )


class LeaveRequestDeleteHistorySerializer(DynamicFieldsModelSerializer):
    leave_request = LeaveRequestSerializer(
        read_only=True,
        exclude_fields=['user', 'created_by']
    )
    created_by = UserThinSerializer(read_only=True)
    acted_remarks = serializers.SerializerMethodField()
    status_history = LeaveRequestDeleteStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = LeaveRequestDeleteHistory
        fields = (
            'leave_request', 'status', 'remarks', 'created_at',
            'created_by', 'id', 'acted_remarks', 'status_history'
        )
        read_only_fields = ('created_by', 'leave_request', 'id')

    def get_fields(self):
        fields = super().get_fields()
        if not self.instance:
            # remove the status while being created
            fields.pop('status', None)
        return fields

    def validate(self, attrs):
        leave_request = self.context.get('leave_request')
        validate = not self.request.query_params.get("bypass_validation")
        if self.request and self.request.method.upper() == 'DELETE' and validate:
            self.on_create_validate(leave_request)

        self.validate_no_renewal_performed(leave_request)
        attrs.update({
            'leave_request': leave_request
        })
        qs = leave_request.delete_history.exclude(
            status=DENIED,
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        pending = qs.first()
        if pending:
            raise ValidationError({
                'detail': 'A cancel request already exists for this leave in '
                          f'{pending.get_status_display()} state.'
            })
        return super().validate(attrs)

    @transaction.atomic()
    def update(self, instance, validated_data):
        status_remark = validated_data.pop('remarks', '')
        ret = super().update(instance, validated_data)
        if ret.status == APPROVED:
            revert_leave_for_date(ret)
        LeaveRequestDeleteStatusHistory.objects.create(
            delete_history=ret,
            status=ret.status,
            remarks=status_remark
        )
        return ret

    @transaction.atomic()
    def create(self, validated_data):
        ret = super().create(validated_data)
        if self.context.get('mode') == 'hr':
            ret.status = APPROVED
            ret.created_by = ret.leave_request.user
            ret.save()
            revert_leave_for_date(ret)
        LeaveRequestDeleteStatusHistory.objects.create(
            delete_history=ret,
            status=ret.status,
            remarks=ret.remarks
        )
        return ret

    @staticmethod
    def get_acted_remarks(instance):
        return getattr(instance.status_history.filter(
            status__in=[APPROVED, DENIED, FORWARDED]
        ).first(), 'remarks', None)

    @staticmethod
    def on_create_validate(leave_request):
        # Condition1: The leave request must not have payroll generated.
        fn, installed = get_dependency(
            'irhrs.payroll.utils.helpers.get_last_payroll_generated_date_excluding_simulated'
        )
        if installed:
            dt = fn(leave_request.user)
            if dt and dt > leave_request.start.date():
                raise ValidationError(
                    f"The payroll for {leave_request.user} has been "
                    f"generated upto {dt}. "
                    f"Cancellation of leave before {dt} is not permitted."
                )
        # condition2: The leave account should not have its master setting
        # expired.
        if leave_request.user.timesheets.filter(
            timesheet_for__in=leave_request.sheets.values_list(
                'leave_for', flat=True
            ),
            overtime__claim__status__in=[REQUESTED, FORWARDED, APPROVED, CONFIRMED]
        ).only('pk').exists():
            raise ValidationError(
                "Please make sure all the overtime created during this leave "
                "is either unclaimed or denied."
            )
        if leave_request.leave_account.master_setting.status == EXPIRED:
            raise ValidationError(
                f"The master setting for this leave request has been expired."
            )

    @staticmethod
    def validate_no_renewal_performed(leave_request):
        # condition3: The leave account should not have been renewed after
        # the requested date
        rule = nested_getattr(
            leave_request.leave_account,
            'rule.renewal_rule'
        )
        if rule and leave_request.leave_account.history.filter(
            created_at__gte=leave_request.created_at,
            renewed__isnull=False,
        ):
            raise ValidationError(
                f"The leave request before the leave renewal cannot be canceled."
            )


class AdminLeaveRequestSerializer(LeaveRequestSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    # filter user to `user__organization = self.context.get('organization')`

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs.get('user')

        leave_account = attrs.get('leave_account')
        if (user and leave_account) and (leave_account.user != user):
            raise ValidationError("The user has no such leave balance")
        if self.request:
            attrs.update({
                'created_by': self.request.user
            })
        return attrs

    def get_fields(self):
        fields = super().get_fields()
        fields.update({
            'leave_account': serializers.PrimaryKeyRelatedField(
                queryset=LeaveAccount.objects.filter(
                    user__detail__organization=self.context.get('organization')
                ).select_related(
                    'user',
                    'rule',
                    'rule__leave_type',
                )
                # Select relating the fields is only for `?format=api`
                # where the form displays these fields and over-queries.
            )
        })
        return fields

    def create(self, validated_data, **kwargs):
        leave_rule = validated_data.get('leave_rule')
        validated_data.update({
            'status': APPROVED
        })
        has_approvals = check_multi_level_approval(leave_rule)
        instance = super().create(validated_data, has_approvals=has_approvals)
        mode = self.context.get('mode')
        if has_approvals:
            recipient, recipient_type, status = get_leave_request_recipient(instance)
            instance.recipient = recipient
            instance.recipient_type = recipient_type
            instance.status = status
            instance.save()
            self.make_history(instance, validated_data.get('details'))
            self.make_changes_to_balances(instance, has_approvals)
            self.after_create(instance)
        else:
            # because at post request, the field has been updated to date fields,
            # and having the start/end dates
            instance.start = instance.start.date()
            instance.end = instance.end.date()

        if instance.status == APPROVED:
            setattr(instance, 'prevent_default', self.context.get('prevent_default'))
            leave_approve_post_actions(instance)
            immediate_supervisors_qs = instance.user.user_supervisors
            immediate_supervisors = [
                supervisor.supervisor for supervisor in immediate_supervisors_qs
            ]
            text = f"{self.request.user} has {instance.status.lower()} {instance.user}'s " \
                   f"leave from {instance.start} to {instance.end}"

            if mode == 'hr':
                recipients = immediate_supervisors

            if mode == 'supervisor':
                user_supervisors = UserSupervisor.objects.filter(user=instance.user)
                supervisors = [user_supervisor.supervisor for user_supervisor in user_supervisors]

                # need to send notification to supervisor below the authority_level of
                # current supervisor
                index = supervisors.index(self.request.user) + 1
                recipients = supervisors[index:]
                notify_organization(
                    text=text,
                    url=f"/admin/{self.context.get('organization').slug}/leave/employees-request",
                    action=instance,
                    permissions=[
                        LEAVE_PERMISSION, LEAVE_REQUEST_PERMISSION, OFFLINE_LEAVE_PERMISSION
                    ],
                    organization=self.context.get('organization'),
                )

            if mode in ['hr', 'supervisor']:
                add_notification(
                    text=text,
                    actor=self.request.user,
                    action=instance,
                    recipient=recipients,
                    url=f"/user/supervisor/leave/overview"
                )
        return instance


class UserLeaveRequestStatisticsSerializer(LeaveRequestSerializer):
    pass


class LeaveSheetSerializer(DynamicFieldsModelSerializer):
    part_of_day = serializers.SerializerMethodField()
    leave_type = serializers.ReadOnlyField(
        source='request.leave_rule.leave_type.name'
    )

    class Meta:
        model = LeaveSheet
        fields = (
            'part_of_day', 'leave_type', 'start', 'end'
        )

    @staticmethod
    def get_part_of_day(leave_sheet):
        return choice_field_display(leave_sheet.request, 'part_of_day')


class LeaveRequestImportSerializer(serializers.Serializer):
    user = serializers.CharField(max_length=255)
    part_of_day = serializers.ChoiceField(
        choices=HALF_LEAVE_CHOICES
    )
    description = serializers.CharField(max_length=255)

    def get_fields(self):
        fields = super().get_fields()
        fields['leave_category'] = serializers.SlugRelatedField(
            queryset=self.context['leave_type_queryset'],
            # This works because has been filtered through Master Setting.
            slug_field='name'
        )
        return fields

    def validate(self, attrs):
        return self.generate_payload_for_admin_leave_request(attrs)

    def create(self, validated_data):
        instance = AdminLeaveRequestSerializer(
            context=self.context
        ).create(
            validated_data
        )
        return instance

    def update(self, instance, validated_data):
        pass

    def parse_date_fields(self):
        result = dict()
        errors = dict()
        for date_field in ('start_date', 'end_date'):
            is_pass, value = self.validate_date(self.initial_data.get(date_field))
            if is_pass:
                # validate_past_date(value)
                result[date_field] = value
            else:
                errors[date_field] = value
        if errors:
            raise ValidationError(errors)
        return result

    @staticmethod
    def validate_date(date):
        if isinstance(date, datetime.datetime):
            return True, date.date()
        elif isinstance(date, datetime.date):
            return True, date
        elif isinstance(date, str):
            try:
                date_ = parse(date)
                return True, date_.date()
            except (TypeError, ValueError):
                pass
        format_name = type(date)
        return False, f"Invalid Date Format. {format_name}"

    def generate_payload_for_admin_leave_request(self, attrs):
        """
        Format for AdminLeaveRequestSerializer.
        user: 329
        # Got this
        leave_account: 1813
        # Parse this from Leave Type
        details: asdfasdf
        # Got this in description
        part_of_day: full
        # Got this
        start: 2020-03-09
        # Got This
        end: 2020-03-09
        # Got This
        start_time: 18:50
        # Not Needed.
        end_time: 18:50
        # Not Needed.
        """
        # we receive start date and end date from there.
        attrs.update(self.parse_date_fields())
        user = attrs.get('user')
        user = (User.objects.filter(Q(username=user) | Q(email=user)).first()).id
        payload = {
            'user': user,
            'leave_account': self.get_leave_account_id(
                attrs.get('user'), attrs.get('leave_category')
            ),
            'details': attrs.get('description'),
            'start': attrs.get('start_date').isoformat(),
            'end': attrs.get('end_date').isoformat(),
            'part_of_day': attrs.get('part_of_day')
        }
        serializer = AdminLeaveRequestSerializer(
            data=payload,
            context=self.context
        )
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    @staticmethod
    def get_leave_account_id(user, leave_type):
        user = (User.objects.filter(Q(username=user) | Q(email=user)).first()).id
        leave_account = LeaveAccount.objects.filter(
            user=user,
            rule__leave_type=leave_type
        ).filter(
            is_archived=False
        ).first()
        if not leave_account:
            raise ValidationError({
                'leave_type': 'There is no leave account associated for this leave type.'
            })
        return leave_account.id


class LeaveRequestAlternateAccountsSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    part_of_day = serializers.ChoiceField(choices=HALF_LEAVE_CHOICES)
    details = serializers.CharField(max_length=600)
    attachment = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST)
        ],
        required=False,
        allow_null=True
    )
    extra_kwargs = {
        'attachment': {
            'required': False,
            'allow_null': True
        }
    }

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request:
            fields.update({
                'leave_accounts': serializers.PrimaryKeyRelatedField(
                    queryset=LeaveAccount.objects.all(),
                    many=True
                )
            })
        return fields

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('start_date')

        if end_date > start_date:
            raise ValidationError({
                "error": "End date cannot be greater than start date."
            })
        return super().validate(attrs)

    @transaction.atomic()
    def create(self, validated_data):
        """Deducts leave balance from multiple leave accounts.

        Takes a leave request and a list of leave accounts.
        Then, iterates through the leave accounts and deducts
        balance until the leave request is satisfied or start
        deducting from next leave account.

        If the balance is still not enough after deducting
        from all the leave accounts, raises ValidationError
        and rolls back the transaction.
        """
        request = self.context.get('request')
        mode = self.context.get('mode')
        initial_start_date = validated_data.get('start_date')
        initial_end_date = validated_data.get('end_date')
        total_leave_requested = (
            initial_end_date - initial_start_date
        ).days
        leave_accounts = validated_data.get('leave_accounts')
        attachment = validated_data.get('attachment')
        remarks = validated_data.get('details')
        part_of_day = validated_data.get('part_of_day')
        user = request.user
        if leave_accounts:
            user = leave_accounts[0].user
        data = dict(
            user=user.id,
            part_of_day=part_of_day,
            start=initial_start_date,
            end=initial_end_date,
            details=remarks,
            attachment=attachment
        )
        for count, leave_acc in enumerate(leave_accounts):
            data.update({
                "leave_account": leave_acc.id
            })
            leave_days = (data.get('end') - data.get('start')).days
            if leave_acc.usable_balance > leave_days:
                # if leave account has enough balance,
                # deduct from this leave account(as usual) and stop.
                balance_to_deduct = total_leave_requested
                user_ser = LeaveRequestSerializer(data=data, context=self.context)
                admin_ser = AdminLeaveRequestSerializer(data=data, context=self.context)
                ser = user_ser if mode == "user" else admin_ser
                ser.is_valid(raise_exception=True)
                ser.save()
                break
            else:
                balance_to_deduct = leave_acc.usable_balance
                # if leave account does not have enough balance
                # for the original LeaveRequest, modify the
                # start and end dates of LeaveRequest so
                # that it can be fulfilled by this leave account
                end = data.get('start') + datetime.timedelta(days=balance_to_deduct - 1)
                data.update({
                    "end": initial_end_date if count == (len(leave_accounts) - 1) else end
                })
                user_ser = LeaveRequestSerializer(data=data, context=self.context)
                admin_ser = AdminLeaveRequestSerializer(data=data, context=self.context)
                ser = user_ser if mode == "user" else admin_ser
                ser.is_valid(raise_exception=True)
                ser.save()

                new_start_date = data.get('start') + datetime.timedelta(days=balance_to_deduct)
                data.update({
                    "start": new_start_date,
                    "end": initial_end_date
                })

        return {}
