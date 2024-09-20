from datetime import timedelta

from django.db.models import Sum, F, DurationField
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.attendance.api.v1.serializers.overtime import OvertimeSettingSerializer
from irhrs.attendance.constants import REQUESTED, DECLINED, APPROVED, CANCELLED, WORKDAY, HOLIDAY, OFFDAY
from irhrs.attendance.managers.timesheet import TimeSheetManager
from irhrs.attendance.models import OvertimeSetting
from irhrs.attendance.models.credit_hours import CreditHourRequest, CreditHourRequestHistory, CreditHourSetting, \
    CreditHourDeleteRequest, CreditHourDeleteRequestHistory
from irhrs.attendance.tasks.credit_hours import recalibrate_credit_when_pre_approval_is_modified, \
    is_pre_approved_credit_hour_editable, revert_credit_hour_from_leave_account
from irhrs.attendance.utils.attendance import humanize_interval, get_week
from irhrs.attendance.utils.credit_hours import is_credit_hours_editable, get_credit_leave_account_for_user, \
    leave_account_exceeds_max_limit, deletable_credit_request
from irhrs.attendance.utils.helpers import get_pre_approval_recipient
from irhrs.attendance.utils.validators import validate_shift_exists
from irhrs.core.constants.organization import CREDIT_HOUR_REQUEST_ON_BEHALF
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import get_patch_attr, nested_getattr
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.core.validators import validate_prior_approval_requests, validate_past_date
from irhrs.leave.models.account import LeaveAccount
from irhrs.organization.models import FiscalYear, get_user_model
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer


class CreditHourSettingSerializer(DynamicFieldsModelSerializer):
    editable = serializers.BooleanField(read_only=True)
    overtime_setting = serializers.SlugRelatedField(
        queryset=OvertimeSetting.objects.all(),
        slug_field='slug',
        allow_null=True,
    )

    class Meta:
        model = CreditHourSetting
        fields = (
            'organization',
            'name',
            'slug',
            'minimum_credit_request',
            'daily_credit_hour_limit_applicable',
            'daily_credit_hour_limit',
            'weekly_credit_hour_limit_applicable',
            'weekly_credit_hour_limit',
            'monthly_credit_hour_limit_applicable',
            'monthly_credit_hour_limit',
            'off_day_credit_hour',
            'off_day_credit_hour_limit',
            'holiday_credit_hour',
            'holiday_credit_hour_limit',
            'credit_hour_calculation',
            'is_archived',
            'deduct_credit_hour_after_for',
            'flat_reject_value',
            'credit_hour_expires',
            'expires_after',
            'expires_after_unit',
            'require_prior_approval',
            'grant_overtime_for_exceeded_minutes',
            'overtime_setting',
            'reduce_credit_if_actual_credit_lt_approved_credit',
            'allow_edit_of_pre_approved_credit_hour',
            'editable',
            # 'allow_delete'
        )
        read_only_fields = 'organization', 'slug'

    def create(self, validated_data):
        validated_data['organization'] = self.context['organization']
        return super().create(validated_data)

    def validate(self, attrs):
        self.validate_pairs(attrs)
        return super().validate(attrs)

    def validate_pairs(self, attrs):
        errors = dict()

        def get_attrib_from_model(attrib):
            return get_patch_attr(attrib, attrs, self)

        for flag, is_set in (
            ('daily_credit_hour_limit_applicable', 'daily_credit_hour_limit'),
            ('weekly_credit_hour_limit_applicable', 'weekly_credit_hour_limit'),
            ('monthly_credit_hour_limit_applicable', 'monthly_credit_hour_limit'),
            ('off_day_credit_hour', 'off_day_credit_hour_limit'),
            ('holiday_credit_hour', 'holiday_credit_hour_limit'),
        ):
            if get_attrib_from_model(flag) and not get_attrib_from_model(is_set):
                # Flag was set, Value was not
                errors[is_set] = '{} needs to be set.'.format(is_set)
            elif not get_attrib_from_model(flag) and get_attrib_from_model(is_set):
                # Flag was not set, value was
                errors[is_set] = '{} can not be set.'.format(is_set)
        if errors:
            raise ValidationError(errors)

    def get_fields(self):
        fields = super().get_fields()
        if 'overtime_setting' in fields:
            overtime_qs = OvertimeSetting.objects.all()
            if self.context.get('organization'):
                overtime_qs = overtime_qs.filter(
                    organization=self.context.get('organization')
                )
            fields['overtime_setting'] = serializers.SlugRelatedField(
                queryset=overtime_qs,
                slug_field='slug',
                allow_null=True
            )
        if self.request and self.request.method == 'GET':
            if 'overtime_setting' in fields:
                fields['overtime_setting'] = OvertimeSettingSerializer(
                    fields=['name', 'slug']
                )
            for f in [
                'daily_credit_hour_limit',
                'weekly_credit_hour_limit',
                'monthly_credit_hour_limit',
                'off_day_credit_hour_limit',
                'holiday_credit_hour_limit',
            ]:
                if f in fields:
                    fields[f] = serializers.SerializerMethodField()
        return fields

    @staticmethod
    def get_minutes_to_json(minutes):
        if not minutes:
            return {
                'hours': None,
                'minutes': None
            }
        min_ = int(minutes)
        hh, mm = divmod(min_, 60)
        return {
            'hours': hh,
            'minutes': mm
        }

    def get_daily_credit_hour_limit(self, instance):
        return self.get_minutes_to_json(instance.daily_credit_hour_limit)

    def get_weekly_credit_hour_limit(self, instance):
        return self.get_minutes_to_json(instance.weekly_credit_hour_limit)

    def get_monthly_credit_hour_limit(self, instance):
        return self.get_minutes_to_json(instance.monthly_credit_hour_limit)

    def get_off_day_credit_hour_limit(self, instance):
        return self.get_minutes_to_json(instance.off_day_credit_hour_limit)

    def get_holiday_credit_hour_limit(self, instance):
        return self.get_minutes_to_json(instance.holiday_credit_hour_limit)


class CreditHourRequestHistorySerializer(DynamicFieldsModelSerializer):
    action_performed_by = UserThinSerializer()

    class Meta:
        model = CreditHourRequestHistory
        fields = (
            'created_at',
            'action_performed',
            'remarks',
            'action_performed_by',
        )


class CreditHourRequestSerializer(DynamicFieldsModelSerializer):
    remarks = serializers.CharField(
        write_only=True,
        max_length=255
    )
    editable = serializers.SerializerMethodField()

    class Meta:
        model = CreditHourRequest
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
            'credit_hour_duration',
            'credit_hour_date',
            'credit_hour_status'
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
                fields['histories'] = CreditHourRequestHistorySerializer(
                    many=True,
                    source='_histories'
                )
        return fields

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
        recalibrate_credit_when_pre_approval_is_modified(instance)
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
        elif self.context.get('status') == APPROVED:
            # This check was done before create.
            self.validate_credit_hour_request_limit({
                'credit_hour_date': self.instance.credit_hour_date,
                'credit_hour_duration': self.instance.credit_hour_duration
            })
        return super().validate(attrs)

    def on_create_validate(self, attrs):
        if not nested_getattr(
                self.credit_hour_user,
                'attendance_setting.credit_hour_setting.require_prior_approval'
        ):
            raise ValidationError(
                "Pre Approval Credit Hour Setting has not been assigned."
            )
        first_level_supervisor = self.credit_hour_user.first_level_supervisor
        if not first_level_supervisor:
            raise ValidationError(
                "Could not perform request as supervisor has not been assigned."
            )
        credit_hour_date = attrs.get('credit_hour_date')
        validate_shift_exists(self.credit_hour_user, credit_hour_date)
        self.validate_credit_hour_request_limit(attrs)
        existing = CreditHourRequest.objects.filter(
            sender=self.credit_hour_user,
            credit_hour_date=credit_hour_date
        ).exclude(
            is_deleted=True
        ).exclude(
            status__in=[DECLINED, CANCELLED]
        ).first()
        if existing:
            delete_request = existing.delete_requests.first()
            credit_hour_delete_status = delete_request.status if delete_request else None
            if credit_hour_delete_status != APPROVED:
                raise ValidationError({
                    'credit_hour_date': 'A Pre Approval Credit Hour for this date already exists '
                                        f'in {existing.get_status_display()} state.'
                })
        if self._as == 'hr':
            validate_past_date(credit_hour_date)
            return
        validate_prior_approval_requests(credit_hour_date)

    @property
    def _as(self):
        return self.request.query_params.get('as')

    def validate_credit_hour_request_limit(self, attrs):
        sender = self.get_sender()
        duration = attrs.get('credit_hour_duration')
        date = attrs.get('credit_hour_date')
        self.payload = attrs
        credit_setting = sender.attendance_setting.credit_hour_setting
        if not credit_setting:
            raise ValidationError(
                'Could not perform request as no credit hour setting is assigned.'
            )
        minimum_duration = credit_setting.minimum_credit_request
        if duration < minimum_duration:
            raise ValidationError({
                'credit_hour_duration': f'You can not request less than '
                                        f'{humanize_interval(minimum_duration)}.'
                                        f'Requested: {humanize_interval(duration)}'
            })
        # Test for Holiday/Off-day.
        coefficient = TimeSheetManager.get_coefficient(sender, date)
        flag_value_map = {
            WORKDAY: ('daily_credit_hour_limit_applicable', 'daily_credit_hour_limit'),
            HOLIDAY: ('holiday_credit_hour', 'holiday_credit_hour_limit'),
            OFFDAY: ('off_day_credit_hour', 'off_day_credit_hour_limit',),
        }
        flag, limit = flag_value_map.get(coefficient)
        if getattr(credit_setting, flag):
            self.validate_daily_limit(
                duration,
                getattr(credit_setting, limit)
            )
        if credit_setting.weekly_credit_hour_limit_applicable:
            self.validate_weekly_limit(
                duration, credit_setting.weekly_credit_hour_limit, sender, date
            )
        if credit_setting.monthly_credit_hour_limit_applicable:
            self.validate_monthly_limit(
                duration, credit_setting.monthly_credit_hour_limit, sender, date
            )
        self.validate_max_balance_in_leave_account(sender, duration)

    def get_sender(self):
        if self.instance:
            sender = self.instance.sender
        else:
            sender = self.credit_hour_user
        return sender

    def raise_validation_error_with_suggestion(self, error_dict):
        sender = self.get_sender()
        if getattr(
                sender.attendance_setting.overtime_setting,
                'require_prior_approval',
                None
        ):
            redirect = {
                'redirect': True,
                'payload': self.generate_payload_for_overtime()
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

    def generate_payload_for_overtime(self):
        mapping = {
            ('overtime_date', 'credit_hour_date',),
            ('overtime_duration', 'credit_hour_duration',),
            ('remarks', 'remarks',),
        }
        return {
            field: self.payload.get(mapped_value)
            for field, mapped_value in mapping
        }

    def validate_weekly_limit(self, duration, limit, sender, date):
        """
        Validate weekly limit as cumulative Pre OT requests (except Declined/Cancelled).
        """
        duration_limit = timedelta(minutes=limit)
        test_start, test_end = self.get_dates_for_week(date)
        existing_sum = self.get_pre_approval_sum(sender, test_end, test_start)
        if (duration + existing_sum) > duration_limit:
            self.raise_validation_error_with_suggestion({
                'credit_hour_duration': f'The weekly limit for Overtime is '
                                        f'{humanize_interval(duration_limit)}. '
                                        f'Existing: {humanize_interval(existing_sum)} '
                                        f'Requested: {humanize_interval(duration)}'
            })

    def validate_monthly_limit(self, duration, limit, sender, date):
        """
        Validate monthly limit as cumulative Pre OT requests (except Declined/Cancelled).
        """
        duration_limit = timedelta(minutes=limit)
        test_start, test_end = self.get_fiscal_month_for_date(date, sender.detail.organization)
        existing_sum = self.get_pre_approval_sum(sender, test_end, test_start)
        if (duration + existing_sum) > duration_limit:
            self.raise_validation_error_with_suggestion({
                'credit_hour_duration': f'The monthly limit for Credit Hour is '
                                        f'{humanize_interval(duration_limit)}.'
                                        f'Existing: {humanize_interval(existing_sum)}. '
                                        f'Requested: {humanize_interval(duration)}'
            })

    def get_pre_approval_sum(self, sender, test_end, test_start):
        base = CreditHourRequest.objects.filter(
            sender=sender,
            credit_hour_date__range=(test_start, test_end)
        ).exclude(
            status__in=[DECLINED, CANCELLED]
        ).exclude(
            is_deleted=True
        )
        if self.instance:
            base = base.exclude(id=self.instance.pk)
        existing_sum = base.annotate(
            earned_duration=Coalesce(
                F('credit_entry__earned_credit_hours'),
                F('credit_hour_duration'),
                output_field=DurationField()
            )
        ).aggregate(
            sum_of_requests=Sum('earned_duration')
        ).get('sum_of_requests')
        if not existing_sum:
            existing_sum = timedelta(0)
        return existing_sum

    def validate_max_balance_in_leave_account(self, sender, duration):
        base = CreditHourRequest.objects.filter(
            sender=sender,
        ).exclude(
            status__in=[DECLINED, CANCELLED]
        ).exclude(
            is_deleted=True
        ).filter(
            # Declined cancelled has to be ignored.
            # TODO @Ravi: Also, need is_deleted, which is in another branch
            # Approved but not yet processed is identified with following logic.
            credit_entry__isnull=True
        )
        if self.instance:
            base = base.exclude(id=self.instance.pk)
        existing_sum = base.aggregate(
            sum_of_requests=Sum('credit_hour_duration')
        ).get('sum_of_requests')
        if not existing_sum:
            existing_sum = timedelta(0)
        leave_account = get_credit_leave_account_for_user(sender)
        if not leave_account:
            # No validation or validate user needs to have a leave account?
            # raise ValidationError("User does not have a valid Credit Leave Account")
            return
        if leave_account_exceeds_max_limit(leave_account, duration, existing_sum):
            self.raise_validation_error_with_suggestion({
                'credit_hour_duration':
                    'The selected duration {} exceeds max balance {}. Existing: {}. Pending {}'.format(
                        humanize_interval(duration),
                        humanize_interval(leave_account.rule.max_balance * 60),
                        humanize_interval(leave_account.usable_balance * 60),
                        humanize_interval(existing_sum)
                    )
            })

    @property
    def credit_hour_user(self):
        return self.context.get('sender')

    @property
    def request_sent_by(self):
        return self.get_sender()

    @staticmethod
    def maintain_history(instance, status, sender, recipient, remarks):
        CreditHourRequestHistory.objects.create(
            credit_hour=instance,
            action_performed=status,
            remarks=remarks,
            action_performed_by=sender,
            action_performed_to=recipient,
        )

    def validate_daily_limit(self, duration, limit):
        """
        Validate duration does not exceed limit for daily case.
        """
        duration_limit = timedelta(minutes=limit)
        if duration > duration_limit:
            self.raise_validation_error_with_suggestion({
                'credit_hour_duration': f'The daily credit hour limit for the day is '
                                        f'{humanize_interval(duration_limit)}. '
                                        f'Requested: {humanize_interval(duration)}'
            })

    @staticmethod
    def get_fiscal_month_for_date(date, organization):
        """
        Returns month to consider before testing for monthly credit_hour limits.
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

    @staticmethod
    def get_editable(instance):
        return is_credit_hours_editable(instance)


class CreditHourRequestEditSerializer(CreditHourRequestSerializer):
    remarks = serializers.CharField(
        write_only=True,
        max_length=255
    )

    class Meta:
        model = CreditHourRequest
        fields = (
            'remarks',
            'credit_hour_duration',
        )

    def validate(self, attrs):
        attrs['credit_hour_date'] = self.instance.credit_hour_date
        if not is_credit_hours_editable(self.instance):
            raise ValidationError("Edit of credit hour is not enabled.")
        editable, remark = is_pre_approved_credit_hour_editable(self.instance, attrs['credit_hour_duration'])
        if not editable:
            raise ValidationError(
                f"Could not edit Credit Hour because {remark}."
            )
        super().validate_credit_hour_request_limit(attrs)
        return attrs

    def update(self, instance, validated_data):
        validated_data.update({
            'request_remarks': validated_data.pop('remarks', None),
            'status': REQUESTED,
            'sender': self.credit_hour_user,
            'recipient': get_pre_approval_recipient(user=self.credit_hour_user)
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
        # we might be recalibrating leave right here.
        # recalibrate_overtime_claim_when_pre_approval_is_modified(instance)
        return instance


class CreditHourRequestOnBehalfSerializer(serializers.Serializer):

    def get_fields(self):
        fields = super().get_fields()
        fields['user_id'] = serializers.PrimaryKeyRelatedField(
            queryset=self.credit_hour_user_queryset,
            write_only=True
        )
        self.context['sender'] = self.credit_hour_user
        fields['requests'] = CreditHourRequestSerializer(write_only=True, many=True)
        return fields

    def validate_user(self, user):
        if not self.credit_hour_user:
            raise ValidationError("The user does not exist.")

    def create(self, validated_data):
        """
        * For simplicity, we are reducing remarks as only writable params.
        * It gets converted to request_remarks at the time of request and action_remarks
        otherwise.
        * Recipient is taken from util.
        * At requested state, the status will always be `Requested`.
        If request-on-behalf is implemented, make it `Approved`.
        """
        requests = validated_data.pop('requests')
        credit_hour_request_list = list()
        for req in requests:
            remarks = req.pop('remarks', None)
            req.update({
                'action_remarks': remarks,
                'request_remarks': remarks,
                'status': APPROVED,
                'sender': self.credit_hour_user,
                'recipient': get_pre_approval_recipient(
                    user=self.credit_hour_user,
                    status=APPROVED,
                    old_recipient=self.credit_hour_user.first_level_supervisor
                )
            })
            credit_hour_request_list.append(CreditHourRequest(**req))
        created = CreditHourRequest.objects.bulk_create(credit_hour_request_list)
        for instance in created:
            CreditHourRequestSerializer.maintain_history(
                instance,
                instance.status,
                self.context['request'].user,
                instance.recipient,
                instance.request_remarks
            )

            send_email_as_per_settings(
                recipients=[self.credit_hour_user, instance.created_by],
                subject="Credit hour request on behalf",
                email_text=(
                    f"{instance.created_by} has request and approved {self.credit_hour_user}'s"
                    f" credit hour for {instance.credit_hour_date}."
                ),
                email_type=CREDIT_HOUR_REQUEST_ON_BEHALF
            )

        return created

    @property
    def credit_hour_user(self):
        credit_hour_user_id = self.context.get('credit_hour_user_id')
        return self.credit_hour_user_queryset.filter(id=credit_hour_user_id).first()

    @cached_property
    def credit_hour_user_queryset(self):
        qs = get_user_model().objects.filter().current().filter(
            detail__organization=self.context.get('organization')
        )
        return qs


class CreditHourDeleteRequestHistorySerializer(DynamicFieldsModelSerializer):
    action_performed_by = UserThinSerializer()

    class Meta:
        model = CreditHourDeleteRequestHistory
        fields = (
            'action_performed',
            'remarks',
            'action_performed_by',
            'action_performed_to',
        )


class CreditHourDeleteRequestSerializer(DynamicFieldsModelSerializer):
    remarks = serializers.CharField(
        write_only=True,
        max_length=255
    )

    class Meta:
        model = CreditHourDeleteRequest
        fields = (
            'id',
            'sender',
            'recipient',
            'request_remarks',
            'action_remarks',
            'status',
            'request',
            'remarks',
            'created_at',
            'modified_at'
        )
        read_only_fields = (
            'sender',
            'recipient',
            'request_remarks',
            'action_remarks',
            'status',
            'request',
        )

    def create(self, validated_data):
        delete_instance = self.context.get('credit_request')
        sender = delete_instance.sender
        validated_data.update({
            'request_remarks': validated_data.pop('remarks', None),
            'status': REQUESTED,
            'sender': sender,
            'recipient': get_pre_approval_recipient(user=sender),
            'request': delete_instance
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

    def update(self, instance, validated_data):
        old_recipient = instance.recipient
        validated_data['recipient'] = get_pre_approval_recipient(
            user=instance.sender,
            status=self.context['status'],
            old_recipient=old_recipient
        )
        validated_data['status'] = self.context['status']
        validated_data['action_remarks'] = validated_data.pop('remarks', None)
        instance = super().update(instance, validated_data)
        if self.context['status'] == APPROVED:
            revert_credit_hour_from_leave_account(instance)
        self.maintain_history(
            instance=instance,
            status=instance.status,
            sender=self.request.user,
            recipient=instance.recipient,
            remarks=instance.action_remarks
        )
        return instance

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['sender'] = UserThinSerializer()
            fields['recipient'] = UserThinSerializer()
            fields['request'] = CreditHourRequestSerializer()
            if self.context.get('show_delete_history'):
                fields['histories'] = CreditHourDeleteRequestHistorySerializer(
                    many=True,
                    source='_histories'
                )
        return fields

    def validate(self, attrs):
        if self.request.method == 'POST':
            self.on_create_validate(attrs)
        elif self.request.method in ('PUT', 'PATCH'):
            self.validate_can_be_deleted(
                self.instance.request
            )
        return attrs

    def on_create_validate(self, data):
        self.validate_can_be_deleted(self.context.get('credit_request'))
        return data

    @staticmethod
    def validate_can_be_deleted(request):
        deletable = deletable_credit_request(request)
        if not deletable:
            raise ValidationError(
                "Can not delete this credit request as leave balance has been consumed."
            )

    @staticmethod
    def maintain_history(instance, status, sender, recipient, remarks):
        CreditHourDeleteRequestHistory.objects.create(
            delete_request=instance,
            action_performed=status,
            remarks=remarks,
            action_performed_by=sender,
            action_performed_to=recipient,
        )

class CreditHourBulkRequestSerializer(serializers.Serializer):
    requests = CreditHourRequestSerializer(many=True, write_only=True)

    def validate(self, attrs):
        requests = attrs.get('requests')
        sender = self.context['sender']
        total_duration = 0
        for req in requests:
            credit_hour_duration = req.get('credit_hour_duration')
            total_duration += credit_hour_duration.total_seconds()
        base_qs = CreditHourRequest.objects.filter(sender=sender, credit_entry__isnull=True).exclude(
            status__in=[DECLINED, CANCELLED]
        ).exclude(is_deleted=True)
        if self.instance:
            base_qs = base_qs.exclude(id=self.instance.pk)
        requested_sum = base_qs.aggregate(
            sum_of_requests=Sum('credit_hour_duration')
        ).get('sum_of_requests')
        if not requested_sum:
            requested_sum = timedelta(0)
        leave_account = get_credit_leave_account_for_user(sender)
        if not leave_account:
            raise ValidationError(
                "User does not have a valid Credit Leave Account"
            )
        usable_balance = getattr(leave_account, 'usable_balance')
        limit = nested_getattr(leave_account, 'rule.max_balance')
        total_credit_hour_duration = (
            (requested_sum.total_seconds())/60 + (total_duration/60) +
            usable_balance
        )
        if total_credit_hour_duration > limit:
            raise ValidationError(
                'The selected duration {} exceeds max balance {}. Existing: {}. Pending {}'.format(
                    humanize_interval(total_duration),
                    humanize_interval(leave_account.rule.max_balance * 60),
                    humanize_interval(leave_account.usable_balance * 60),
                    humanize_interval(requested_sum)
                )
            )
        return attrs

    def create(self, validated_data):
        requests = validated_data.get('requests')
        remarks_list = [req.pop('remarks') for req in requests]
        for req in requests:
            req.update({
                'sender': self.context.get('sender'),
                'recipient': get_pre_approval_recipient(user=self.context.get('sender'))
            })
        credit_hours = [
            CreditHourRequest(**req) for req in requests
        ]
        created = CreditHourRequest.objects.bulk_create(credit_hours)
        for remarks, instance in zip(remarks_list, created):
             CreditHourRequestSerializer.maintain_history(
                instance,
                instance.status,
                instance.sender,
                instance.recipient,
                remarks
            )
        return created
