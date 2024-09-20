from datetime import timedelta

from django.conf import settings
from django.db.models import Sum, OuterRef, Subquery, F
from django.db.models.functions import Coalesce
from django.forms import DurationField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import REQUESTED, DECLINED, APPROVED, CANCELLED, CONFIRMED, WORKDAY, HOLIDAY, OFFDAY
from irhrs.attendance.managers.timesheet import TimeSheetManager
from irhrs.attendance.models import OvertimeEntry
from irhrs.attendance.models.pre_approval import PreApprovalOvertime, PreApprovalOvertimeHistory
from irhrs.attendance.tasks.pre_approval import recalibrate_overtime_claim_when_pre_approval_is_modified, \
    is_pre_approved_overtime_editable
from irhrs.attendance.utils.attendance import humanize_interval, get_week
from irhrs.attendance.utils.helpers import get_pre_approval_recipient
from irhrs.attendance.utils.overtime_utils import get_pre_approval_overtime_sum
from irhrs.attendance.utils.validators import validate_shift_exists
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.core.validators import validate_prior_approval_requests
from irhrs.organization.models import FiscalYear
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
REQUIRE_CONFIRM = getattr(settings, 'REQUIRE_PRE_APPROVAL_CONFIRMATION', False)


class PreApprovalOvertimeHistorySerializer(DynamicFieldsModelSerializer):
    action_performed_by = UserThinSerializer()
    action_performed_to = UserThinSerializer()

    class Meta:
        model = PreApprovalOvertimeHistory
        fields = (
            'created_at',
            'action_performed',
            'remarks',
            'action_performed_by',
            'action_performed_to',
        )


class PreApprovalOvertimeSerializer(DynamicFieldsModelSerializer):
    remarks = serializers.CharField(
        write_only=True,
        max_length=255
    )
    editable = serializers.SerializerMethodField()

    class Meta:
        model = PreApprovalOvertime
        read_only_fields = (
            'id',
            'created_at',
            'modified_at',
            'sender',
            'recipient',
            'status',
            'request_remarks',
            'action_remarks',
            'editable'
        )
        fields = read_only_fields + (
            'remarks',
            'overtime_duration',
            'overtime_date'
        )

    def create(self, validated_data):
        """
        * For simplicity, we are reducing remarks as only writable params.
        * It gets converted to request_remarks at the time of request and action_remarks
        otherwise.
        * Recipient is taken from util.
        * At requested state, the status will always be `Requested`.
        If request-on-behalf is implemented, make it `Approved`.
        """
        validated_data.update({
            'request_remarks': validated_data.pop('remarks', None),
            'status': REQUESTED,
            'sender': self.context.get('sender'),
            'recipient': get_pre_approval_recipient(user=self.context.get('sender'))
        })
        instance = super().create(validated_data)
        self.maintain_history(
            instance,
            instance.status,
            instance.sender,
            instance.recipient,
            instance.request_remarks
        )
        return instance

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['sender'] = UserThinSerializer()
            fields['recipient'] = UserThinSerializer()
            if self.context.get('show_history'):
                fields['histories'] = PreApprovalOvertimeHistorySerializer(
                    many=True,
                    source='_histories'
                )
        return fields

    @staticmethod
    def maintain_history(instance, status, sender, recipient, remarks):
        PreApprovalOvertimeHistory.objects.create(
            pre_approval=instance,
            action_performed=status,
            remarks=remarks,
            action_performed_by=sender,
            action_performed_to=recipient,
        )

    def update(self, instance, validated_data):
        old_recipient = instance.recipient
        validated_data['recipient'] = get_pre_approval_recipient(
            user=instance.sender,
            status=self.context['status'],
            old_recipient=old_recipient
        )
        validated_data['status'] = self.context['status']
        validated_data['action_remarks'] = self.context.get('remarks')
        instance = super().update(instance, validated_data)
        self.maintain_history(
            instance=instance,
            status=instance.status,
            sender=self.request.user,
            recipient=instance.recipient,
            remarks=instance.action_remarks
        )
        return instance

    def validate(self, attrs):
        if self.request.method == 'POST' and not self.context.get('action'):
            self.on_create_validate(attrs)
        elif self.context.get('status') == (CONFIRMED if REQUIRE_CONFIRM else APPROVED):
            # This check was done before create.
            self.validate_overtime_request_limit({
                'overtime_date': self.instance.overtime_date,
                'overtime_duration': self.instance.overtime_duration
            })
        return super().validate(attrs)

    def on_create_validate(self, attrs):
        if not self.context.get('allow_request'):
            raise ValidationError(
                "Pre Approval Overtime Setting has not been assigned."
            )
        overtime_date = attrs.get('overtime_date')
        first_level_supervisor = self.context.get('sender').first_level_supervisor_including_bot
        if not first_level_supervisor:
            raise ValidationError(
                "Could not perform request as supervisor has not been assigned."
            )
        validate_shift_exists(self.context.get('sender'), overtime_date)
        self.validate_overtime_request_limit(attrs)
        existing = PreApprovalOvertime.objects.filter(
            sender=self.context.get('sender'),
            overtime_date=overtime_date
        ).exclude(
            status__in=(DECLINED, CANCELLED)
        ).first()
        if existing:
            raise ValidationError({
                'overtime_date': 'A Pre Approval Overtime for this date already exists '
                                 f'in {existing.get_status_display()} state.'
            })
        validate_prior_approval_requests(overtime_date)

    def validate_overtime_request_limit(self, attrs):
        sender = self.get_sender()
        duration = attrs.get('overtime_duration')
        date = attrs.get('overtime_date')
        self.payload = attrs
        ot_setting = sender.attendance_setting.overtime_setting
        if not ot_setting:
            raise ValidationError(
                'Could not perform request as no overtime setting is assigned.'
            )
        self.validate_minimum_request_limit(ot_setting, duration)

        coefficient = TimeSheetManager.get_coefficient(sender, date)
        flag_value_map = {
            WORKDAY: ('daily_overtime_limit_applicable', 'daily_overtime_limit'),
            OFFDAY: ('off_day_overtime', 'off_day_overtime_limit'),
            HOLIDAY: ('paid_holiday_affect_overtime', 'holiday_overtime_limit'),
        }
        flag, limit = flag_value_map.get(coefficient)
        if getattr(ot_setting, flag):
            self.validate_daily_limit(
                duration,
                getattr(ot_setting, limit)
            )
        if ot_setting.weekly_overtime_limit_applicable:
            self.validate_weekly_limit(
                duration, ot_setting.weekly_overtime_limit, sender, date
            )
        if ot_setting.monthly_overtime_limit_applicable:
            self.validate_monthly_limit(
                duration, ot_setting.monthly_overtime_limit, sender, date
            )

    def get_sender(self):
        if self.instance:
            sender = self.instance.sender
        else:
            sender = self.context.get('sender')
        return sender

    def raise_validation_error_with_suggestion(self, error_dict):
        sender = self.get_sender()
        if getattr(
                sender.attendance_setting.credit_hour_setting,
                'require_prior_approval',
                None
        ):
            redirect = {
                'redirect': True,
                'payload': self.generate_payload_for_credit_hour()
            }
        else:
            redirect = {
                'redirect': False,
                'payload': {}
            }
        raise ValidationError({
            **error_dict,
            'redirect': redirect
        })

    def generate_payload_for_credit_hour(self):
        mapping = {
            ('credit_hour_date', 'overtime_date',),
            ('credit_hour_duration', 'overtime_duration',),
            ('remarks', 'remarks',),
        }
        return {
            field: self.payload.get(mapped_value)
            for field, mapped_value in mapping
        }

    def validate_minimum_request_limit(self, setting, duration):
        can_not_request_less_than = setting.minimum_request_duration
        if can_not_request_less_than and duration < can_not_request_less_than:
            raise ValidationError({
                'overtime_duration': f'Can not request less than {humanize_interval(can_not_request_less_than)}. '
                                     f'Requested: {humanize_interval(duration)}'
            })

    def validate_daily_limit(self, duration, limit):
        """
        Validate duration does not exceed limit for daily case.
        """
        duration_limit = timedelta(minutes=limit)
        if duration > duration_limit:
            self.raise_validation_error_with_suggestion({
                'overtime_duration': f'The daily limit for Overtime is '
                                     f'{humanize_interval(duration_limit)}. '
                                     f'Requested: {humanize_interval(duration)}'
            })

    @property
    def get_mode(self):
        return self.request.query_params.get('as')

    def validate_weekly_limit(self, duration, limit, sender, date):
        """
        Validate weekly limit as cumulative Pre OT requests (except Declined/Cancelled).
        """
        duration_limit = timedelta(minutes=limit)
        test_start, test_end = self.get_dates_for_week(date)
        existing_sum = get_pre_approval_overtime_sum(sender, test_end, test_start)

        if self.get_mode not in ['hr', 'supervisor'] and (duration + existing_sum) > duration_limit:
            self.raise_validation_error_with_suggestion(
                self.get_weekly_validation_message(duration_limit, existing_sum, duration)
            )

        if self.get_mode in ['hr', 'supervisor'] and not existing_sum <= duration_limit:
            self.raise_validation_error_with_suggestion(
                self.get_weekly_validation_message(duration_limit, existing_sum, duration)
            )

    def validate_monthly_limit(self, duration, limit, sender, date):
        """
        Validate monthly limit as cumulative Pre OT requests (except Declined/Cancelled).
        """
        duration_limit = timedelta(minutes=limit)
        test_start, test_end = self.get_fiscal_month_for_date(date, sender.detail.organization)
        existing_sum = get_pre_approval_overtime_sum(sender, test_end, test_start)

        if self.get_mode not in ['hr', 'supervisor'] and (duration + existing_sum) > duration_limit:
            self.raise_validation_error_with_suggestion(
                self.get_monthly_validation_message(duration_limit, existing_sum, duration)
            )

        if self.get_mode in ['hr', 'supervisor'] and not existing_sum <= duration_limit:
            self.raise_validation_error_with_suggestion(
                self.get_monthly_validation_message(duration_limit, existing_sum, duration)
            )

    @staticmethod
    def get_weekly_validation_message(duration_limit, existing_sum, duration):
        return {
            'overtime_duration': f'The weekly limit for Overtime is '
                                 f'{humanize_interval(duration_limit)}. '
                                 f'Existing : {humanize_interval(existing_sum)}. '
                                 f'Requested : {humanize_interval(duration)}'
        }

    @staticmethod
    def get_monthly_validation_message(duration_limit, existing_sum, duration):
        return {
            'overtime_duration': f'The monthly limit for Overtime is '
                                 f'{humanize_interval(duration_limit)}. '
                                 f'Existing : {humanize_interval(existing_sum)}. '
                                 f'Requested : {humanize_interval(duration)}'
        }

    @staticmethod
    def get_fiscal_month_for_date(date, organization):
        """
        Returns month to consider before testing for monthly overtime limits.
        Eg: Pre Approval for Shrawan 5th shall consider (Shrawan 1, Shrawan 30)
        Because FY for org and FY for Attendance can be different, handled through here.
        :param date: Date for which Pre OT was requested.
        :param organization: Organization to extract FY.
        :returns: appropriate month (start, end)
        """
        fy = FiscalYear.objects.current(organization=organization)
        if fy:
            fm = fy.fiscal_months.filter(
                start_at__lte=date,
                end_at__gte=date,
            ).order_by(
                'start_at'
            ).values_list('start_at', 'end_at')
            if fm:
                return fm[0]
        raise ValidationError(
            "Fiscal Year is not defined."
        )

    @staticmethod
    def get_dates_for_week(date):
        """
        Returns week start/end to consider for Weekly OT limit.
        Eg: Pre Approval for Wednesday shall consider dates between adjacent Sunday, Saturday.
        If there's a setting for organization's week definition: MON-SUN or SAT-SUN, do make changes here.
        :param date: Date for which Pre OT was requested.
        :returns: appropriate week (start, end)
        TODO @Ravi: Take start of week, from env.constants
        """
        return get_week(date)

    def get_editable(self, instance):
        return is_pre_approved_overtime_editable(instance)


class PreApprovalOvertimeEditSerializer(PreApprovalOvertimeSerializer):
    remarks = serializers.CharField(
        write_only=True,
        max_length=255
    )

    class Meta:
        model = PreApprovalOvertime
        fields = (
            'remarks',
            'overtime_duration',
        )

    def validate(self, attrs):
        attrs['overtime_date'] = self.instance.overtime_date
        pre_approval_setting = self.instance.sender.attendance_setting.overtime_setting
        if not pre_approval_setting:
            raise ValidationError(
                "Overtime Setting was not found."
            )
        if not is_pre_approved_overtime_editable(self.instance):
            raise ValidationError(
                "Confirmed Pre Approval can not be edited."
            )
        if not pre_approval_setting.allow_edit_of_pre_approved_overtime:
            raise ValidationError("Edit has been disabled.")
        super().validate_overtime_request_limit(attrs)
        return attrs

    def update(self, instance, validated_data):
        validated_data.update({
            'request_remarks': validated_data.pop('remarks', None),
            'status': REQUESTED,
            'sender': self.context.get('sender'),
            'recipient': get_pre_approval_recipient(user=self.context.get('sender'))
        })
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self.maintain_history(
            instance,
            instance.status,
            instance.sender,
            instance.recipient,
            instance.request_remarks
        )
        # Delete Generated Overtime Claim (in approved State).
        overtime_entry = getattr(instance, 'overtime_entry', None)
        if overtime_entry:
            overtime_entry.delete()
        return instance
