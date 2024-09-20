from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django_q.tasks import async_task
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField

from irhrs.attendance.models import WorkShift
from irhrs.attendance.models.shift_roster import TimeSheetRoster
from irhrs.attendance.utils.shift_planner import (
    find_shift_timings_for_future, roster_shift_display, send_roster_notification,
    segregate_roster_payload
)
from irhrs.attendance.utils.timesheet import update_timesheet_rooster_and_time_sheet, \
    create_timesheet_roster_and_update_timesheet
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.common import DummyObject
from irhrs.payroll.utils.helpers import get_last_payroll_generated_date_excluding_rejected_payroll
from irhrs.users.api.v1.serializers.thin_serializers import UserThickSerializer
from django.utils.translation import gettext_lazy as _

USER = get_user_model()


class TimeSheetRosterListSerializer(UserThickSerializer):
    results = SerializerMethodField()

    class Meta(UserThickSerializer.Meta):
        fields = [
            'id',
            'full_name',
            'profile_picture',
            'job_title',
            'is_online',
            'is_current',
            'organization',
            'results',
            'username',
        ]

    def get_results(self, instance):
        fiscal_month = self.context.get('fiscal_month')
        queryset = instance._roster_qs
        defaults = find_shift_timings_for_future(user=instance, fym=fiscal_month)
        ret = TimeSheetRosterSerializer(
            many=True,
            fields=('shift', 'date'),
            context=self.context,
            instance=queryset
        ).data
        # normalized_defaults = {
        #     str(k): v.get('shift', {}) for k, v in defaults.items()
        # }
        normalized_ret = {
            datum['date']: datum.get('shift', {})
            for datum in ret
        }
        defaults.update(normalized_ret)
        return defaults


class TimeSheetRosterSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TimeSheetRoster
        fields = (
            'shift', 'id', 'date'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['shift'] = serializers.SerializerMethodField()
        else:
            fields['shift'] = serializers.PrimaryKeyRelatedField(
                queryset=self.get_shift_queryset(),
            )
        return fields

    def get_shift_queryset(self):
        return WorkShift.objects.filter(
            organization=self.context['organization']
        )

    def validate_date(self, date):
        fiscal_range = self.context.get('fiscal_month')
        # https://stackoverflow.com/questions/5464410/how-to-tell-if-a-date-is-between-two-other-dates
        if fiscal_range.start_at <= date <= fiscal_range.end_at:
            return date
        raise serializers.ValidationError(
            "The date is beyond fiscal range"
        )

    @staticmethod
    def get_shift(instance):
        return roster_shift_display(
            instance.shift
        )


class TimeSheetRosterCreateSerializer(serializers.Serializer):
    def get_fields(self):
        return {
            'roster_list': TimeSheetRosterSerializer(
                many=True,
            ),
            'user': PrimaryKeyRelatedField(
                queryset=self.get_valid_user_queryset(),
                error_messages={
                    'required': _('This field is required.'),
                    'does_not_exist': _('Only immediate subordinates is allowed.'),
                    'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
                }
            )
        }

    def get_valid_user_queryset(self):
        return USER.objects.filter(
            **self.context.get('user_filter')
        ).current()

    @staticmethod
    def validate_roster_list(roster_list):
        if not roster_list:
            raise serializers.ValidationError(
                "Roster list may not be empty."
            )
        return roster_list


class TimeSheetRosterBulkCreateSerializer(serializers.Serializer):
    def get_fields(self):
        return {
            'data': TimeSheetRosterCreateSerializer(many=True, context=self.context),
            # 'fiscal_month': serializers.PrimaryKeyRelatedField(
            #     queryset=self.get_fiscal_month_queryset()
            # )
        }

    # def get_fiscal_month_queryset(self):
    #     return FiscalYearMonth.objects.filter()

    @transaction.atomic
    def create(self, validated_data):
        fiscal_month = self.context['fiscal_month']
        error_dict = {}
        for roster_data in validated_data.get('data'):
            user = roster_data['user']
            new_list, existing_list, deleted_list = segregate_roster_payload(
                roster_data['roster_list'], user, fiscal_month
            )
            cleaned_data = self.clean_list(roster_data['roster_list'])
            last_payroll_generated_date = get_last_payroll_generated_date_excluding_rejected_payroll(user)
            error_msg = f"Payroll has generated for selected date." \
                                       f" Last payroll generated date was {last_payroll_generated_date}."
            for timesheet_roster in existing_list:
                if last_payroll_generated_date and last_payroll_generated_date >= timesheet_roster.date:
                    error_dict[user.full_name] = error_msg
                    break
                shift = [data['shift'] for data in cleaned_data if
                         data['date'] == timesheet_roster.date]
                async_task(
                    update_timesheet_rooster_and_time_sheet,
                    timesheet_roster,
                    shift[0]
                )
            new_roster_data = self.clean_list(new_list)
            if new_roster_data:
                async_task(
                    create_timesheet_roster_and_update_timesheet,
                    user,
                    new_roster_data,
                    last_payroll_generated_date,
                    error_msg
                )
                errors = cache.get('roster_errors', None)
                cache.delete('roster_errors')
                if errors:
                    error_dict.update(errors)
                    continue
            TimeSheetRoster.objects.filter(
                id__in=deleted_list
            ).delete()
            send_roster_notification(user, fiscal_month)
        if error_dict:
            raise ValidationError(error_dict)
        return DummyObject(**validated_data)

    @staticmethod
    def clean_list(new_list):
        di = {o['date']: o for o in new_list}
        return list(di.values())
