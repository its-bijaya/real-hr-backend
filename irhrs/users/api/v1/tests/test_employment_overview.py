from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Sum, Case, When, DurationField, F, IntegerField, Count, Avg, \
    FloatField, Q
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from faker import Factory
from rest_framework import status
from rest_framework.test import APIClient

from irhrs.attendance.api.v1.tests.factory import WorkShiftFactory2, \
    IndividualAttendanceSettingFactory, OvertimeSettingFactory
from irhrs.attendance.constants import PUNCH_IN, PUNCH_OUT, DAILY, WORKDAY, NO_LEAVE, UNCLAIMED
from irhrs.attendance.managers.utils import fix_entries_on_commit
from irhrs.attendance.tasks.overtime import generate_overtime
from irhrs.attendance.models import IndividualUserShift, TimeSheet, OvertimeClaim, WorkDay
from irhrs.common.api.tests.common import TestCaseValidateData
from irhrs.core.constants.user import MALE
from irhrs.core.utils.common import get_today, get_yesterday
from irhrs.hris.api.v1.tests.factory import ChangeTypeFactory
from irhrs.leave.api.v1.tests.factory import MasterSettingFactory, LeaveTypeFactory, \
    LeaveAccountFactory, LeaveRuleFactory
from irhrs.leave.constants.model_constants import LEAVE_TYPE_CATEGORIES, FULL_DAY, APPROVED, \
    FIRST_HALF
from irhrs.leave.models import LeaveAccount, LeaveRequest
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory, \
    EmploymentStatusFactory, EmploymentJobTitleFactory, EmploymentLevelFactory, \
    FiscalYearFactory, OrganizationDivisionFactory
from irhrs.organization.models import FiscalYear, EmploymentStatus
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import ATTENDANCE_REPORTS_PERMISSION, ATTENDANCE_PERMISSION, \
    USER_PROFILE_PERMISSION
from irhrs.permission.models import HRSPermission
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from irhrs.task.constants import TASK_STATUSES_CHOICES, COMPLETED, RESPONSIBLE_PERSON, ON_HOLD, \
    PENDING, IN_PROGRESS, CLOSED
from irhrs.task.models import Task
from irhrs.task.models.ra_and_core_tasks import ResultArea, CoreTask, UserResultArea
from irhrs.task.models.task import TaskAssociation
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserExperience, UserDetail


def fix_entries_immediately(self):
    fix_entries_on_commit(self)


class EmploymentOverviewTestCase(TestCaseValidateData):
    client = APIClient()
    fake = Factory.create()
    experience_url = 'api_v1:users:experience-history-list'

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        super().setUp()
        self.users = [UserFactory()]
        self.user = get_user_model()
        self.client.force_login(self.users[0])
        self.user_check = self.users[0]
        group, _ = Group.objects.update_or_create(name=ADMIN)
        self.user_check.groups.add(group)
        org_group, _ = OrganizationGroup.objects.update_or_create(
            organization=self.user_check.detail.organization,
            group=group
        )
        for perm in [
            USER_PROFILE_PERMISSION,
            ATTENDANCE_PERMISSION,
            ATTENDANCE_REPORTS_PERMISSION
        ]:
            perm, _ = HRSPermission.objects.update_or_create(**perm)
            org_group.permissions.add(perm)

        self.organization = self.user_check.detail.organization

    def test_task_details(self):
        """
        test task details of user,
        test covers the total , pending, in progress , completed , closed and on hold task assigned
        to user
        """
        org_branch = OrganizationBranchFactory(organization=self.organization)
        org_division = OrganizationDivisionFactory(organization=self.organization)
        change_type = ChangeTypeFactory(organization=self.organization)
        employment_status = EmploymentStatus.objects.create(
            title=self.fake.text(max_nb_chars=150),
            organization=self.organization,
            description=self.fake.text(max_nb_chars=500)
        )
        # create current experience of users
        user_experience = self.user_check.current_experience
        user_experience.branch = org_branch
        user_experience.employment_status = employment_status
        user_experience.change_type = change_type
        user_experience.save()

        # create result area and core task and assign it to user
        result_area = ResultArea.objects.create(
            title=self.fake.name(),
            division=self.organization.divisions.first()
        )
        core_task = CoreTask.objects.create(
            result_area=result_area,
            title=self.fake.name()
        )
        user_result_area = UserResultArea.objects.create(
            user_experience=self.user_check.current_experience,
            result_area=result_area,
        )
        user_result_area.core_tasks.add(core_task)

        # create users to assign task
        users = self.create_users()
        # create fiscal year
        FiscalYearFactory(organization=self.organization,
                          start_at=timezone.now().date() - relativedelta(days=7),
                          end_at=timezone.now().date() + relativedelta(days=5),
                          applicable_from=timezone.now().date() - relativedelta(days=7),
                          applicable_to=timezone.now().date() + relativedelta(days=5))

        # now create task and assign it to user
        task_create_list = list()
        task_create_list.append({
            'title': self.fake.name(),
            'created_by': users[0],
            'created_at': timezone.now() - relativedelta(days=9),
            'starts_at': timezone.now() - relativedelta(days=8),  # test starts at to earlier
            # than fiscal year
            'deadline': timezone.now() + relativedelta(days=1),
            'start': timezone.now() - relativedelta(days=2),
            'finish': timezone.now() - relativedelta(days=1),
            'status': COMPLETED
        })
        for index, task_status in enumerate(TASK_STATUSES_CHOICES):
            task_create_list.append({
                'title': self.fake.name(),
                'created_by': users[0],
                'created_at': timezone.now() - relativedelta(days=index + 1),
                'starts_at': timezone.now() - relativedelta(days=index),
                'deadline': timezone.now() + relativedelta(days=index),
                'start': timezone.now() - relativedelta(days=index),
                'finish': timezone.now() + relativedelta(days=index + 2),
                'status': task_status[0]
            })
        task_created = Task.objects.bulk_create([Task(**data) for data in task_create_list])

        # create task association
        task_association_list = list()
        for task in task_created:
            task_association_list.append({
                'created_by': users[0],
                'user': self.user_check,
                'association': RESPONSIBLE_PERSON,
                'task': task
            })
        TaskAssociation.objects.bulk_create([
            TaskAssociation(**data) for data in task_association_list])

        # get response form task detail url
        response = self.client.get(reverse('api_v1:task:task-detail',
                                           kwargs={
                                               'user_id': self.user_check.id,
                                           }))

        # now we get data from database
        fiscal_year = FiscalYear.objects.current(
            organization=self.user_check.detail.organization)

        agg_data = TaskAssociation.objects.filter(
            user=self.user_check, association=RESPONSIBLE_PERSON,
            task__starts_at__date__gte=fiscal_year.applicable_from,
            task__deadline__date__lte=fiscal_year.applicable_to
        ).aggregate(
            all_tasks=Count('id', distinct=True),

            pending=Count(
                'id',
                filter=Q(task__status=PENDING),
                distinct=True
            ),
            in_progress=Count(
                'id',
                filter=Q(task__status=IN_PROGRESS),
                distinct=True
            ),
            completed=Count(
                'id',
                filter=Q(task__status=COMPLETED),
                distinct=True
            ),
            closed_and_hold=Count(
                'id',
                filter=Q(Q(task__status=CLOSED) | Q(task__status=ON_HOLD)),
                distinct=True
            ),
            efficiency=Avg(
                'efficiency',
                filter=Q(efficiency__isnull=False)
            ),
            total_score=Sum(
                'taskverificationscore__score',
                filter=Q(taskverificationscore__ack=True)
            ),
            average_score=Avg(
                'taskverificationscore__score',
                filter=Q(taskverificationscore__ack=True),
                output_field=FloatField()
            ),
        )
        user_ra = UserResultArea.objects.filter(
            user_experience__user=self.user_check).distinct().values_list(
            'result_area__title',
            flat=True)
        result_area = {}
        for _result_area in user_ra:
            task_association = TaskAssociation.objects.filter(
                user=self.user_check, association=RESPONSIBLE_PERSON,
                task__starts_at__date__gte=fiscal_year.applicable_from,
                task__deadline__date__lte=fiscal_year.applicable_to,
                efficiency__isnull=False
            ).aggregate(
                avg_data=Avg('efficiency',
                             filter=Q(core_tasks__result_area__title=_result_area)))
            if task_association['avg_data']:
                result_area[_result_area] = task_association['avg_data']

        sorted_result_area = dict(
            sorted(result_area.items(), key=lambda x: x[1], reverse=True)[:5])

        agg_data['result_area_efficiency'] = sorted_result_area

        # test data from database is equal to data from response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), agg_data)

    def create_users(self):
        count = 50
        names = set()
        while len(names) < 50:
            names.add(self.fake.first_name())
        users = self.user.objects.bulk_create([self.user(
                first_name=name,
                last_name=name,
                email=f'{name}@gmail.com'
            ) for name in names])
        UserDetail.objects.bulk_create([
            UserDetail(
                user=user,
                gender=MALE,
                date_of_birth='2000-01-01',
                organization=self.organization
            ) for user in users
        ])
        return users

    def test_attendance_details(self):
        """
        test covers the individual attendance details in user profile
        """
        FiscalYearFactory(organization=self.organization,
                          start_at=timezone.now().date() - relativedelta(days=5),
                          end_at=timezone.now().date(),
                          applicable_from=timezone.now().date() - relativedelta(days=5),
                          applicable_to=timezone.now().date())

        # here we create user shift, ot(over time), late in and absent data
        self.create_individual_user_shift()
        self.generate_ot()
        self.generate_late_in()
        self.generate_absent()
        punch_in = timezone.now().astimezone().replace(hour=9, minute=0)
        punch_out = timezone.now().astimezone().replace(hour=18, minute=0)
        self.make_attendance(punch_in=punch_in - relativedelta(days=3),
                             punch_out=punch_out - relativedelta(days=3))
        punch_in = timezone.now().astimezone().replace(hour=9, minute=0)
        punch_out = timezone.now().astimezone().replace(hour=18, minute=0)

        self.make_attendance(punch_in- relativedelta(days=4),
                             punch_out - relativedelta(days=4))
        punch_in = timezone.now().astimezone().replace(hour=9, minute=0)
        punch_out = timezone.now().astimezone().replace(hour=18, minute=0)
        self.make_attendance(punch_in - relativedelta(days=6),
                             punch_out - relativedelta(days=6))

        # get attendance detail response of individual user from url
        response = self.client.get(reverse('api_v1:attendance:user-overview-detail',
                                           kwargs={
                                               'user_id': self.user_check.id,
                                               'organization_slug': self.organization.slug,
                                           }), data={
            'fiscal_year': 'current'
        })

        fiscal_year = FiscalYear.objects.current(
            organization=self.organization)

        # get details from database
        time_sheet_db = TimeSheet.objects.filter(timesheet_user=self.user_check,
                                                 timesheet_for__gte=fiscal_year.applicable_from,
                                                 timesheet_for__lte=fiscal_year.applicable_to
                                                 ).aggregate(
            total_worked=Coalesce(Sum(
                F('worked_hours'),
            ), timezone.timedelta(0)),
            expected_work=Coalesce(Sum(
                Case(
                    When(
                        expected_punch_in__isnull=False,
                        expected_punch_out__isnull=False,
                        coefficient=WORKDAY,
                        then=F('work_time__working_minutes')
                    ),
                    default=0,
                    output_field=IntegerField()
                )
            ), 0),
            absent_days=Count('id',
                              filter=Q(is_present=False, coefficient=WORKDAY,
                                       leave_coefficient=NO_LEAVE)),
            present_days=Count('id', filter=Q(is_present=True)),
            working_days=Count('id', filter=Q(coefficient=WORKDAY)),
            punctuality=Avg(
                Coalesce(F('punctuality'), 0),
                filter=Q(coefficient=WORKDAY, leave_coefficient=NO_LEAVE),
                output_field=FloatField()
            ),
            overtime_claimed=Sum(
                'overtime__overtime_detail__claimed_overtime',
                filter=~Q(overtime__claim__status=UNCLAIMED),
                output_field=DurationField()
            )
        )

        # calculate and arrange in dictionary
        response_db = {
            'total_lost_minutes': time_sheet_db["expected_work"] - (
                time_sheet_db['total_worked'].total_seconds() // 60),
            'expected_minutes': time_sheet_db['expected_work'],
            'total_worked_minutes': time_sheet_db[
                                        'total_worked'].total_seconds() // 60,
            'absent_days': time_sheet_db['absent_days'],
            'present_days': time_sheet_db['present_days'],
            'working_days': time_sheet_db['working_days'],
            'punctuality': round(time_sheet_db['punctuality'] or 0.0, 2),
            'overtime_claimed': time_sheet_db['overtime_claimed'].total_seconds() // 60 if
            time_sheet_db['overtime_claimed'] else 0
        }

        # test response from url is equal to database value
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.validate_data([response.json()], [response_db])

    def create_individual_user_shift(self):

        ius = IndividualUserShift.objects.create(
            individual_setting=IndividualAttendanceSettingFactory(
                user=self.user_check,
                enable_overtime=True,
                overtime_setting=OvertimeSettingFactory(organization=self.organization)
            ),
            shift=WorkShiftFactory2(work_days=6, organization=self.organization),
            applicable_from=timezone.now() - timezone.timedelta(days=6)
        )
        WorkDay.objects.filter(shift=ius.shift).update(applicable_from=ius.applicable_from)

    def generate_ot(self):
        self.make_attendance(
            punch_in=get_today(with_time=True).replace(
                hour=7,
                minute=0
            ),
            punch_out=get_today(with_time=True).replace(
                hour=20,
                minute=0
            ),
        )
        generate_overtime(
            timezone.now().date() - timezone.timedelta(days=4),
            timezone.now().date(),
            DAILY
        )
        overtime_claim = OvertimeClaim.objects.get(recipient=self.user_check)
        overtime_claim.status = APPROVED
        overtime_claim.save()

    def generate_late_in(self):
        self.make_attendance(
            punch_in=get_yesterday(with_time=True).replace(
                hour=11,
                minute=0
            ),
            punch_out=get_yesterday(with_time=True).replace(
                hour=18,
                minute=0
            ),
        )

    def generate_absent(self):
        time_sheet = TimeSheet(
            timesheet_user=self.user_check,
            timesheet_for=timezone.now().date() - timezone.timedelta(days=2),
        )
        time_sheet.save()

    def make_attendance(self, punch_in, punch_out):
        with patch(
            'irhrs.attendance.models.attendance.TimeSheet.fix_entries',
            fix_entries_immediately
        ):
            # for punch in
            TimeSheet.objects.clock(
                user=self.user_check,
                date_time=punch_in,
                entry_method='Web App',
                entry_type=PUNCH_IN
            )

            # for punch out
            TimeSheet.objects.clock(
                user=self.user_check,
                date_time=punch_out,
                entry_method='Web App',
                entry_type=PUNCH_OUT
            )

    def test_leave_details(self):
        """
        test leave details of user
        """
        master_setting = MasterSettingFactory(organization=self.organization,
                                              half_shift_leave=True,
                                              compensatory=True
                                              )
        FiscalYearFactory(organization=self.organization)

        # create four different leave type on the basis of category and send leave request
        data = []
        for index, leave_type_constant in enumerate(LEAVE_TYPE_CATEGORIES):
            leave_type = LeaveTypeFactory(master_setting=master_setting,
                                          category=leave_type_constant[0],
                                          )
            leave_rule = LeaveRuleFactory(leave_type=leave_type,
                                          employee_can_apply=True,
                                          can_apply_half_shift=True,
                                          )
            leave_account = LeaveAccountFactory(user=self.user_check,
                                                rule=leave_rule,
                                                )
            if index == 0:
                data.append({
                    'user': self.user_check,
                    'balance': 0.5,
                    'start': timezone.now() - relativedelta(days=index),
                    'end': timezone.now() - relativedelta(days=index),
                    'part_of_day': FIRST_HALF,
                    'leave_account': leave_account,
                    'leave_rule': leave_rule,
                    'status': APPROVED,
                    'details': self.fake.text(max_nb_chars=500),
                })
            else:
                data.append({
                    'user': self.user_check,
                    'balance': 1,
                    'start': timezone.now() - relativedelta(days=index),
                    'end': timezone.now() - relativedelta(days=index),
                    'part_of_day': FULL_DAY,
                    'leave_account': leave_account,
                    'leave_rule': leave_rule,
                    'status': APPROVED,
                    'details': self.fake.text(max_nb_chars=500),
                })
        LeaveRequest.objects.bulk_create(
                [
                    LeaveRequest(**leave) for leave in data
                ]
            )

        # get leave details from database on the basis of fiscal year
        fiscal_year = FiscalYear.objects.current(
            organization=self.organization)
        leave_db = LeaveAccount.objects.filter(user=self.user_check).annotate(
            consumed_balance=Sum('leave_requests__balance', filter=Q(
                leave_requests__start__date__gte=fiscal_year.applicable_from,
                leave_requests__end__date__lte=fiscal_year.applicable_to,
                leave_requests__status='Approved'))).filter(
            consumed_balance__isnull=False)

        # get leave detail response of individual user from url
        response = self.client.get(reverse('api_v1:leave:leave-employee-profile-list',
                                           kwargs={
                                               'user_id': self.user_check.id
                                           }))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test response from url is equal to database value
        self.validate_data(
            results=response.json().get('results'),
            data=leave_db
        )

    def test_employment_history(self):
        """
        test employment history of user
        """
        user_detail = self.user_check.detail
        user_detail.joined_date = timezone.now().date() - relativedelta(months=4)
        user_detail.save()

        # create employment history of user
        data = []
        for create_user_experience in range(1, 3):
            org_branch = OrganizationBranchFactory(organization=self.organization)
            change_type = ChangeTypeFactory(organization=self.organization)
            employment_status = EmploymentStatusFactory(organization=self.organization)
            job_title = EmploymentJobTitleFactory(organization=self.organization)
            employee_level = EmploymentLevelFactory(organization=self.organization,
                                                    order_field=create_user_experience)
            data.append(
                {
                    "user": self.user_check,
                    "job_title": job_title,
                    "organization": self.organization,
                    "employee_level": employee_level,
                    "branch": org_branch,
                    "change_type": change_type,
                    "employment_status": employment_status,
                    "is_current": False,
                    "start_date": timezone.now().date() - relativedelta(
                        months=create_user_experience *
                               2),
                    "end_date": timezone.now().date() - relativedelta(
                        months=create_user_experience),
                    "job_description": self.fake.text(max_nb_chars=500),
                    "objective": self.fake.text(max_nb_chars=500),
                    "current_step": create_user_experience
                }
            )
        UserExperience.objects.bulk_create([UserExperience(**experiences) for experiences in
                                            data])

        # get experience history from database
        experience_history = UserExperience.objects.filter(upcoming=False, user=self.user_check)

        # get response form url
        response = self.client.get(reverse(self.experience_url,
                                           kwargs={
                                               'user_id': self.user_check.id
                                           }))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # here we change the database value into the format of response so we can compare
        experience_history_list = []

        for i in range(experience_history.count()):
            try:
                pre_emp_level = experience_history[i + 1].employee_level
                pre_step = experience_history[i + 1].current_step
            except IndexError:
                experience_history_list.append({
                    'start_date': self.user_check.detail.joined_date,
                    'text': f'As {experience_history[i].employee_level.title}',
                    'change_type': 'Joined'
                })
                continue

            cur_emp_level = experience_history[i].employee_level
            cur_step = experience_history[i].current_step

            # if pre_step and pre_emp_level:
            text = f'To {cur_emp_level.title if cur_emp_level else "N/A"} From {pre_emp_level.title if pre_emp_level else "N/A"}' \
                if not pre_emp_level == cur_emp_level else \
                f'To Step {cur_step if cur_step else "N/A"} From Step {pre_step if pre_step else "N/A"}'

            experience_history_list.append({
                'start_date': experience_history[i].start_date,
                'text': text,
                'change_type': experience_history[i].change_type if experience_history[
                    i].change_type else 'Updated'
            })

        # test response from url is equal to database value
        self.validate_data(
            results=response.json().get('results'),
            data=experience_history_list
        )
