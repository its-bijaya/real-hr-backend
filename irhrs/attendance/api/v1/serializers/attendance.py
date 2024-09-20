from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField, CharField, \
    DateField, DateTimeField, ReadOnlyField, ChoiceField, FloatField, BooleanField
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator

from irhrs.attendance.api.v1.serializers.breakout_penalty import BreakOutPenaltySettingSerializer
from irhrs.attendance.api.v1.serializers.credit_hours import CreditHourSettingSerializer
from irhrs.attendance.api.v1.serializers.overtime import \
    OvertimeSettingSerializer
from irhrs.attendance.api.v1.serializers.source import \
    AttendanceSourceSerializer
from irhrs.attendance.api.v1.serializers.workshift import WorkShiftSerializer, \
    WorkTimingSerializer
from irhrs.attendance.constants import WEB_APP, \
    PUNCH_OUT, PUNCH_IN, WH_DAILY, WH_MONTHLY, WH_WEEKLY, \
    TIMESHEET_ENTRY_REMARKS, OTHERS, NO_LEAVE, MOBILE_APP, WORKING_HOURS_DURATION_CHOICES
from irhrs.attendance.models import IndividualAttendanceSetting, \
    OvertimeSetting, WorkShift, TimeSheetEntryApproval, BreakOutPenaltySetting
from irhrs.attendance.models.attendance import WebAttendanceFilter, TimeSheet, \
    AttendanceUserMap, TimeSheetEntry, IndividualUserShift, IndividualWorkingHour
from irhrs.attendance.models.credit_hours import CreditHourSetting
from irhrs.attendance.signals import OFFLINE_ATTENDANCE, \
    perform_overtime_credit_hour_recalibration
from irhrs.attendance.utils.attendance import double_date_conflict_checker
from irhrs.attendance.validation_error_messages import IP_FILTERS_REQUIRED, \
    CONFLICTING_CIDR, OT_SETTING_REQUIRED, HAS_TO_BE_OF_SAME_ORGANIZATION, \
    SET_LESS_THAN_24, SET_LESS_THAN_768, SET_LESS_THAN_168, \
    SET_BOTH_HOURS_AND_DURATION
from irhrs.core.constants.common import WEB_ATTENDANCE_APPROVAL
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import DummyObject, get_today, combine_aware
from irhrs.core.validators import validate_past_datetime, MinMaxValueValidator
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import ATTENDANCE_PERMISSION
from irhrs.permission.constants.permissions.attendance import ATTENDANCE_APPROVAL_PERMISSION
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer, UserThickSerializer


USER = get_user_model()


class WebAttendanceFilterSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = WebAttendanceFilter
        fields = ['allow', 'cidr']


class IndividualAttendanceSettingSerializer(DynamicFieldsModelSerializer):
    ip_filters = WebAttendanceFilterSerializer(many=True)
    supervisor = UserThinSerializer(
        source='user.first_level_supervisor',
        fields=['id', 'full_name', 'profile_picture', 'is_current', 'organization', 'job_title'],
        read_only=True,
        allow_null=True
    )

    upcoming_shift = serializers.SerializerMethodField(read_only=True)
    upcoming_work_hour = serializers.SerializerMethodField()
    work_shift = WorkShiftSerializer(
        read_only=True
    )
    penalty_setting = BreakOutPenaltySettingSerializer(
        fields=['id', 'title'],
        read_only=True
    )

    class Meta:
        model = IndividualAttendanceSetting
        fields = (
            'id',
            'user',
            'work_shift',
            'supervisor',
            'web_attendance',

            'late_in_notification_email',
            'absent_notification_email',
            'weekly_attendance_report_email',

            'enable_overtime',

            'overtime_remainder_email',

            'overtime_setting',

            'enable_credit_hour',
            'credit_hour_setting',
            'penalty_setting',

            'ip_filters',
            'working_hours',
            'working_hours_duration',
            'upcoming_shift',
            "upcoming_work_hour",
            'enable_hr_notification',
            'enable_supervisor_notification',
            'enable_approval'
        )
        read_only_fields = (
            'work_shift',
            'overtime_setting',
            'working_hours',
            'working_hours_duration',
            'late_in_notification_email',
            'absent_notification_email',
            'weekly_attendance_report_email',
            'enable_overtime',
            'overtime_remainder_email',
            'penalty_setting',
            'credit_hour_setting',
            'user'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            if fields.get('user'):
                fields['user'] = UserThickSerializer(
                    context=self.context
                )
            if fields.get('work_shift'):
                fields['work_shift'] = WorkShiftSerializer(
                    fields=["id", "name", "is_expiring"],
                    context=self.context
                )
            if fields.get('overtime_setting'):
                fields['overtime_setting'] = OvertimeSettingSerializer(
                    fields=["slug", "name"],
                    context=self.context
                )
            if fields.get('credit_hour_setting'):
                fields['credit_hour_setting'] = CreditHourSettingSerializer(
                    fields=["slug", "name"],
                    context=self.context
                )
        return fields

    @staticmethod
    def get_upcoming_shift(obj):
        shift_objects = WorkShift.objects.filter(
            individual_shifts__individual_setting=obj,
            individual_shifts__applicable_from__gt=timezone.now(),
            individual_shifts__applicable_to__isnull=True
        )
        ser = WorkShiftSerializer(instance=shift_objects, many=True,
                                  fields=('id', 'name',))
        return ser.data

    @staticmethod
    def get_upcoming_work_hour(obj):
        upcoming = obj.individual_setting_working_hours.filter(
            applicable_from__gt=timezone.now(),
            applicable_to__isnull=True
        )

        if upcoming:
            return [{
                "working_hours": u.working_hours,
                "working_hours_duration": u.working_hours_duration,
                "applicable_from": u.applicable_from
            } for u in upcoming]
        return None

    def validate_ip_filters(self, ip_filters):
        # can be empty list if not web_attendance
        if ip_filters:
            cidrs = []
            for ip_filter in ip_filters:
                if ip_filter.get('cidr') in cidrs:
                    raise ValidationError(CONFLICTING_CIDR)
                else:
                    cidrs.append(ip_filter.get('cidr'))
        return ip_filters

    def validate(self, attrs):
        web_attendance = attrs.get('web_attendance')
        ip_filters = attrs.get('ip_filters')
        enable_overtime = attrs.get('enable_overtime')
        overtime_setting = attrs.get('overtime_setting')
        work_shift = attrs.get('work_shift')
        user = attrs.get('user')

        working_hours = attrs.pop('working_hours', None)
        working_hours_duration = attrs.pop('working_hours_duration', '')

        if work_shift and working_hours:
            raise ValidationError("Can not set both work shift and work hours.")

        if bool(working_hours) != bool(working_hours_duration):
            raise ValidationError(SET_BOTH_HOURS_AND_DURATION)

        if working_hours and working_hours_duration:
            if working_hours_duration == WH_DAILY and working_hours > 24:
                raise ValidationError({'working_hours': [SET_LESS_THAN_24]})

            if working_hours_duration == WH_MONTHLY and working_hours > 768:
                raise ValidationError({'working_hours': [SET_LESS_THAN_768]})

            if working_hours_duration == WH_WEEKLY and working_hours > 168:
                raise ValidationError({'working_hours': [SET_LESS_THAN_168]})

            attrs["working_hour"] = DummyObject(
                working_hours=working_hours,
                working_hours_duration=working_hours_duration
            )
        else:
            attrs["working_hour"] = None

        if work_shift and work_shift.organization != user.detail.organization:
            raise ValidationError(HAS_TO_BE_OF_SAME_ORGANIZATION)

        if web_attendance and not ip_filters:
            raise ValidationError(IP_FILTERS_REQUIRED)

        if enable_overtime and not overtime_setting:
            raise ValidationError(OT_SETTING_REQUIRED)

        # update attrs if no values were sent (None) because only put is allowed
        attrs["work_shift"] = work_shift

        return attrs

    def create(self, validated_data):
        ip_filters = validated_data.pop('ip_filters', None)
        work_shift = validated_data.pop('work_shift', None)
        working_hour = validated_data.pop('working_hour', None)
        setting = super().create(validated_data)

        if ip_filters and setting.web_attendance:
            filters = [
                WebAttendanceFilter(
                    setting=setting,
                    **fil
                )
                for fil in ip_filters
            ]
            WebAttendanceFilter.objects.bulk_create(filters)
        _ = transaction.commit()
        if work_shift:
            setting.work_shift = work_shift
        elif working_hour:
            setting.working_hour = working_hour
        return setting

    def update(self, instance, validated_data):
        valid_fields = [
            'web_attendance', 'ip_filters',
            'enable_hr_notification', 'enable_supervisor_notification', 'enable_approval'
        ]
        validated_data = {
            k: v for k, v in validated_data.items() if k in valid_fields
        }
        # Update is confirmed to be PUT
        _ = validated_data.pop('user', None)
        ip_filters = validated_data.pop('ip_filters', None)
        instance = super().update(instance, validated_data)
        instance.ip_filters.all().delete()

        if instance.web_attendance and ip_filters:
            filters = [
                WebAttendanceFilter(
                    setting=instance,
                    **fil
                )
                for fil in ip_filters
            ]
            WebAttendanceFilter.objects.bulk_create(filters)

        return instance


class BulkIndividualAttendanceSettingSerializer(DummySerializer):
    def get_fields(self):
        organization = self.context.get('organization')
        return {
            'remove_shift': serializers.BooleanField(
                required=False,
                allow_null=True,
            ),
            'remove_working_hours': serializers.BooleanField(
                required=False,
                allow_null=True,
            ),
            'remove_overtime': serializers.BooleanField(
                required=False,
                allow_null=True
            ),
            'remove_credit_hour': serializers.BooleanField(
                required=False,
                allow_null=True
            ),
            'remove_penalty_setting': serializers.BooleanField(
                required=False,
                allow_null=True
            ),
            'users': PrimaryKeyRelatedField(
                queryset=get_user_model().objects.filter(
                    detail__organization=organization,
                    attendance_setting__isnull=False,
                    is_active=True,
                    is_blocked=False,
                    user_experiences__is_current=True
                ),
                many=True
            ),
            'overtime_setting': SlugRelatedField(
                queryset=OvertimeSetting.objects.filter(
                    organization=organization
                ),
                slug_field='slug',
                allow_null=True,
                required=False
            ),
            'credit_hour_setting': SlugRelatedField(
                queryset=CreditHourSetting.objects.filter(
                    organization=organization
                ),
                slug_field='slug',
                allow_null=True,
                required=False
            ),
            'penalty_setting': PrimaryKeyRelatedField(
                queryset=BreakOutPenaltySetting.objects.filter(
                    organization=organization
                ),
                allow_null=True,
                required=False
            ),
            'work_shift': PrimaryKeyRelatedField(
                queryset=WorkShift.objects.filter(
                    organization=organization
                ),
                allow_null=True,
                required=False
            ),
            **{
                field: serializers.BooleanField(
                    allow_null=True,
                    required=False
                ) for field in (
                    "late_in_notification_email",
                    "absent_notification_email",
                    "weekly_attendance_report_email",
                    "overtime_remainder_email",
                )
            },
            'working_hours': serializers.IntegerField(
                required=False,
                allow_null=True
            ),
            'working_hours_duration': serializers.ChoiceField(
                allow_blank=True,
                allow_null=True,
                required=False,
                choices=WORKING_HOURS_DURATION_CHOICES
            ),
            'web_attendance': serializers.BooleanField(
                required=False,
                allow_null=True,
            ),
            'remove_web_attendance': serializers.BooleanField(
                required=False,
                allow_null=True,
            ),
            'ip_filters': WebAttendanceFilterSerializer(
                many=True,
                required=False
            ),
        }

    def validate_ip_filters(self, ip_filters):
        # can be empty list if not web_attendance
        if ip_filters:
            cidrs = []
            for ip_filter in ip_filters:
                if ip_filter.get('cidr') in cidrs:
                    raise ValidationError(CONFLICTING_CIDR)
                else:
                    cidrs.append(ip_filter.get('cidr'))
        return ip_filters

    def validate(self, attrs):
        users = attrs.get('users', [])
        work_shift = attrs.get('work_shift')
        working_hours = attrs.get('working_hours', None)
        working_hours_duration = attrs.get('working_hours_duration', '')
        web_attendance = attrs.get('web_attendance')
        ip_filters = attrs.get('ip_filters')

        if work_shift and working_hours:
            raise ValidationError("Can not set both work shift and work hours.")

        if bool(working_hours) != bool(working_hours_duration):
            raise ValidationError(SET_BOTH_HOURS_AND_DURATION)

        if working_hours and working_hours_duration:
            if working_hours_duration == WH_DAILY and working_hours > 24:
                raise ValidationError({'working_hours': [SET_LESS_THAN_24]})

            if working_hours_duration == WH_MONTHLY and working_hours > 768:
                raise ValidationError({'working_hours': [SET_LESS_THAN_768]})

            if working_hours_duration == WH_WEEKLY and working_hours > 168:
                raise ValidationError({'working_hours': [SET_LESS_THAN_168]})
        # ensure both credit and overtime is not set at once.
        # credit_hour_setting = attrs.get('credit_hour_setting')
        # overtime_setting = attrs.get('overtime_setting')
        # if credit_hour_setting:
        #     if IndividualAttendanceSetting.objects.filter(
        #         user__in=users
        #     ).filter(
        #         enable_overtime=True
        #     ).exists():
        #         raise ValidationError({
        #             'credit_hour_setting': 'There are users with active Overtime Setting.'
        #                                    'Please remove overtime before assignment of Credit Hour Setting.'
        #         })
        # if overtime_setting:
        #     if IndividualAttendanceSetting.objects.filter(
        #         user__in=users
        #     ).filter(
        #         enable_credit_hour=True
        #     ).exists():
        #         raise ValidationError({
        #             'overtime_setting': 'There are users with active Credit Hour Setting.'
        #                                 'Please remove Credit Hour Setting before assignment of Overtime Setting..'
        #         })

        if not users:
            raise ValidationError({
                'users': 'Please select at least one user.'
            })
        if web_attendance and not ip_filters:
            raise ValidationError(IP_FILTERS_REQUIRED)

        _VALID_FLAGS = True, False
        action_defined = any((
            attrs.get('remove_shift'),
            attrs.get('remove_working_hours'),
            attrs.get('remove_overtime'),
            attrs.get('remove_credit_hour'),
            attrs.get('remove_penalty_setting'),
            attrs.get('work_shift'),
            attrs.get('overtime_setting'),
            attrs.get('penalty_setting'),
            attrs.get('credit_hour_setting'),
            attrs.get('working_hours'),
            attrs.get('working_hours_duration'),
            attrs.get("late_in_notification_email") in _VALID_FLAGS,
            attrs.get("absent_notification_email") in _VALID_FLAGS,
            attrs.get("weekly_attendance_report_email") in _VALID_FLAGS,
            attrs.get("overtime_remainder_email") in _VALID_FLAGS,
            attrs.get("web_attendance"),
            attrs.get("remove_web_attendance")
        ))
        if not action_defined:
            raise ValidationError(
                'Please select at least one action.'
            )
        return super().validate(attrs)

    def create(self, validated_data):
        users = validated_data.get('users', [])

        remove_shift = validated_data.get('remove_shift')
        remove_working_hours = validated_data.get('remove_working_hours')
        remove_overtime = validated_data.get('remove_overtime')
        remove_credit_hour = validated_data.get('remove_credit_hour')
        remove_penalty_setting = validated_data.get('remove_penalty_setting')

        new_shift = validated_data.get('work_shift')
        new_overtime = validated_data.get('overtime_setting')
        new_penalty_setting = validated_data.get('penalty_setting')
        new_credit_hour = validated_data.get('credit_hour_setting')
        working_hours = validated_data.get('working_hours')
        working_hours_duration = validated_data.get('working_hours_duration')
        web_attendance = validated_data.get('web_attendance')
        ip_filters = validated_data.get('ip_filters', [])
        remove_web_attendance = validated_data.get('remove_web_attendance')

        # Get flags from request data if provided else do not create
        flags = {f: v for f, v in {
            f: validated_data.get(f, ...) for f in (
                "late_in_notification_email",
                "absent_notification_email",
                "weekly_attendance_report_email",
                "overtime_remainder_email",
            )
        }.items() if v is not ... and v is not None}
        _dummy_return = super().create(validated_data)

        if remove_shift:
            base_qs = IndividualUserShift.objects.filter(
                individual_setting__user__in=users
            )
            # Remove future applicable User Shift.
            base_qs.filter(
                applicable_from__gt=get_today()
            ).delete()

            base_qs.filter(
                applicable_from__lte=get_today(),
                applicable_to__isnull=True
            ).update(
                applicable_to=get_today()
            )
        elif new_shift:
            for att in map(lambda x: x.attendance_setting, users):
                att.work_shift = new_shift
        elif remove_working_hours:
            base_qs = IndividualWorkingHour.objects.filter(
                individual_setting__user__in=users
            )
            # Remove future applicable User Shift.
            base_qs.filter(
                applicable_from__gt=get_today()
            ).delete()

            base_qs.filter(
                applicable_from__lte=get_today(),
                applicable_to__isnull=True
            ).update(
                applicable_to=get_today()
            )
        elif working_hours and working_hours_duration:
            # Set here
            working_hrs_obj = DummyObject(
                working_hours=working_hours,
                working_hours_duration=working_hours_duration
            )
            for att in map(lambda x: x.attendance_setting, users):
                att.working_hour = working_hrs_obj

        if remove_overtime:
            IndividualAttendanceSetting.objects.filter(
                user__in=users
            ).update(
                overtime_setting=None,
                enable_overtime=False
            )
        elif new_overtime:
            IndividualAttendanceSetting.objects.filter(
                user__in=users
            ).update(
                overtime_setting=new_overtime,
                enable_overtime=True
            )

        if remove_credit_hour:
            IndividualAttendanceSetting.objects.filter(
                user__in=users
            ).update(
                credit_hour_setting=None,
                enable_credit_hour=False
            )
        elif new_credit_hour:
            IndividualAttendanceSetting.objects.filter(
                user__in=users
            ).update(
                credit_hour_setting=new_credit_hour,
                enable_credit_hour=True
            )

        if remove_penalty_setting:
            IndividualAttendanceSetting.objects.filter(
                user__in=users
            ).update(
                penalty_setting=None
            )
        elif new_penalty_setting:
            IndividualAttendanceSetting.objects.filter(user__in=users).update(
                penalty_setting=new_penalty_setting
            )

        if flags:
            IndividualAttendanceSetting.objects.filter(
                user__in=users
            ).update(
                **flags
            )

        if web_attendance and ip_filters:
            IndividualAttendanceSetting.objects.filter(user__in=users).update(web_attendance=True)
            for user in users:
                setting = IndividualAttendanceSetting.objects.filter(user=user).first()
                if setting:
                    setting.ip_filters.all().delete()                    
                    filters = [
                        WebAttendanceFilter(
                                setting=setting,
                                **fil
                            )
                        for fil in ip_filters
                    ]
                    WebAttendanceFilter.objects.bulk_create(filters)
        
        if remove_web_attendance:
            IndividualAttendanceSetting.objects.filter(user__in=users).update(web_attendance=False)
            WebAttendanceFilter.objects.filter(setting__user__in=users).delete()
        return _dummy_return

    def update(self, instance, validated_data):
        return instance


class AttendanceUserMapSerializer(DynamicFieldsModelSerializer):
    supervisor = UserThinSerializer(
        source="setting.user.first_level_supervisor",
        read_only=True,
        fields=('user_id', 'full_name', 'profile_picture', 'is_current', 'organization', 'job_title')
    )

    class Meta:
        model = AttendanceUserMap
        fields = ('id', 'setting', 'bio_user_id', 'supervisor', 'source')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('bio_user_id', 'source'),
                message='The device already has this Bio User Id set.'
            ),
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('setting', 'source'),
                message='This user already has Bio User Id set for this device.'
            )
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields["setting"] = IndividualAttendanceSettingSerializer(
                fields=["id", "user", "work_shift", "username"],
                context=self.context
            )
            fields["source"] = AttendanceSourceSerializer(
                fields=["id", "name", "serial_number", "sync_method"],
                context=self.context
            )
        return fields


class TimeSheetSerializer(DynamicFieldsModelSerializer):
    # timesheet for individual
    info = ReadOnlyField(source='attendance_category')
    work_time = WorkTimingSerializer(read_only=True,
                                     allow_null=True)
    work_shift = WorkShiftSerializer(fields=['id', 'name'], read_only=True,
                                     allow_null=True)
    can_adjust = SerializerMethodField()

    class Meta:
        model = TimeSheet
        fields = [
            "id",
            "coefficient",
            "punch_in",
            "punch_out",
            "punch_in_delta",
            "punch_out_delta",
            "timesheet_for",
            "info",
            "can_adjust",
            "work_time",
            "work_shift",
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            if fields.get('coefficient'):
                fields["coefficient"] = SerializerMethodField()
        return fields

    @staticmethod
    def get_coefficient(instance):
        if not instance:
            return None
        if instance.leave_coefficient == NO_LEAVE:
            return instance.get_coefficient_display()
        return instance.get_leave_coefficient_display()

    @staticmethod
    def get_can_adjust(instance):
        # the limit is no longer valid.
        return True


class UserTimeSheetSerializer(TimeSheetSerializer):
    # user with timesheet details
    timesheet_user = UserThinSerializer()

    class Meta(TimeSheetSerializer.Meta):
        fields = TimeSheetSerializer.Meta.fields + ['timesheet_user']


class TimeSheetImportSerializer(DynamicFieldsModelSerializer):
    timesheet_for = serializers.DateTimeField()
    punch_in = serializers.TimeField()
    punch_out = serializers.TimeField()
    extends = serializers.CharField(
        default='f',
        write_only=True
    )

    class Meta:
        model = TimeSheet
        fields = (
            'timesheet_for', 'punch_in', 'punch_out', 'extends'
        )

    def validate(self, attrs):
        extends = attrs.get('extends', 'f').lower() in ('t', 'true')
        date = attrs.get('timesheet_for').date()
        punch_in = combine_aware(
            date,
            attrs.get('punch_in')
        )
        punch_out = combine_aware(
            date + timedelta(days=1) if extends else date,
            attrs.get('punch_out')
        )
        if date > get_today():
            raise ValidationError(
                {
                    'timesheet_for': f'Unable to punch attendance for future date.'
                }
            )
        if punch_in > punch_out:
            raise ValidationError(
                f'Punch Out must be greater than Punch In.'
            )
        attrs.update({
            'punch_in': {'date_time': punch_in, "entry_type": PUNCH_IN},
            'punch_out': {'date_time': punch_out, "entry_type": PUNCH_OUT}
        })
        return attrs


class TimeSheetEntrySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TimeSheetEntry
        fields = [
            "id", "timestamp", "entry_method",
            "entry_type", "category", "remarks",
            "remark_category", "latitude", "longitude"
        ]


class TimeSheetEntryApprovalSerializer(TimeSheetEntrySerializer):
    class Meta(TimeSheetEntrySerializer.Meta):
        model = TimeSheetEntryApproval
        fields = TimeSheetEntrySerializer.Meta.fields + ['status']


class WebAttendanceSerializer(DummySerializer):
    remark_category = ChoiceField(choices=TIMESHEET_ENTRY_REMARKS)
    message = CharField(max_length=255, default='')
    entry_method = ChoiceField(choices=(
        (WEB_APP, 'Web App'),
        (MOBILE_APP, 'Mobile App'),
    ), default=WEB_APP)

    # location details [Optional]
    latitude = FloatField(allow_null=True, required=False,
                          validators=[MinMaxValueValidator(min_value=-90, max_value=90)])
    longitude = FloatField(allow_null=True, required=False,
                           validators=[MinMaxValueValidator(min_value=-180, max_value=180)])
    working_remotely = BooleanField(default=False)

    def validate(self, attrs):
        if bool(attrs.get('longitude')) != bool(attrs.get('latitude')):
            raise ValidationError("`latitude` and `longitude` are required in pair.")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        entry_type = validated_data.get('entry_type')
        remarks = validated_data.get('message', '')
        remark_category = validated_data.get('remark_category', OTHERS)
        entry_method = validated_data.get('entry_method')
        latitude = validated_data.get('latitude')
        longitude = validated_data.get('longitude')
        working_remotely = validated_data.get('working_remotely')

        notify_hr = user.attendance_setting.enable_hr_notification
        notify_supervisor = user.attendance_setting.enable_supervisor_notification
        _timesheet = None
        supervisor = user.first_level_supervisor

        if user.attendance_setting.enable_approval:
            _timesheet = TimeSheet.objects.generate_approvals(
                user,
                timezone.now(),
                entry_method,
                entry_type=entry_type,
                supervisor=supervisor,
                remarks=remarks,
                remark_category=remark_category,
                latitude=latitude,
                longitude=longitude,
                working_remotely=working_remotely
            )
            notify_hr = True
            notify_supervisor = True
        else:
            _timesheet = TimeSheet.objects.clock(
                user,
                timezone.now(),
                entry_method,
                entry_type,
                remarks=remarks,
                remark_category=remark_category,
                latitude=latitude,
                longitude=longitude,
                working_remotely=working_remotely
            )

        if not _timesheet:
            raise ValidationError(detail={"non_field_errors": ["Could not clock."]})

        if notify_hr or notify_supervisor:
            organization = user.detail.organization

            text = f"{user.full_name} punched in using web attendance feature."
            supervisor_url = f'/user/supervisor/attendance/reports/daily-attendance?user={user.id}'
            admin_url = f'/admin/{organization.slug}/attendance/reports/daily-attendance?user={user.id}'

            if user.attendance_setting.enable_approval:
                text = f"{user.full_name} sent attendance request."
                supervisor_url = '/user/supervisor/attendance/requests/web-attendance'
                admin_url = f'/admin/{organization.slug}/attendance/requests/web-attendance'

            # force interactive notification for FE
            interactive_data = dict(
                is_interactive=True,
                interactive_type=WEB_ATTENDANCE_APPROVAL,
                interactive_data={
                    'timesheet_id': _timesheet.id,
                    'organization': {
                        'name': organization.name,
                        'slug': organization.slug,
                    }
                }
            )
            if notify_supervisor and user.first_level_supervisor and user.first_level_supervisor != get_system_admin():
                add_notification(
                    text=text,
                    recipient=user.first_level_supervisor,
                    action=_timesheet,
                    actor=user,
                    url=supervisor_url,
                    **interactive_data
                )
            if notify_hr:
                notify_organization(
                    text=text,
                    action=user,
                    organization=organization,
                    permissions=[
                        ATTENDANCE_PERMISSION, ATTENDANCE_APPROVAL_PERMISSION
                    ],
                    url=admin_url
                )
        return DummyObject(**validated_data)


class ManualAttendanceSerializer(DummySerializer):
    timesheet_user = PrimaryKeyRelatedField(
        queryset=USER.objects.all()
    )
    punch_in = DateTimeField(validators=[validate_past_datetime])
    punch_out = DateTimeField(validators=[validate_past_datetime], allow_null=True)
    date = DateField()
    timesheet = PrimaryKeyRelatedField(
        queryset=TimeSheet.objects.all(),
        allow_null=True
    )
    working_remotely = BooleanField(default=False)
    remarks = CharField(max_length=255)

    def validate_date(self, date):
        if date > get_today():
            raise ValidationError("Date must be a past date.")
        return date

    def validate(self, attrs):
        date = attrs.get('date')
        punch_in = attrs.get('punch_in')
        punch_out = attrs.get('punch_out')
        timesheet = attrs.get('timesheet')
        timesheet_user = attrs.get('timesheet_user')
        errors = dict()

        if timesheet:
            if timesheet.timesheet_user != timesheet_user:
                errors.update({
                    'timesheet': ['The timesheet for this user is not valid.']
                })
            if timesheet.timesheet_for != date:
                errors.update({
                    'date': ['The timesheet for the given date is not valid.']
                })
        else:
            # if timesheet is not created for the day then only allow user to
            # attend without timesheet
            # TODO: @Ravi WorkShift update case
            # Even in the past, Work-shift is taken from current. This is a potential issue.
            if TimeSheet.objects.filter(timesheet_for=date,
                                        timesheet_user=timesheet_user).exists():
                errors.update({
                    'timesheet': ['This field is required.']
                })

        if punch_in.date() < date:
            errors.update({
                'punch_in': ['Punch in can not be before attendance date.']
            })
        elif (punch_in.date() - date).days > 1:
            errors.update({
                'punch_in': ['Punch in date can not be more than 1 day after '
                             'the attendance date.']
            })

        if punch_out and punch_out.date() < date:
            errors.update({
                'punch_out': ['Punch out can not be before attendance date.']
            })

        if punch_out and punch_out < punch_in:
            errors.update({
                'non_field_errors': ['Punch In must be before Punch Out.']
            })

        if errors:
            raise ValidationError(errors)

        return attrs

    def create(self, validated_data):
        timesheet_user = validated_data.get('timesheet_user')
        timesheet = validated_data.get('timesheet')
        punch_in = validated_data.get('punch_in')
        punch_out = validated_data.get('punch_out')
        manual_user = self.context.get("request").user
        working_remotely = validated_data.get('working_remotely')
        remarks = validated_data.get('remarks')

        common_params = {
            "user": timesheet_user,
            "entry_method": WEB_APP,
            "manual_user": manual_user,
            "remarks": remarks,
            "working_remotely": working_remotely,
        }

        if timesheet:
            common_params.update({"timesheet": timesheet})

        punch_in_params = common_params.copy()
        punch_out_params = common_params.copy()

        punch_in_params.update({
            "entry_type": PUNCH_IN,
            "date_time": punch_in
        })

        TimeSheet.objects.clock(
            **punch_in_params
        )

        if punch_out:
            punch_out_params.update({
                "entry_type": PUNCH_OUT,
                "date_time": punch_out
            })
            timesheet = TimeSheet.objects.clock(
                **punch_out_params
            )
        transaction.commit()
        if timesheet:
            timesheet.refresh_from_db()
            perform_overtime_credit_hour_recalibration(
                timesheet=timesheet,
                actor=manual_user,
                action_type=OFFLINE_ATTENDANCE
            )
        return super().create(validated_data)


class IndividualUserShiftSerializer(DynamicFieldsModelSerializer):
    applicable_from = serializers.DateField(required=True)

    class Meta:
        model = IndividualUserShift
        fields = (
            'id',
            'shift',
            'applicable_from',
            'applicable_to',
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method == 'GET':
            fields['shift'] = WorkShiftSerializer(fields=('id', 'name'))
        else:
            fields['shift'].queryset = self.get_shift_queryset
        return fields

    def create(self, validated_data):
        validated_data['individual_setting'] = self.user.attendance_setting
        current_from = validated_data['applicable_from']
        self.user.attendance_setting.individual_setting_shift.filter(
            applicable_to__isnull=True
        ).update(
            applicable_to=current_from - timedelta(days=1)
        )
        return super().create(validated_data)

    def validate(self, attrs):
        applicable_from = attrs['applicable_from']
        applicable_to = attrs['applicable_to']
        if self.verify_clashes(applicable_from, applicable_to):
            raise ValidationError(
                'Applicable dates are conflicting.'
            )
        return super().validate(attrs)

    def verify_clashes(self, current_from, current_to):
        att_setting = self.user.attendance_setting
        old_queryset = att_setting.individual_setting_shift.order_by('applicable_from')
        if self.instance:
            old_queryset = old_queryset.exclude(id=self.instance.id)
        return double_date_conflict_checker(
            queryset=old_queryset,
            new_from=current_from,
            new_to=current_to
        )

    @property
    def get_shift_queryset(self):
        return WorkShift.objects.filter(
            organization=self.organization
        )

    @property
    def organization(self):
        return self.context['organization']

    @property
    def user(self):
        return self.context['user']

class ExcelCreateUpdateSerializer(serializers.Serializer):
    file = serializers.FileField(
        max_length=100,
        validators=[
        FileExtensionValidator(
            allowed_extensions=['xlsx', 'xlsm', 'xltx', 'xltm']
        )],
        write_only=True
    )
