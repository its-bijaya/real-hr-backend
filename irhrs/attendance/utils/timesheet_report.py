from dateutil import rrule
from django.db import models
from django.db.models import Case, When, F, Subquery, OuterRef, Sum
from django.utils import timezone
from django.utils.functional import cached_property

from irhrs.attendance.api.v1.serializers.timesheet_registration_report_settings import \
    TimeSheetRegistrationReportSettingsSerializer
from irhrs.attendance.constants import WORKDAY, NO_LEAVE, HOLIDAY, OFFDAY, FIRST_HALF, SECOND_HALF, \
    APPROVED, GENERATED, CREDIT_TIME_OFF
from irhrs.attendance.models import TimeSheetRegistrationReportSettings, TimeSheet, \
    AttendanceUserMap
from irhrs.attendance.models.timesheet_report_request import TimeSheetReportRequest, \
    TimeSheetReportRequestHistory
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.common import get_today
from irhrs.leave.constants.model_constants import CREDIT_HOUR
from irhrs.leave.models import LeaveType, LeaveAccount, LeaveAccountHistory
from irhrs.leave.models.request import LeaveSheet, LeaveRequestDeleteHistory


class TimeSheetReport:
    default_leave_legend = {
        "legend": "L",
        "color": "#8B008B",
        "text": "Leave"
    }

    def __init__(self, user, fiscal_year, queryset=None, fiscal_month=None, report_setting=None):
        self.user = user
        self.organization = user.detail.organization
        self.fiscal_year = fiscal_year
        self._queryset = queryset
        self._fiscal_month = fiscal_month
        self._report_setting = report_setting
        self.legend = dict()
        self.leave_legend = dict()

        self.initialize_legend()
        self.initialize_leave_legend()

        self.all_colors = ["#5B84B1FF", "#5F4B8BFF", "#E69A8DFF", "#00A4CCFF", "#F95700FF",
                           "#4B878BFF", "#ADEFD1FF", "#606060FF", "#D6ED17FF", "#ED2B33FF",
                           "#2C5F2D", "#00539CFF", "#EEA47FFF", "#0063B2FF", "#97BC62FF",
                           "#FEE715FF", "#B1624EFF", "#9CC3D5FF", "#89ABE3FF", "#F2AA4CFF",
                           "#603F83FF", "#C7D3D4FF", "#2BAE66FF", "#F95700FF"
                           ]
        self.unused_color = list(self.all_colors)

    @cached_property
    def queryset(self):
        queryset = self._queryset or TimeSheet.objects.filter(timesheet_user=self.user)

        queryset = queryset.filter(
            timesheet_for__gte=self.fiscal_year.start_at,
            timesheet_for__lte=self.fiscal_year.end_at
        )

        if self._fiscal_month:
            queryset = queryset.filter(timesheet_for__lte=self._fiscal_month.end_at)
        return queryset

    @cached_property
    def report_setting(self):
        return self._report_setting or TimeSheetRegistrationReportSettings.setting_for_organization(
            self.organization
        )

    @cached_property
    def month_slots(self):
        return list(self.fiscal_year.fiscal_months.all().values_list(
            'id',
            'display_name',
            'start_at',
            'end_at'
        ))

    def initialize_legend(self):
        # format { legend: {"name": "", "color": ""}}
        saved_primary_legend = {
            # "Offday": {
            #     "legend": "O",
            #     "color": "black"
            # },
            legend_['name']: {
                "legend": legend_["letter"],
                "color": legend_["color"],
                "text": legend_["text"]
            }
            for legend_ in self.report_setting.primary_legend
        }
        self.legend = {
            legend['name']: saved_primary_legend.get(
                legend['name'], {
                    "legend": legend["letter"],
                    "color": legend["color"],
                    "text": legend["text"]
                }  # if not configured pick from default legend
            )
            for legend in TimeSheetRegistrationReportSettings.DEFAULT_PRIMARY_LEGEND
        }

    def initialize_leave_legend(self):
        self.leave_legend = {
            str(legend["leave_type_id"]): {
                "legend": legend["letter"],
                "color": legend["color"],
                "text": legend["text"],
                "name": legend["text"]
            }
            for legend in self.report_setting.leave_legend
        }

    def get_legend_data(self, name, hours=None, leave_type_id=None):
        if name == "time_registered":
            return {
                "legend": hours,
                "color": self.legend["time_registered"]["color"],
                "hours": hours,
                "text": self.legend["time_registered"]["text"]
            }
        else:
            if leave_type_id:
                legend_data = self.leave_legend.get(str(leave_type_id))
                if not legend_data:
                    return dict(
                        hours=hours,
                        **self.default_leave_legend
                    )

            else:
                legend_data = self.legend.get(name)
                if not legend_data:
                    legend_data = self.get_new_legend_data(name)
                    self.legend.update({
                        name: legend_data
                    })
            return dict(hours=hours, **legend_data)

    def get_new_legend_data(self, name):
        if not self.unused_color:
            self.unused_color = list(self.all_colors)
        return {
            'legend': name[0].upper(),
            'color': self.unused_color.pop()
        }

    def get_days_info(self, timesheet_info):

        if timesheet_info['hour_off_coefficient'] in [CREDIT_HOUR, CREDIT_TIME_OFF]:
            return self.get_legend_data(
                "credit_hour_consumed",
                hours=timesheet_info['worked_hours']
            )

        if timesheet_info["leave_type_id"]:
            return self.get_legend_data(
                timesheet_info["leave_type"],
                hours=timesheet_info['worked_hours'],
                leave_type_id=timesheet_info["leave_type_id"]
            )
        elif timesheet_info['coefficient'] == WORKDAY:
            if timesheet_info["leave_coefficient"] == NO_LEAVE:
                if timesheet_info["is_present"]:
                    return self.get_legend_data(
                        "time_registered",
                        hours=timesheet_info["worked_hours"]
                    )
                else:
                    return self.get_legend_data("absent", hours=0)
            else:
                # this case should not happen, just a fallback
                self.get_legend_data(
                    "leave",
                    hours=timesheet_info['worked_hours']
                )

        elif timesheet_info['coefficient'] == HOLIDAY:
            return self.get_legend_data(
                "holiday", hours=timesheet_info["worked_hours"]
            )
        elif timesheet_info["coefficient"] == OFFDAY:
            return self.get_legend_data("offday", hours=timesheet_info['worked_hours'])
        return {
            "legend": "",
            "color": "yellow",
            "hours": 0,
        }

    def get_selected_leave_types(self):
        if self.report_setting.id:
            return list(self.report_setting.selected_leave_types.all().values(
                'id', 'name'
            ))
        return []

    def get_worked_hours_from_timedelta(self, duration):
        if duration:
            hours = duration.seconds // (60 * 60)
            minutes = (duration.seconds // 60) - hours * 60
            limit_value = self.report_setting.worked_hours_ceil_limit

            if limit_value and minutes >= limit_value:
                hours += 1
            return hours

        return None

    def prepare_data(self, qs):
        date_data_map = {
            str(ts['timesheet_for']): {
                'is_present': ts['is_present'],
                'coefficient': ts['coefficient'],
                'leave_coefficient': ts['leave_coefficient'],
                'worked_hours': self.get_worked_hours_from_timedelta(ts['worked_hours']),
                'leave_type': ts['leave_type_name'],
                'leave_type_id': ts['leave_type_id'],
                'hour_off_coefficient': ts['hour_off_coefficient']
            }
            for ts in qs
        }
        default_data = {
            'is_present': False,
            'coefficient': None,
            'leave_coefficient': None,
            'worked_hours': 0,
            'leave_type': None,
            'leave_type_id': None,
            'hour_off_coefficient': None
        }
        months = []
        days = {}
        monthly_leave_info = dict()

        for pk, display, start_at, end_at in self.month_slots:
            months.append({"id": pk, "name": display})
            month_days = []
            leave_info = dict()
            dates = rrule.rrule(freq=rrule.DAILY, dtstart=start_at, until=end_at)
            for date in dates:
                timesheet_info = date_data_map.get(str(date.date()), default_data)
                month_days.append(self.get_days_info(timesheet_info))

                if timesheet_info["leave_type_id"]:

                    leave_detail = leave_info.get(
                        timesheet_info["leave_type_id"],
                        {
                            "balance": 0,
                            "name": timesheet_info["leave_type"],
                        }
                    )
                    if timesheet_info["leave_coefficient"] in [FIRST_HALF, SECOND_HALF]:
                        leave_detail["balance"] += 0.5
                    else:
                        leave_detail["balance"] += 1
                    leave_info[timesheet_info["leave_type_id"]] = leave_detail

            days.update({pk: month_days})
            monthly_leave_info.update({pk: leave_info})

        if self.get_selected_leave_types():
            leave_type_data = {
                str(leave_type.id): self.extra_data(leave_type)
                for leave_type in self.report_setting.selected_leave_types.all()
            }
        else:
            leave_type_data = {}

        return {
            "months": months,
            "days": days,
            "leave_info": self.prepare_leave_info_for_response(monthly_leave_info),
            "legend": self.prepare_legend_for_response(),
            "leave_legend": self.get_leave_legend(),
            "selected_leave_types": self.get_selected_leave_types(),
            "header_map": self.report_setting.headers,
            "extra_data": {
                'leave_types': leave_type_data,
                'accumulated_credit_hour_to_next_month': self.get_accumulated_credit_hour_to_next_month()
            },
            "header_data": self.get_header_data()
        }

    def get_proportionate_rate(self):
        user = self.user
        fiscal_year = self.fiscal_year
        current_experience = user.current_experience

        doj = user.detail.joined_date
        yearly_balance = 100
        balance_to_grant = yearly_balance

        if doj > fiscal_year.start_at:
            days_since_fiscal_start = (doj - fiscal_year.start_at).days

            balance_to_grant = balance_to_grant - int(
                yearly_balance / 365 * days_since_fiscal_start
            )

        if (
            current_experience and
            current_experience.end_date and
            current_experience.end_date < fiscal_year.end_at
        ):
            days_to_end = (
                fiscal_year.end_at - current_experience.end_date
            ).days

            balance_to_grant = balance_to_grant - int(
                yearly_balance / 365 * days_to_end
            )

        return balance_to_grant

    def get_header_data(self):
        user = self.user
        current_experience = self.user.current_experience
        bio_user_id = ', '.join(set(
            AttendanceUserMap.objects.filter(
                setting__user=user
            ).values_list('bio_user_id', flat=True))
        )

        start_date = getattr(current_experience, 'start_date', None)
        end_date = getattr(current_experience, 'end_date', None)

        start_date = str(start_date) if start_date else None
        end_date = str(end_date) if end_date else None

        data = {
            'report_title': self.report_setting.headers.get('report_title', 'Timesheet Report'),
            'full_name': user.full_name,
            'employee_code': user.detail.code,
            'employment_type': getattr(user.detail.employment_status, 'title', 'N/A'),
            'division': getattr(user.detail.division, 'name', 'N/A'),
            'job_title': getattr(user.detail.job_title, 'title', 'N/A'),
            'branch': getattr(user.detail.branch, 'name', 'N/A'),
            'contract_start': start_date,
            'contract_end': end_date,
            'bio_user_id': bio_user_id,
            'proportionate_rate': self.get_proportionate_rate()
        }

        return data

    def get_leave_legend(self):
        legend = [
            {
                "id": int(k),
                "letter": v["legend"],
                "text": v["name"],
                "color": v["color"]
            } for k, v in self.leave_legend.items()
        ]
        for item in self.get_selected_leave_types():
            if str(item["id"]) not in self.leave_legend:
                legend.append({
                    "id": item["id"],
                    "letter": "L",
                    "text": item["name"],
                    "color": self.default_leave_legend["color"]
                })
        return legend

    def get_accumulated_credit_hour_to_next_month(self):
        month_end = self._fiscal_month.end_at if self._fiscal_month else self.fiscal_year.end_at

        latest_history = LeaveAccountHistory.objects.filter(
            created_at__date__lte=month_end,
            account__user=self.user,
            account__rule__leave_type__category=CREDIT_HOUR
        ).order_by('-created_at').first()

        return getattr(latest_history, 'new_balance', 0)

    def prepare_legend_for_response(self):
        return [
           {
               "letter": v["legend"],
               "text": v.get("text", k),
               "color": v["color"]
           } for k, v in self.legend.items()
        ] + [
            {
                "letter": v["legend"],
                "text": v["name"],
                "color": v["color"]
            } for v in self.leave_legend.values()
        ]

    @staticmethod
    def prepare_leave_info_for_response(monthly_leave_info):
        return {
            month: [
                dict(id=int(leave_id), **data_dict)
                for leave_id, data_dict in leaves.items()
            ]
            for month, leaves in monthly_leave_info.items()
        }

    @staticmethod
    def prepare_queryset(qs):
        return qs.annotate(
            leave_type_id=Subquery(
                LeaveSheet.objects.filter(
                    request__user_id=OuterRef('timesheet_user_id'),
                    request__status=APPROVED,
                    leave_for=OuterRef('timesheet_for')
                ).exclude(
                    request__is_deleted=True
                ).values('request__leave_rule__leave_type_id')[:1]
            )
        ).annotate(
            leave_type_name=Subquery(
                LeaveType.objects.filter(
                    id=OuterRef('leave_type_id')
                ).values('name')[:1]
            )
        ).values(
            "timesheet_for",
            "is_present",
            "coefficient",
            "leave_coefficient",
            "hour_off_coefficient",
            "worked_hours",
            "leave_type_name",
            "leave_type_id"
        )

    def get_report_data(self):
        return self.prepare_data(self.prepare_queryset(self.queryset))

    @staticmethod
    def get_renewal_info(date_range_histories):
        proportionate_history = date_range_histories.filter(
            remarks='Proportionate Leave by the System',
            actor=get_system_admin()
        ).first()
        if proportionate_history:
            entitled_this_year = proportionate_history.new_balance
            carry_forwarded_from_previous_year = 0
        else:
            first_renewed_history = date_range_histories.filter(renewed__isnull=False).first()
            if first_renewed_history:
                entitled_this_year = first_renewed_history.renewed
                carry_forwarded_from_previous_year = first_renewed_history.carry_forward
            else:
                # if no renew was found, take balance as start of year as carry forwarded
                # from previous year
                first_history = date_range_histories.first()
                if first_history:
                    entitled_this_year = 0
                    carry_forwarded_from_previous_year = first_history.previous_balance
                else:
                    entitled_this_year = 0
                    carry_forwarded_from_previous_year = 0
        return entitled_this_year, carry_forwarded_from_previous_year

    @staticmethod
    def get_balance_consumed(leave_account, start_date, end_date):
        return LeaveSheet.objects.filter(
            request__status=APPROVED,
            request__leave_account=leave_account,
            leave_for__range=[start_date, end_date],
            request__is_deleted=False
        ).aggregate(
            sum=Sum('balance'),
        ).get('sum') or 0

    @staticmethod
    def get_balance_till_date(leave_account, till_date):
        recent_history = leave_account.history.filter(
            created_at__date__lte=till_date
        ).order_by('-created_at').first()
        return getattr(recent_history, 'new_balance', 0)

    def extra_data(self, leave_type):
        fiscal_year = self.fiscal_year

        leave_account = LeaveAccount.objects.filter(
            user=self.user,
            rule__leave_type=leave_type
            # archived filter is missing
        ).first()

        if not leave_account:
            return {
                "carry_forwarded_from_previous_year": 0,
                "entitled_this_year": 0,
                "balance_consumed": 0,
                "balance_till_date": 0,
                "collapsible_balance": 0
            }

        date_range_histories = leave_account.history.filter(
            created_at__date__range=(fiscal_year.start_at, fiscal_year.end_at),
        ).order_by('created_at')

        entitled_this_year, carry_forwarded_from_previous_year = self.get_renewal_info(
            date_range_histories
        )
        balance_consumed = self.get_balance_consumed(
            leave_account, fiscal_year.start_at, fiscal_year.end_at
        )
        balance_till_date = self.get_balance_till_date(leave_account, fiscal_year.end_at)

        renewal_rule = getattr(leave_account.rule, 'renewal_rule', None)
        if not renewal_rule:
            collapsible_balance = 0

        else:
            carry_forward_limit = renewal_rule.max_balance_forwarded or 0
            encashment_limit = renewal_rule.max_balance_encashed or 0
            collapsible_balance = balance_till_date - carry_forward_limit - encashment_limit
            if collapsible_balance < 0:
                collapsible_balance = 0

        return {
            "carry_forwarded_from_previous_year": carry_forwarded_from_previous_year,
            "entitled_this_year": entitled_this_year,
            "balance_consumed": balance_consumed,
            "balance_till_date": balance_till_date,
            "collapsible_balance": collapsible_balance
        }


def generate_timesheet_report_of_user(user, fiscal_month, report_settings):
    report = TimeSheetReport(
        user,
        fiscal_year=fiscal_month.fiscal_year,
        fiscal_month=fiscal_month,
        report_setting=report_settings
    )

    return report.get_report_data()


def save_timesheet_report(report_data, user, fiscal_month, report_settings):
    instance = TimeSheetReportRequest.objects.create(
        user=user,
        status=GENERATED,
        recipient=None,  # for generated status, recipient is None,
        report_data=report_data,
        settings_data=TimeSheetRegistrationReportSettingsSerializer(instance=report_settings).data,
        fiscal_month=fiscal_month,
        month_name=fiscal_month.display_name,
        month_from_date=fiscal_month.start_at,
        month_to_date=fiscal_month.end_at,
        year_name=fiscal_month.fiscal_year.name,
        year_from_date=fiscal_month.fiscal_year.start_at,
        year_to_date=fiscal_month.fiscal_year.end_at
    )

    TimeSheetReportRequestHistory.objects.create(
        request=instance,
        actor=get_system_admin(),
        action=GENERATED,
        action_to=user,
        remarks=f'Generated timesheet report on {get_today()}.'
    )

    return instance


def update_timesheet_report(instance, report_data, actor, remarks):
    instance.status = GENERATED
    instance.recipient = None
    instance.report_data = report_data
    instance.save()

    TimeSheetReportRequestHistory.objects.create(
        request=instance,
        actor=actor,
        action=GENERATED,
        action_to=instance.user,
        remarks=remarks or f'Regenerated timesheet report on {get_today()}.'
    )

    return instance
