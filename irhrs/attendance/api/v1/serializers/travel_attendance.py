import itertools

from datetime import time
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.db.models import Q
from django_q.tasks import async_task
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from irhrs.attendance.api.v1.serializers.credit_hours import CreditHourRequestSerializer, \
    CreditHourDeleteRequestSerializer
from irhrs.attendance.constants import REQUESTED, APPROVED, DECLINED, CANCELLED, FORWARDED, \
    FULL_DAY, TRAVEL_ATTENDANCE, UNCLAIMED
from irhrs.attendance.models import TravelAttendanceSetting, IndividualUserShift, TimeSheet, \
    OvertimeClaim, TimeSheetEntry, CreditHourRequest
from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest, \
    TravelAttendanceRequestHistory, TravelAttendanceDays, TravelAttendanceAttachments, \
    TravelAttendanceDeleteRequest, TravelAttendanceDeleteRequestHistory
from irhrs.attendance.utils.attendance import get_week
from irhrs.attendance.utils.helpers import get_authority, get_pre_approval_recipient
from irhrs.attendance.utils.shift_planner import get_shift_details
from irhrs.attendance.utils.travel_attendance import calculate_balance, \
    create_travel_attendance_for_past_dates
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import get_patch_attr, nested_getattr
from irhrs.core.utils.common import combine_aware, extract_documents, get_today
from irhrs.leave.utils.leave_request import get_appropriate_recipient
from irhrs.leave.utils.timesheet import empty_timesheets
from irhrs.organization.api.v1.serializers.common_org_serializer import OrganizationSerializerMixin
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import User


class TravelAttendanceSettingSerializer(OrganizationSerializerMixin, DynamicFieldsModelSerializer):
    class Meta:
        model = TravelAttendanceSetting
        fields = (
            'can_apply_in_offday', 'can_apply_in_holiday'
        )


class TravelAttendanceAttachmentsSerializer(DynamicFieldsModelSerializer):
    attachment = serializers.FileField(
        validators=[FileExtensionValidator(
            allowed_extensions=settings.ACCEPTED_FILE_FORMATS_LIST
        )],
        source='file',
        write_only=True
    )

    class Meta:
        # TODO @Ravi: Merge file and attachment as one. This is done to have no rework in FE.
        model = TravelAttendanceAttachments
        fields = 'file', 'attachment', 'filename',
        read_only_fields = 'file',


class TravelAttendanceRequestHistorySerializer(DynamicFieldsModelSerializer):
    # created_by = UserThumbnailSerializer(read_only=True)
    log = serializers.SerializerMethodField()

    class Meta:
        model = TravelAttendanceRequestHistory
        fields = (
            'status', 'remarks', 'created_at', 'log'
            # 'created_by',
        )

    @staticmethod
    def get_log(instance):
        if instance.status == CANCELLED:
            return f"{instance.created_by} has cancelled this travel request."
        return "{} has {} with remarks {}".format(
            instance.created_by.full_name,
            instance.status.lower(),
            instance.remarks
        )


class TravelAttendanceDaysSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TravelAttendanceDays
        fields = (
            'day', 'is_archived', 'id'
        )


class TravelAttendanceDeleteRequestHistorySerializer(DynamicFieldsModelSerializer):
    log = serializers.SerializerMethodField()
    created_by = UserThinSerializer()
    status = serializers.ReadOnlyField(source='action_performed')

    class Meta:
        model = TravelAttendanceDeleteRequestHistory
        fields = (
            'created_at', 'created_by', 'log', 'status'
        )

    @staticmethod
    def get_log(instance):
        if instance.action_performed == CANCELLED:
            return f"{instance.created_by} has cancelled this delete request."
        return "{} has {} with remarks {}".format(
            instance.created_by.full_name,
            instance.action_performed.lower(),
            instance.remarks
        )


# TODO @ravi: Move to util.
def revert_travel_attendance(travel_attendance_delete_request_id):
    travel_attendance_delete_request = TravelAttendanceDeleteRequest.objects.get(
        pk=travel_attendance_delete_request_id
    )
    # TODO @Ravi: Async this, and make sure the worker does not timeout.
    # Do not take more than 10/15 requests at once.
    if travel_attendance_delete_request.status != APPROVED:
        return
    deleted_days = travel_attendance_delete_request.deleted_days.all()
    user = travel_attendance_delete_request.travel_attendance.user
    for deleted_day in deleted_days:
        raw_entries = list(
            TimeSheetEntry.objects.filter(
                timesheet__in=set(deleted_day.timesheets.only('pk').order_by())
            ).order_by().values_list(
                'timestamp', 'entry_method'
            ).distinct()
        )
        empty_timesheets(
            deleted_day.timesheets.filter(timesheet_for=deleted_day.day)
        )
        for timestamp, entry_method in raw_entries:
            if (not timestamp) or (entry_method == TRAVEL_ATTENDANCE):
                continue
            TimeSheet.objects.clock(
                user,
                timestamp,
                entry_method
            )
        deleted_day.is_archived = True
        deleted_day.save()
        equivalent_credit_request = travel_attendance_delete_request.travel_attendance.credit_hour_requests.filter(
            credit_hour_date=deleted_day.day
        ).first()
        if equivalent_credit_request:
            TravelAttendanceRequestSerializer.cancel_single_credit_request(
                credit_request=equivalent_credit_request,
                remarks=travel_attendance_delete_request.request_remarks
            )
    return


def create_travel_attendance(instance_id):
    instance = TravelAttendanceRequest.objects.get(pk=instance_id)
    user = instance.user
    attendance_setting = user.attendance_setting
    travel_setting = user.detail.organization.travel_setting
    offday_applicable = travel_setting.can_apply_in_offday
    holiday_applicable = travel_setting.can_apply_in_holiday
    dates = list()
    for date in rrule(freq=DAILY, dtstart=instance.start, until=instance.end):
        # check for holiday,
        # if no holiday check for workday
        # if no workday (i.e. workday) check for if settings count off-days too.
        if user.is_holiday(date):
            if holiday_applicable:
                dates.append(date)
            continue
        wd = attendance_setting.work_day_for(date)
        if wd:
            dates.append(date)
        elif offday_applicable:
            dates.append(date)
    breakdown_travel_attendance(instance, dates)
    if instance.start <= get_today():
        create_travel_attendance_for_past_dates(instance)


def breakdown_travel_attendance(travel_attendance, dates):
    # Here we will break travel attendance start and end to per-day basis.
    TravelAttendanceDays.objects.bulk_create([
        TravelAttendanceDays(
            user=travel_attendance.user,
            day=date,
            travel_attendance=travel_attendance
        ) for date in dates
    ])


def cancel_credit_requests(instance):
    all_credit_requests = instance.credit_hour_requests.filter()
    for credit_request in all_credit_requests:
        TravelAttendanceRequestSerializer.cancel_single_credit_request(
            credit_request, remarks=instance.action_remarks
        )


class TravelAttendanceDeleteRequestSerializer(DynamicFieldsModelSerializer):
    recipient = UserThinSerializer(read_only=True)
    histories = TravelAttendanceDeleteRequestHistorySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = TravelAttendanceDeleteRequest
        fields = (
            'travel_attendance', 'recipient', 'request_remarks', 'action_remarks', 'status',
            'deleted_days', 'id', 'histories', 'created_at'
        )
        read_only_fields = 'status',

    def get_fields(self):
        fields = super().get_fields()
        if self.request:
            if self.request.method == 'GET':
                fields['deleted_days'] = TravelAttendanceDaysSerializer(many=True)
                fields['travel_attendance'] = TravelAttendanceRequestSerializer()
            elif self.request.method == 'POST':
                fields.pop('action_remarks', None)
            elif self.request.method in ['PUT', 'PATCH']:
                fields.pop('request_remarks', None)
        return fields

    @staticmethod
    def on_create_validate(data):
        # No Longer need to validate existence. [User can send multiple requests at once]
        recipient = data['travel_attendance'].user.first_level_supervisor_including_bot
        if not recipient:
            raise ValidationError(
                "There is no supervisor assigned for this user."
            )
        # Check if there is already deleted days for this.
        if set(
            data['travel_attendance'].delete_request.exclude(
                status__in=[CANCELLED, DECLINED]
            ).values_list('deleted_days', flat=True)
        ).intersection(
            set(
                map(
                    lambda d: d.id,
                    data['deleted_days']
                )
            )
        ):
            raise ValidationError({
                'deleted_days': 'Could not request for some of the days.'
            })
        data['recipient'] = recipient
        return data

    def create(self, validated_data):
        validated_data['status'] = REQUESTED
        instance = super().create(validated_data)
        self.create_history(instance)
        return instance

    def validate(self, data):
        if self.request:
            if self.request.method == 'POST':
                data = self.on_create_validate(data)
            if self.context.get('status') and self.request.method in ['PUT', 'PATCH']:
                if not data.get('action_remarks'):
                    raise ValidationError({
                        'action_remarks': 'The remarks may not be empty.'
                    })
        # If there is status, its action, else, its update.
        if self.instance and not self.context.get('status') and self.instance.status != REQUESTED:
            raise ValidationError(
                f"Can not update requests once they are {self.instance.status.lower()}"
            )
        travel_attendance = get_patch_attr(
            attribute='travel_attendance',
            validated_data=data,
            serializer=self
        )
        # From the list we got, we make sure, no previously deleted days are included.
        deleted_days = get_patch_attr(
            'deleted_days',
            data,
            self
        )
        if not isinstance(deleted_days, list):
            deleted_days = deleted_days.all()
        # Test if all the dates have already been deleted, and there are no new dates to delete.
        if deleted_days:
            if any(map(lambda dx: dx.is_archived, deleted_days)):
                raise ValidationError(
                    'There are days that have already been deleted.'
                )
            if set(map(
                lambda deleted_day: deleted_day.travel_attendance, deleted_days
            )) - {travel_attendance}:
                raise ValidationError({
                    'deleted_days': 'There are days that does not belong to the '
                                    'specified travel request'
                })
            if OvertimeClaim.objects.exclude(status=UNCLAIMED).filter(
                overtime_entry__user=travel_attendance.user,
                overtime_entry__timesheet__timesheet_for__in=map(
                    lambda deleted_day: deleted_day.day, deleted_days
                )
            ).exists():
                raise ValidationError({
                    'deleted_days': "One or more selection of deleted day's overtime has "
                                    "been claimed. Can not request to delete travel attendance."
                })
        return super().validate(data)

    def validate_travel_attendance(self, travel_attendance):
        if travel_attendance.user != self.request.user:
            raise ValidationError(
                'There is no such travel attendance.'
            )
        if travel_attendance.status != APPROVED:
            raise ValidationError(
                f'{travel_attendance.status} travel requests can not be deleted.'
            )
        return travel_attendance

    def update(self, instance, validated_data):
        status = self.context.get('status')
        if status:
            validated_data['status'] = status
            validated_data['recipient'] = self.context.get('recipient')
        obj = super().update(instance, validated_data)
        if status:
            async_task(
                revert_travel_attendance,
                instance.id
            )
            self.create_history(instance)
        return obj

    @staticmethod
    def create_history(instance):
        instance.history.create(
            action_performed=instance.status,
            action_performed_to=instance.recipient,
            remarks=(
                instance.request_remarks
                if instance.status == REQUESTED else instance.action_remarks
            )
        )

    @staticmethod
    def find_recipient(user, current_recipient, status):
        return {
            APPROVED: current_recipient,
            DECLINED: current_recipient,
            CANCELLED: current_recipient,
            FORWARDED: getattr(
                get_appropriate_recipient(
                    user=user,
                    level=(get_authority(user, current_recipient) or -1) + 1
                ),
                'supervisor',
                current_recipient
            )
        }.get(status)


class TravelAttendanceRequestSerializer(DynamicFieldsModelSerializer):
    days = TravelAttendanceDaysSerializer(
        many=True,
        read_only=True,
        source='travel_attendances'
    )
    user = UserThinSerializer(read_only=True)
    recipient = UserThinSerializer(read_only=True)
    attachments = TravelAttendanceAttachmentsSerializer(
        many=True,
        read_only=True,
    )
    histories = TravelAttendanceRequestHistorySerializer(
        many=True, read_only=True,
        source='history_logs'
    )
    has_shift = serializers.SerializerMethodField()
    deleted_days = serializers.SerializerMethodField()
    action_remarks = serializers.CharField(
        max_length=255, required=False,
        allow_null=True, allow_blank=True
    )

    class Meta:
        model = TravelAttendanceRequest
        fields = (
            'user', 'status', 'request_remarks', 'action_remarks', 'location', 'days',
            'start', 'start_time', 'end', 'end_time', 'id', 'balance', 'created_at',
            'recipient', 'attachments', 'histories', 'working_time', 'has_shift',
            'deleted_days'
        )
        read_only_fields = 'balance', 'status', 'start_time', 'end_time'

    def create(self, validated_data):
        # For mode = 'supervisor' and 'hr', we will use validated_data
        # passed from TravelAttendanceOnBehalfSerializer
        mode = self.request.query_params.get('as')
        if mode not in ['supervisor', 'hr']:
            user = self.context['user']
            validated_data['user'] = user
            validated_data['status'] = REQUESTED
            validated_data['recipient'] = self.request.user.first_level_supervisor
        attachments = validated_data.pop('attachments', None)
        with transaction.atomic():
            instance = super().create(validated_data)
            self.create_history(instance, instance.status, instance.request_remarks)
            self.add_attachments(instance, attachments)
        if mode in ['supervisor', 'hr'] and instance.status == APPROVED:
            async_task(
                create_travel_attendance,
                instance.id
            )
        return instance

    @staticmethod
    def add_attachments(instance, attachments):
        TravelAttendanceAttachments.objects.bulk_create([
            TravelAttendanceAttachments(
                travel_request=instance,
                file=attachment.get('attachment'),
                filename=attachment.get('filename')
            ) for attachment in attachments
        ])

    def update(self, instance, validated_data):
        validated_data['recipient'] = self.context['recipient']
        validated_data['status'] = self.context['status']
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            self.create_history(instance, instance.status, instance.action_remarks)
        if instance.status == APPROVED:
            async_task(
                create_travel_attendance,
                instance.id
            )
        elif instance.status in [CANCELLED, DECLINED]:
            async_task(
                cancel_credit_requests,
                instance
            )
        return instance

    @staticmethod
    def cancel_single_credit_request(credit_request, remarks):
        # If the credit request has already been declined/cancelled or deleted, ignore.
        if credit_request.status in (DECLINED, CANCELLED) or credit_request.is_deleted:
            return
        # If there is a delete request in progress for this, ignore.
        if credit_request.delete_requests.exclude(
            status__in=[CANCELLED, DECLINED, APPROVED]
        ).exists():
            return

        def sub_cancel(cred):
            # No Matter What, Cancel this.
            cred.status = CANCELLED
            cred.action_remarks = remarks
            cred.save()
            CreditHourRequestSerializer.maintain_history(
                instance=cred,
                status=CANCELLED,
                sender=cred.sender,
                recipient=cred.sender,
                remarks=remarks
            )

        if credit_request.credit_hour_date > get_today():
            sub_cancel(credit_request)
        # Send Delete Request for Past ones.
        else:
            if credit_request.status == APPROVED:
                # we will create a credit hour delete request for past ones.
                CreditHourDeleteRequestSerializer(
                    context={
                        'credit_request': credit_request
                    }
                ).create(
                    validated_data={
                        'remarks': remarks
                    }
                )
            else:
                sub_cancel(credit_request)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'POST':
            fields['start'] = serializers.DateField(write_only=True)
            fields['end'] = serializers.DateField(write_only=True)
            fields['start_time'] = serializers.TimeField(write_only=True, required=False, allow_null=True)
            fields['end_time'] = serializers.TimeField(write_only=True, required=False, allow_null=True)
            fields.pop('action_remarks', None)
        else:
            for f in [
                'request_remarks', 'start', 'end', 'start_time', 'end_time', 'working_time'
            ]:
                fields[f].read_only = True
        return fields

    def on_create_validate(self, attrs):
        user = attrs.get('employee') or self.request.user
        if not user.first_level_supervisor_including_bot:
            raise ValidationError({
                'non_field_errors': [
                    'There is no first level supervisor for this user.'
                ]
            })
        start_timestamp = combine_aware(
            attrs.get('start'),
            attrs.get('start_time')
        )
        end_timestamp = combine_aware(
            attrs.get('end'),
            attrs.get('end_time')
        )
        # Validate the date order is correct
        if start_timestamp > end_timestamp:
            raise ValidationError(
                'Start must be smaller than end date.'
            )
        # Validate there are no other TravelRequests on that range
        if self.request.query_params.get('as') not in ['supervisor', 'hr']:
            user = self.context['user']
        else:
            # employee is a user whose record is being processed by either supervisor or hr
            user = attrs.get('employee')
        conflicting = TravelAttendanceRequest.objects.filter(
            user=user
        ).exclude(
            status__in=[CANCELLED, DECLINED]
        ).filter(
            Q(
                start__gte=start_timestamp,
                start__lte=end_timestamp
            )
            | Q(
                end__gte=start_timestamp,
                end__lte=end_timestamp
            ) | Q(
                start__lte=start_timestamp,
                end__gte=end_timestamp
            )
        ).first()
        if conflicting and not conflicting.delete_request.filter(status=APPROVED).exists():
            raise ValidationError(
                f'There is a {conflicting.get_status_display()} travel request on this range.'
            )

    def validate(self, attrs):
        if not self.context.get('travel_setting'):
            raise ValidationError(
                'There is no travel setting for this organization.'
            )
        user = attrs.get("employee") or self.context['user']
        if self.request:
            if self.request.method == 'POST':
                start, end = attrs.pop('start', None), attrs.pop('end', None)
                attrs.update(
                    self.append_timestamp(
                        start=start, end=end,
                        part=attrs.get('working_time', FULL_DAY),
                        start_time=attrs.get('start_time'),
                        end_time=attrs.get('end_time'),
                        employee=user
                    )
                )
                attrs['balance'] = calculate_balance(
                    user,
                    start,
                    end,
                    self.context.get('travel_setting'),
                    part=attrs.get('working_time', FULL_DAY)
                )
                self.on_create_validate(attrs)
                attrs['attachments'] = extract_documents(
                    self.initial_data,
                    file_field='attachment',
                    filename_field='filename'
                )
                attachment_ser = TravelAttendanceAttachmentsSerializer(
                    data=attrs['attachments'],
                    many=True
                )
                attachment_ser.is_valid(raise_exception=True)
            elif self.instance:
                curr_status = self.instance.status
                if curr_status in [APPROVED, DECLINED, CANCELLED]:
                    raise ValidationError({
                        'status': f'Further actions on {curr_status} travel request is restricted.'
                    })
                has_cancelled = self.context['status'] == CANCELLED
                if not attrs.get('action_remarks') and not has_cancelled:
                    raise ValidationError({
                        'action_remarks': 'Remarks is required to perform this action.'
                    })
        if user and user.first_level_supervisor_including_bot:
            attrs['recipient_id'] = user.first_level_supervisor_including_bot.id
        return super().validate(attrs)

    def append_timestamp(self, **kwargs):
        start = kwargs.get('start')
        end = kwargs.get('end')
        user = kwargs["employee"]
        # First, we check the coefficients for Start and End date.
        # Holiday takes priority, so we test if start or end is holiday.
        # If there is no holiday, we test if the day is offday or not.
        # If the start or end is offday, we mandate start or end time.
        # For days that are weekends, or off-days, we take start/end time from
        # the default time. (if provided)
        travel_setting = self.context.get('travel_setting')
        offday_applicable = travel_setting.can_apply_in_offday
        holiday_applicable = travel_setting.can_apply_in_holiday
        is_start_holiday = user.is_holiday(start)
        is_end_holiday = user.is_holiday(end) and holiday_applicable

        errors = dict()
        if is_start_holiday and not holiday_applicable:
            errors['start'] = 'The start must be a day with shift.'
        if is_end_holiday and not holiday_applicable:
            errors['end'] = 'The start is holiday and travel requests for holiday is not allowed.'

        if errors:
            raise ValidationError(errors)

        # Check to see if the user has a past shift
        shift_exists_for_end, shift_exists_for_start = get_shift_details(user, end, start)
        shiftless_employee = not (shift_exists_for_start and shift_exists_for_end)
        if shiftless_employee:
            raise serializers.ValidationError(
                "There is no shift for this user."
            )

        workday_start = user.attendance_setting.work_day_for(start)
        workday_end = user.attendance_setting.work_day_for(end)

        # If there is no timing, and no offday; raise
        if not workday_start and not offday_applicable:
            errors.update({
                'start': 'The start of travel attendance must be a day with shift.'
            })
        if not workday_end and not offday_applicable:
            errors.update({
                'end': 'The end is off-day and travel requests for off-day is not allowed.'
            })
        if errors:
            raise ValidationError(errors)

        if not workday_start:
            timing_start = kwargs.get('start_time')
            timing_end = kwargs.get('end_time')
            if not timing_start:
                errors.update({
                    'start_time': 'The start time is required.'
                })
                errors['require_timings'] = True
            if not timing_end:
                errors.update({
                    'end_time': 'The end time is required.'
                })
                errors['require_timings'] = True
            if errors:
                raise ValidationError(errors)
        else:
            timing_start = workday_start.timings.order_by('start_time').values_list(
                'start_time', flat=True
            ).first()
            timing_end = workday_start.timings.order_by('-end_time').values_list(
                'end_time', flat=True
            ).first()

        return {
            'start': start,
            'start_time': timing_start,
            'end': end,
            'end_time': timing_end,
        }

    @staticmethod
    def create_history(instance, status, remarks):
        instance.histories.create(
            status=status,
            action_performed_to=instance.recipient,
            remarks=remarks
        )

    @staticmethod
    def get_has_shift(instance):
        base_qs = IndividualUserShift.objects.filter(
            individual_setting__user=instance.user,
        )
        shift_exists_for_start = base_qs.filter(
            applicable_from__lte=instance.start
        ).filter(
            Q(
                applicable_to__isnull=True
            ) | Q(
                applicable_to__gte=instance.start
            )
        ).exists()
        shift_exists_for_end = base_qs.filter(
            applicable_from__lte=instance.end
        ).filter(
            Q(
                applicable_to__isnull=True
            ) | Q(
                applicable_to__gte=instance.end
            )
        ).exists()
        return all((shift_exists_for_end, shift_exists_for_start))

    def get_deleted_days(self, instance):
        days_deleted = TravelAttendanceDays.objects.filter(
            # HRIS-1584: Deleted Days seen after supervisor Declined the request.
            travelattendancedeleterequest__in=instance.delete_request.exclude(
                status__in=[CANCELLED, DECLINED]
            ).values_list('id', flat=True)
        )
        return TravelAttendanceDaysSerializer(
            instance=days_deleted,
            many=True,
            context=self.context,
        ).data


def group_dates_into_week(credit_json_list):
    def identifier_function(credit_json):
        return get_week(credit_json.get('credit_hour_date'))[0]

    return itertools.groupby(credit_json_list, key=identifier_function)


def group_dates_into_month(credit_json_list, organization):
    def identifier_function(credit_json):
        return CreditHourRequestSerializer.get_fiscal_month_for_date(
            credit_json.get('credit_hour_date'),
            organization
        )[0]

    return itertools.groupby(credit_json_list, key=identifier_function)


class TravelAttendanceWithCreditRequestSerializer(TravelAttendanceRequestSerializer):
    class Meta(TravelAttendanceRequestSerializer.Meta):
        pass

    @transaction.atomic()
    def create(self, validated_data):
        # Step1: Create Travel Attendance
        # Step2: Breakdown Travel Attendance
        # Step3: Link Travel Attendance With Credit Request
        credit_requests = validated_data.pop('credit_requests', [])
        instance = super().create(validated_data)
        # TravelAttendanceRequestSerializer.breakdown_travel_attendance()
        for credit_request in credit_requests:
            credit_request.update({
                'travel_attendance_request': instance,
                'request_remarks': validated_data.get('request_remarks'),
                'status': REQUESTED,
                'sender': self.context.get('sender'),
                'recipient': get_pre_approval_recipient(user=self.context.get('sender'))
            })
            credit_instance = CreditHourRequest.objects.create(
                **credit_request
            )
            CreditHourRequestSerializer.maintain_history(
                credit_instance,
                credit_instance.status,
                credit_instance.sender,
                credit_instance.recipient,
                credit_instance.request_remarks
            )
        return instance

    def validate(self, attrs):
        return self.validate_bulk_credit_requests(attrs)

    def validate_bulk_credit_requests(self, attrs):
        credit_requests = self.parse_credit_requests()
        # All validations are run from CreditHourRequestSerializer
        # Here, I shall only validate the grouped limit. (i.e. group of dates in week/month do not exceed limit)
        if credit_requests:
            credit_setting = nested_getattr(
                self.context.get('sender'),
                'attendance_setting.credit_hour_setting'
            )
            credit_requests_serializer = CreditHourRequestSerializer(
                fields=('credit_hour_date', 'credit_hour_duration'),
                many=True,
                data=credit_requests,
                context=self.context
            )
            credit_requests_serializer.is_valid(raise_exception=True)
            if credit_setting:
                if credit_setting.weekly_credit_hour_limit_applicable:
                    week_iterable = group_dates_into_week(
                        credit_requests_serializer.validated_data)
                    for week, week_credits in week_iterable:
                        sum_of_credits = sum(
                            [credit.get('credit_hour_duration').total_seconds() for credit in
                             week_credits]
                        )
                        if (sum_of_credits / 60) > credit_setting.weekly_credit_hour_limit:
                            raise ValidationError(
                                "The requests exceed weekly limit for credit hours."
                            )
                if credit_setting.monthly_credit_hour_limit_applicable:
                    month_iterable = group_dates_into_month(
                        credit_requests_serializer.validated_data,
                        self.context.get('sender').detail.organization
                    )
                    for month, monthly_credits in month_iterable:
                        sum_of_credits = sum(
                            [credit.get('credit_hour_duration').total_seconds() for credit in
                             monthly_credits]
                        )
                        if (sum_of_credits / 60) > credit_setting.monthly_credit_hour_limit:
                            raise ValidationError(
                                "The requests exceed monthly limit for credit hours."
                            )
                # TODO @Ravi: Validate bulk sum, against leave balance.
                attrs['credit_requests'] = credit_requests_serializer.validated_data
        return super().validate(attrs)

    def update(self, instance, validated_data):
        return instance

    def parse_credit_requests(self):
        key = 'credit_requests'
        nested_credit_keys = [x for x in self.initial_data.keys() if x.startswith(key)]
        ret = dict()
        for attachment_key in nested_credit_keys:
            parent = attachment_key.split('.')[0]
            key = attachment_key.split('.')[-1]
            parent_dict = ret.get(parent, {})
            parent_dict.update({
                key: self.initial_data.get(attachment_key)
            })
            ret.update({
                parent: parent_dict
            })
        return list(ret.values())


class TravelAttendanceOnBehalfSerializer(TravelAttendanceRequestSerializer):
    employee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)

    class Meta(TravelAttendanceRequestSerializer.Meta):
        fields = TravelAttendanceRequestSerializer.Meta.fields + ('employee',)

    def validate(self, attrs):
        if self.request.query_params.get('as') == 'supervisor':
            subordinate = attrs.get('employee')
            supervisor = subordinate.supervisors.filter(supervisor=self.context.get('user')).first()
            if not supervisor:
                raise ValidationError(
                    f"You are not the right supervisor for { attrs.get('employee') }."
                )
            if not (supervisor.approve or supervisor.forward):
                raise ValidationError(
                    f"You dont have authority to perform this action for { attrs.get('employee') }."
                )
        return super().validate(attrs)

    def create(self, validated_data):
        mode = self.request.query_params.get('as')
        user = self.context.get('user')
        requested_for = validated_data.pop('employee')
        recipient = user
        status = APPROVED
        if mode == 'supervisor':
            supervisor = requested_for.supervisors.filter(supervisor=user).first()
            if not supervisor.approve and supervisor.forward:
                status = FORWARDED
                recipient = get_appropriate_recipient(
                    user=requested_for, level=(supervisor.authority_order + 1))

        validated_data['user'] = requested_for
        validated_data['status'] = status
        validated_data['recipient'] = recipient
        return super().create(validated_data)



