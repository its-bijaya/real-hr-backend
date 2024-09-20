import math
from datetime import timedelta, date

from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Exists, OuterRef, Subquery, Case, When, F, Q, ExpressionWrapper, \
    Value, Sum, Count
from django.db.models.functions import Coalesce, TruncDate, Cast, Concat
from django.utils.functional import cached_property

from irhrs.attendance.constants import BREAK_IN, BREAK_OUT, LATE_IN, EARLY_OUT, DAYS, FREQUENCY, \
    DURATION, GENERATED, P_DAYS
from irhrs.attendance.models import TimeSheetEntry, TimeSheet, BreakOutPenaltySetting, \
    BreakOutReportView, IndividualAttendanceSetting
from irhrs.attendance.models.breakout_penalty import TimeSheetUserPenalty, \
    TimeSheetUserPenaltyStatusHistory, TimeSheetPenaltyToPayroll
from irhrs.attendance.tasks.breakout_penalty import refresh_break_out_report_view
from irhrs.core.constants.organization import LEAVE_DEDUCTION_ON_PENALTY
from irhrs.core.utils import grouper, get_system_admin
from irhrs.core.utils.common import format_timezone
from irhrs.core.utils.dependency import get_dependency
from irhrs.core.utils.email import send_email_as_per_settings
from irhrs.leave.constants.model_constants import ADDED, DEDUCTED
from irhrs.leave.models import LeaveAccountHistory
from irhrs.leave.models.request import LeaveSheet, LeaveRequest
from irhrs.notification.utils import notify_organization
from irhrs.organization.models import FiscalYearMonth, FiscalYear, get_today
from irhrs.attendance.utils.attendance import humanize_interval
from irhrs.permission.constants.permissions import ATTENDANCE_BREAK_OUT_PENALTY_PERMISSION

USER = get_user_model()
get_last_payroll_generated_date, payroll_installed = get_dependency(
    'irhrs.payroll.utils.helpers.get_last_payroll_generated_date'
)


def make_key(head, toe, rule):
    return "%s|%s|%s" % (head, toe, rule)


class BreakoutReport:
    def __init__(self, user, fiscal_month):  # date_start: payroll_generated_date, date_until: yesterday
        self.user = user
        self.organization = user.detail.organization
        self.start_date = fiscal_month.start_at
        self.end_date = fiscal_month.end_at
        self.fiscal_month = fiscal_month
        self.setting = self.organization.break_out_penalty_settings.first()

    @cached_property
    def date_iterators(self):
        # if not self.fiscal_months:
        #     return [
        #         list(
        #             map(
        #                 lambda dt: dt.date(),
        #                 rrule(
        #                     freq=DAILY,
        #                     dtstart=self.start_date,
        #                     until=self.end_date
        #                 )
        #             )
        #         )
        #     ]
        # iterators = list()
        # if start_date < fym start date,
        # first_month = self.fiscal_month
        # if self.start_date < first_month[0]:
        #     iterators.append(
        #         list(
        #             map(
        #                 lambda dt: dt.date(),
        #                 rrule(
        #                     freq=DAILY,
        #                     dtstart=self.start_date,
        #                     until=first_month[0] - timedelta(1)
        #                 )
        #             )
        #         )
        #     )
        return [list(
            map(
                lambda dt: dt.date(),
                rrule(
                    freq=DAILY,
                    dtstart=self.start_date,
                    until=self.end_date
                )
            )
        )]
        # try:
        #     last_month = self.fiscal_months.pop(-1)
        #     last_month_iterator = list(
        #         map(
        #             lambda dt: dt.date(),
        #             rrule(
        #                 freq=DAILY,
        #                 dtstart=last_month[0],
        #                 until=self.end_date
        #             )
        #         )
        #     )
        # except IndexError:
        #     return iterators
        # if not self.fiscal_months:
        #     iterators.append(last_month_iterator)
        #     return iterators
        # for start_at, end_at in self.fiscal_months:
        #     iterators.append(
        #         list(
        #             map(
        #                 lambda dt: dt.date(),
        #                 rrule(
        #                     freq=DAILY,
        #                     dtstart=start_at,
        #                     until=end_at
        #                 )
        #             )
        #         )
        #     )
        # iterators.append(last_month_iterator)
        # return iterators

#     def generate_report(self):
#         # list of start/end dates.
#         # Tolerable hours matter between these groups only.
#         groups = self.group_dates()
#         penalty_aggregator = dict()
#         base = TimeSheet.objects.filter(
#             timesheet_user=self.user,
#             timesheet_for__range=(self.start_date, self.end_date)
#         ).annotate(
#             organization=F('timesheet_user__detail__organization')
#         )
#         penalty_setting = BreakOutPenaltySetting.objects.filter(
#             organization=OuterRef('organization')
#         )[:1]
#         # Late IN
#         breakout_aggregator = BreakOutReportView.objects.order_by().values(
#             'timesheet'
#         ).annotate(
#             total_sum=Sum('total_lost')
#         ).values('total_sum', 'timesheet')
#         res = base.annotate(
#             late_in_exists=Exists(
#                 TimeSheetEntry.objects.filter(
#                     timesheet_id=OuterRef('pk'),
#                     is_deleted=False
#                 ).filter(
#                     category=LATE_IN
#                 ).only('pk')
#             ),
#             early_out_exists=Exists(
#                 TimeSheetEntry.objects.filter(
#                     timesheet_id=OuterRef('pk'),
#                     is_deleted=False
#                 ).filter(
#                     category=EARLY_OUT
#                 ).only('pk')
#             ),
#             consider_late_in=Subquery(
#                 penalty_setting.values('consider_late_in')
#             ),
#             consider_early_out=Subquery(
#                 penalty_setting.values('consider_early_out')
#             ),
#             consider_in_between_breaks=Subquery(
#                 penalty_setting.values('consider_in_between_breaks')
#             ),
#         ).annotate(
#             sum_late_in=ExpressionWrapper(
#                 Case(
#                     When(
#                         Q(
#                             late_in_exists=True,
#                             consider_late_in=True
#                         ),
#                         then=Value(True)
#                     ),
#                     default=Value(False)
#                 ),
#                 output_field=models.BooleanField()
#             ),
#             sum_early_out=ExpressionWrapper(
#                 Case(
#                     When(
#                         Q(
#                             early_out_exists=True,
#                             consider_early_out=True
#                         ),
#                         then=Value(True)
#                     ),
#                     default=Value(False)
#                 ),
#                 output_field=models.BooleanField()
#             ),
#         ).annotate(
#             lost_for_the_day=Case(
#                 When(
#                    Q(sum_late_in=True, sum_early_out=True),
#                    then=ExpressionWrapper(
#                        F('punch_in_delta') - F('punch_out_delta'),
#                        output_field=models.DurationField()
#                    )
#                 ),
#                 When(
#                     Q(sum_late_in=True),
#                     then=ExpressionWrapper(
#                         F('punch_in_delta'), output_field=models.DurationField()
#                     )
#                 ),
#                 When(
#                     Q(sum_early_out=True),
#                     then=ExpressionWrapper(
#                         -F('punch_out_delta'),
#                         output_field=models.DurationField()
#                     )
#                 ),
#                 default=Value(timedelta(0))
#             )
#         ).annotate(
#             total_lost_for_the_day_temp=ExpressionWrapper(
#                 Coalesce(F('lost_for_the_day'), Value(timedelta(0)))
#                 + Coalesce(F('lost_due_to_in_between_breaks'), Value(timedelta(0)))
#                 - Coalesce(F('excused_time_off'), Value(timedelta(0))),
#                 output_field=models.DurationField()
#             )
#         ).annotate(
#             # This will prevent us from taking excuse of one day to another.
#             total_lost_for_the_day=Case(
#                 When(
#                     Q(total_lost_for_the_day_temp__gt=Value(timedelta(0))),
#                     then=F('total_lost_for_the_day_temp')
#                 ),
#                 default=Value(timedelta(0))
#             )
#         )
#         penalty_aggregator = res.aggregate(
#             **{
#               f'{head}|{tail}': Sum('total_lost_for_the_day', filter=Q(
#                   timesheet_for__range=(head, tail)
#               )) for head, tail in groups
#             }
#         )
#         return penalty_aggregator

    def group_dates(self, rule):
        groups = list()
        penalty_counter_value = rule.penalty_counter_value
        penalty_counter_unit = rule.penalty_counter_unit
        group_into = penalty_counter_value if penalty_counter_unit == P_DAYS else None
        for date_iterator in self.date_iterators:
            if group_into:
                for each_group in grouper(date_iterator, n=group_into, fillvalue=None):
                    head = each_group[0]
                    # get last not-null value
                    tail = self.get_not_null_last_element(each_group)
                    groups.append((head, tail))
            else:
                head = date_iterator[0]
                tail = date_iterator[-1]
                groups.append((head, tail))
        return groups

    @staticmethod
    def get_not_null_last_element(iterable):
        return list(filter(
            lambda x: x,
            iterable
        ))[-1]

#     def calculate_penalty_days(self):
#         threshold = self.setting.tolerated_duration_in_minutes
#         result = dict()
#         for key, penalty in self.generate_report().items():
#             if penalty and penalty > timedelta(minutes=threshold):
#                 if self.setting.penalty_accumulates:
#                     penalty_days = math.floor(
#                         penalty.total_seconds()/threshold/60
#                     )
#                 else:
#                     penalty_days = self.setting.penalty_duration_in_days
#             else:
#                 penalty_days = 0
#             result[key] = {
#                 'accumulated': penalty,
#                 'penalty_days': penalty_days
#             }
#         return result

#     def summary(self):
#         summary = list()
#         for key, values in self.calculate_penalty_days().items():
#             start, end = key.split('|')
#             summary.append({
#                 'start_date': parse(start).date(),
#                 'end_date': parse(end).date(),
#                 'loss_accumulated': values.get('accumulated') or timedelta(0),
#                 'penalty_accumulated': values.get('penalty_days') or 0,
#             })
#         return sorted(summary, key=lambda dic: dic.get('start_date'))

    def compute_lost_penalty(self):
        penalty_aggregator = dict()
        base = TimeSheet.objects.filter(
            timesheet_user=self.user,
            timesheet_for__range=(self.start_date, self.end_date)
        ).annotate(
            organization=F('timesheet_user__detail__organization')
        ).annotate(
            is_late_in=Exists(
                TimeSheetEntry.objects.filter(
                    category=LATE_IN,
                    timesheet=OuterRef('pk')
                )
            ),
            is_early_out=Exists(
                TimeSheetEntry.objects.filter(
                    category=EARLY_OUT,
                    timesheet=OuterRef('pk')
                )
            ),
        )
        penalty_setting = IndividualAttendanceSetting.objects.filter(
            user=self.user
        ).get().penalty_setting
        if not penalty_setting:
            return penalty_aggregator
        ts_iterator = list(base)
        for rule in penalty_setting.rules.all():
            groups = self.group_dates(rule)
            tolerated_duration_in_minutes = rule.tolerated_duration_in_minutes
            tolerated_occurrences = rule.tolerated_occurrences
            consider_late_in = rule.consider_late_in
            consider_early_out = rule.consider_early_out
            consider_in_between_breaks = rule.consider_in_between_breaks
            calculation_type = rule.calculation_type
            for head, toe in groups:
                total_lost_count = 0
                total_lost_sum = 0
                for timesheet in filter(lambda ts: head <= ts.timesheet_for <= toe, ts_iterator):
                    lost_today = 0
                    if consider_late_in and timesheet.is_late_in:
                        lost_today = lost_today + abs(timesheet.punch_in_delta.total_seconds())
                    if consider_early_out and timesheet.is_early_out:
                        lost_today = lost_today + abs(timesheet.punch_out_delta.total_seconds())
                    if consider_in_between_breaks:
                        if timesheet.unpaid_break_hours:
                            lost_today = lost_today + abs(
                                timesheet.unpaid_break_hours.total_seconds()
                            )
                    if calculation_type == FREQUENCY and (
                        lost_today > (tolerated_duration_in_minutes * 60)
                    ):
                        total_lost_count = total_lost_count + 1
                        total_lost_sum = total_lost_sum + lost_today
                    if calculation_type == DURATION and lost_today > 0:
                        total_lost_count = total_lost_count + 1
                        total_lost_sum = total_lost_sum + lost_today
                if calculation_type == FREQUENCY:
                    if total_lost_count > 0 and total_lost_count >= tolerated_occurrences:
                        penalty_aggregator[make_key(head, toe, rule.id)] = {
                            'count': total_lost_count,
                            'accumulated': humanize_interval(total_lost_sum),
                            'penalty_days': rule.penalty_duration_in_days
                        }
                elif calculation_type == DURATION:
                    if total_lost_sum >= (tolerated_duration_in_minutes * 60):
                        if rule.penalty_accumulates:
                            penalty_days = math.floor(
                                total_lost_sum/(tolerated_duration_in_minutes * 60)
                            ) * rule.penalty_duration_in_days
                        else:
                            penalty_days = rule.penalty_duration_in_days
                        penalty_aggregator[make_key(head, toe, rule.id)] = {
                            'count': total_lost_count,
                            'accumulated': humanize_interval(total_lost_sum),
                            'penalty_days': penalty_days
                        }
        return penalty_aggregator


def generate_penalty_report_for_user(user, fiscal_month):
    breakout_report = BreakoutReport(user, fiscal_month)
    results = breakout_report.compute_lost_penalty()
    for key, result in results.items():
        d_start, d_end, rule_id = key.split('|')
        existing = TimeSheetUserPenalty.objects.filter(
            user=user,
            start_date=d_start,
            fiscal_month=fiscal_month,
            end_date=d_end,
            rule_id=rule_id,
        ).first()
        if existing:
            if existing.status == GENERATED:
                history = TimeSheetUserPenaltyStatusHistory(
                    break_out_user_record=existing,
                    status=GENERATED,
                    remarks='Regenerated on %s' % format_timezone(get_today(True)),
                    old_loss_accumulated=existing.loss_accumulated,
                    old_lost_days_count=existing.lost_days_count,
                    old_penalty_accumulated=existing.penalty_accumulated,
                )
                existing.loss_accumulated = result.get('accumulated')
                existing.penalty_accumulated = result.get('penalty_days')
                existing.lost_days_count = result.get('count')
                existing.save()

                # due to humanized duration, and direct duration fields, has changed wont work
                existing.refresh_from_db()

                history.new_loss_accumulated = existing.loss_accumulated
                history.new_lost_days_count = existing.lost_days_count
                history.new_penalty_accumulated = existing.penalty_accumulated
                has_changed = any([
                    getattr(history, o) != getattr(history, n)
                    for o, n in
                    (
                        ('old_loss_accumulated', 'new_loss_accumulated'),
                        ('old_lost_days_count', 'new_lost_days_count'),
                        ('old_penalty_accumulated', 'new_penalty_accumulated'),
                    )
                ])
                if has_changed:
                    history.save()
        else:
            instance = TimeSheetUserPenalty.objects.create(
                user=user,
                rule_id=rule_id,
                start_date=d_start,
                fiscal_month=fiscal_month,
                end_date=d_end,
                loss_accumulated=result.get('accumulated'),
                penalty_accumulated=result.get('penalty_days'),
                lost_days_count=result.get('count'),
            )
            TimeSheetUserPenaltyStatusHistory.objects.create(
                break_out_user_record=instance,
                status=GENERATED,
                remarks='Generated on %s' % format_timezone(instance.created_at),
                old_loss_accumulated=timedelta(0),
                new_loss_accumulated=instance.loss_accumulated,
                old_lost_days_count=0,
                new_lost_days_count=instance.lost_days_count,
                old_penalty_accumulated=0,
                new_penalty_accumulated=instance.penalty_accumulated
            )


def generate_penalty_report(organization, fiscal_month):
    # fiscal month is a wrapper for Breakout's start and end dates.
    for user in get_user_model().objects.filter(
        detail__organization=organization
    ).current():
        generate_penalty_report_for_user(user, fiscal_month)
    frontend_penalty_report_url = '/admin/%s/attendance/penalty' % organization.slug
    notify_organization(
        text="The timesheet Penalty report for `%s` has been generated."
             % fiscal_month.display_name,
        action=organization,
        url=frontend_penalty_report_url,
        permissions=[
            ATTENDANCE_BREAK_OUT_PENALTY_PERMISSION
        ],
        organization=organization
    )


def get_leave_account(user, leave_type):
    return user.leave_accounts.filter(
        #rule__leave_type__master_setting__in=MasterSetting.objects.filter().active_for_organization
    ).filter(
        rule__leave_type=leave_type,
        is_archived=False
    ).first()


def update_leave_balance(leave_account, difference=0, remarks=''):
    leave_account.refresh_from_db()
    new_balance = leave_account.balance + difference
    new_usable = leave_account.usable_balance + difference
    account_history = LeaveAccountHistory(
        account=leave_account,
        user=leave_account.user,
        actor=get_system_admin(),
        action=ADDED if difference > 0 else DEDUCTED,
        previous_balance=leave_account.balance,
        previous_usable_balance=leave_account.usable_balance,
        new_balance=new_balance,
        new_usable_balance=new_usable,
        remarks=remarks
    )
    leave_account.balance = new_balance
    leave_account.usable_balance = new_usable
    account_history.save()
    leave_account.save()


def reduce_penalty_from_leave(penalty_report):
    to_reduce = penalty_report.penalty_accumulated
    leave_types_to_reduce = penalty_report.rule.penalty_setting.leave_types_to_reduce.all()
    for _leave_type in leave_types_to_reduce:
        leave_type = _leave_type.leave_type_to_reduce
        if to_reduce == 0:
            break
        account = get_leave_account(penalty_report.user, leave_type)
        if account and account.usable_balance > 0:
            deletable = min(account.usable_balance, to_reduce)
            update_leave_balance(
                account,
                -deletable,
                remarks='Reduce %.2f balance from %s' % (deletable, account.rule.leave_type.name)
            )
            send_email_as_per_settings(
                recipients=[penalty_report.user],
                subject="Leave balance is deducted due to penalty",
                email_text=(
                    f'Your Leave balance for {leave_type.name} has decremented by {deletable} '
                    f'due to penalty.'
                ),
                email_type=LEAVE_DEDUCTION_ON_PENALTY
            )
            if not account.rule.is_paid:
                TimeSheetPenaltyToPayroll.objects.create(
                    user_penalty=penalty_report,
                    confirmed_on=get_today(with_time=True),
                    days=deletable
                )
            to_reduce = to_reduce - deletable
    if to_reduce > 0:
        TimeSheetPenaltyToPayroll.objects.create(
            user_penalty=penalty_report,
            confirmed_on=get_today(with_time=True),
            days=to_reduce
        )
