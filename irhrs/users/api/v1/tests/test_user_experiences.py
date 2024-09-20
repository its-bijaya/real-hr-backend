import functools
import json
from datetime import date
from unittest import mock

from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from faker import Factory

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience, RHRSAPITestCase
from irhrs.hris.api.v1.tests.factory import ChangeTypeFactory
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory, \
    EmploymentStatusFactory, EmploymentJobTitleFactory, OrganizationDivisionFactory, \
    EmploymentLevelFactory
from irhrs.users.models import UserExperience


User = get_user_model()


class UserExperienceTestCase(RHRSTestCaseWithExperience):
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('hello@hello.com', 'secretThing', 'Male', 'Clerk'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()

    experience_url = 'api_v1:users:user-experience-list'

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        super().setUp()
        self.user = get_user_model()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        # get user object
        self.user_check = self.user.objects.get(email=self.users[0][0])
        self.user_hello = self.user.objects.get(email=self.users[1][0])

    def test_user_experience(self):
        """
        test scenario
         Test list api and detail api of test experience.
         First user current experience is created and tested whether all the data is correct or
         not.
         A user can have any number of experiences so we will create in bulk and count the
         number of experiences.
         Here normal user cannot view his/her upcoming experience, so we have created a upcoming
         experience and assured that it is not in the list.
        """

        org_branch = OrganizationBranchFactory(organization=self.organization)
        change_type = ChangeTypeFactory(organization=self.organization)
        employment_status = EmploymentStatusFactory(organization=self.organization)

        # update user current experience information
        user_experience = self.user_check.current_experience
        user_experience.branch = org_branch
        user_experience.employment_status = employment_status
        user_experience.change_type = change_type
        user_experience.division = self.division
        user_experience.objective = self.fake.text(max_nb_chars=500)
        user_experience.job_description = self.fake.text(max_nb_chars=500)
        user_experience.save()

        # this is response from list api
        response = self.client.get(reverse(self.experience_url,
                                           kwargs={
                                               'user_id': self.user_check.id
                                           }))

        # test all the data is correct
        self.assertEqual(response.data.get('results')[0].get('is_current'),
                         user_experience.is_current)
        self.assertEqual(response.data.get('results')[0].get('division').get('name'),
                         user_experience.division.name)
        self.assertEqual(response.data.get('results')[0].get('branch').get('name'),
                         user_experience.branch.name)
        self.assertEqual(response.data.get('results')[0].get('user').get('id'),
                         self.user_check.id)
        self.assertEqual(response.data.get('results')[0].get('organization').get('name'),
                         self.organization.name)
        self.assertEqual(response.data.get('results')[0].get('employment_status').get('title'),
                         user_experience.employment_status.title)
        self.assertEqual(response.data.get('results')[0].get('job_title').get('title'),
                         user_experience.job_title.title)
        self.assertEqual(parse(response.data.get('results')[0].get('start_date')).date(),
                         user_experience.start_date)
        self.assertEqual(response.data.get('results')[0].get('is_current'),
                         user_experience.is_current)
        self.assertEqual(response.data.get('results')[0].get('current_step'),
                         user_experience.current_step)

        # detail experience is needed to test the objective and job description.
        response_data = self.client.get(reverse('api_v1:users:user-experience-detail',
                                                kwargs={
                                                    'user_id': self.user_check.id,
                                                    'pk': user_experience.id,
                                                }))

        # test job description and objective
        self.assertEqual(response_data.data.get('job_description'),
                         user_experience.job_description)
        self.assertEqual(response_data.data.get('objective'),
                         user_experience.objective)

        # create upcoming user experience and past user experiences
        create_bulk = list()
        for create_user_experience in range(0, 6):
            org_branch = OrganizationBranchFactory(organization=self.organization)
            change_type = ChangeTypeFactory(organization=self.organization)
            employment_status = EmploymentStatusFactory(organization=self.organization)
            job_title = EmploymentJobTitleFactory(organization=self.organization)
            if create_user_experience == 0:
                # here user experience is upcoming that might be promotion...
                create_bulk.append(UserExperience(
                    user=self.user_check,
                    job_title=job_title,
                    organization=self.organization,
                    division=self.division,
                    branch=org_branch,
                    change_type=change_type,
                    employment_status=employment_status,
                    current_step=10,
                    upcoming=True,
                    is_current=False,
                    start_date=timezone.now().date() + timezone.timedelta(days=30)
                ))
            else:
                end_days = create_user_experience * 100
                start_days = create_user_experience * 365
                create_bulk.append(UserExperience(
                    user=self.user_check,
                    job_title=job_title,
                    organization=self.organization,
                    division=self.division,
                    branch=org_branch,
                    change_type=change_type,
                    employment_status=employment_status,
                    is_current=False,
                    start_date=timezone.now().date() - timezone.timedelta(days=start_days),
                    end_date=timezone.now().date() - timezone.timedelta(days=end_days),
                    job_description=self.fake.text(max_nb_chars=500),
                    objective=self.fake.text(max_nb_chars=500),
                    current_step=create_user_experience
                ))
        UserExperience.objects.bulk_create(create_bulk)

        # database query to get the all the work experiences except the upcoming
        get_query = UserExperience.objects.filter(upcoming=False, user=self.user_check)
        response = self.client.get(reverse(self.experience_url,
                                           kwargs={
                                               'user_id': self.user_check.id
                                           }))

        # test number of  user experience is equal to response data excluding upcoming experience
        self.assertEqual(response.data.get('count'),
                         get_query.count())


class TestUserExperienceAPIValidation(RHRSAPITestCase):
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male'),
        ('hello@hello.com', 'secretThing', 'Male'),
    ]
    organization_name = "Google"
    reverse_list_url = "api_v1:users:user-experience-list"
    reverse_detail_url = "api_v1:users:user-experience-detail"

    @property
    def json_post(self) -> functools.partial:
        return functools.partial(self.client.post, content_type="application/json")

    @property
    def json_put(self) -> functools.partial:
        return functools.partial(self.client.put, content_type="application/json")

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.get(email=self.users[1][0])

        detail = self.user.detail
        detail.joined_date = timezone.now().date()
        detail.save()

        self.job_title = EmploymentJobTitleFactory(organization=self.organization)
        self.division = OrganizationDivisionFactory(organization=self.organization)
        self.employee_level = EmploymentLevelFactory(organization=self.organization)
        self.change_type = ChangeTypeFactory(organization=self.organization)

        self.client.force_login(self.admin)

    def get_url(self, experience_id: id = None, mode: str = 'hr') -> str:
        if experience_id:
            url = reverse(
                self.reverse_detail_url,
                kwargs={
                    'user_id': self.user.id,
                    'pk': experience_id
                }
            )
        else:
            url = reverse(
                self.reverse_list_url,
                kwargs={
                    'user_id': self.user.id,
                }
            )
        return f"{url}?as={mode}"

    def create_experience(
        self, user: User = None,
        start_date: date = None,
        end_date: date = None,
        joined_date: date = None
    ) -> UserExperience:
        user = user or self.user
        start_date = start_date or timezone.now().date()
        end_date = end_date
        is_current = not bool(end_date)

        detail = user.detail
        detail.joined_date = joined_date or start_date
        detail.save()

        experience = UserExperience(
            user=self.user,
            job_title=self.job_title,
            organization=self.organization,
            division=self.division,
            branch=self.get_branch(),
            change_type=self.change_type,
            employment_status=self.get_employment_status(),
            is_current=is_current,
            start_date=start_date,
            end_date=end_date,
            job_description="This is job specification",
            objective="Objective",
            current_step=1
        )
        experience.save()

        return experience

    def get_branch(self) -> OrganizationBranchFactory:
        return OrganizationBranchFactory(organization=self.organization)

    def get_employment_status(self, is_contract=False) -> EmploymentStatusFactory:
        return EmploymentStatusFactory(organization=self.organization, is_contract=is_contract)

    def get_data(self, user: User = None, config: dict = None) -> dict:

        user = user or self.user
        config = config or dict()

        raw_data = {
            "job_title": self.job_title.slug,
            "organization": self.organization.slug,
            "division": self.division.slug,
            "employee_level": self.employee_level.slug,
            "employment_status": self.get_employment_status().slug,
            "branch": self.get_branch().slug,
            "change_type": self.change_type.slug,
            "start_date": user.detail.joined_date,
            "end_date": None,
            "is_current": True,
            "current_step": 1,
            "job_specification": "This is job specification",
            "objective": "Objective",
            "in_probation": False,
            "skill": [],
            "probation_end_date": None
        }

        raw_data.update(**config)

        json_serializable_data = {
            k: v if type(v) in [int, float, list, type(None)] else str(v) for k, v in raw_data.items()
        }
        return json_serializable_data

    def test_valid_create(self) -> None:
        """
        Valid create with current non contract experience starting on joined date
        """
        data = self.get_data()
        response = self.json_post(self.get_url(), json.dumps(data))
        self.assertEqual(response.status_code, 201)

    def test_start_date_before_joined_date(self) -> None:
        """
        [HRIS-2794] Start date should not be before employee join date
        """

        joined_date = self.user.detail.joined_date
        start_date = joined_date - timezone.timedelta(days=1)

        data = self.get_data(config={'start_date': start_date})
        response = self.json_post(self.get_url(), data=json.dumps(data))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['start_date'],
            ['Start date must be greater than or equivalent to joined date.']
        )

    def test_changing_start_date_after_payroll_is_generated_for_that_date(self) -> None:
        """
        [HRIS-2794] Employee should not be able to change start date if payroll is generated
        for that date
        """

        experience = self.create_experience()
        last_paid_date = experience.start_date + timezone.timedelta(days=20)
        new_start_date = experience.start_date + timezone.timedelta(days=10)

        data = self.get_data(config={'start_date': new_start_date})
        url = self.get_url(experience_id=experience.id)

        with mock.patch(
            'irhrs.payroll.utils.helpers.get_last_payroll_generated_date',
            return_value=last_paid_date
        ):
            response = self.json_put(url, json.dumps(data))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['start_date'],
            ['Can not edit this value because payroll has been generated after this date.']
        )

    def test_adding_experience_before_last_payroll_generated_date(self) -> None:
        """
        [HRIS-2794] Employee should not be able to add experience starting
        before last payroll generated date
        """

        # by default joined date is today
        last_paid_date = timezone.now().date() + timezone.timedelta(days=20)

        data = self.get_data()

        with mock.patch(
            'irhrs.payroll.utils.helpers.get_last_payroll_generated_date',
            return_value=last_paid_date
        ):
            response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['start_date'],
            [
                "Can not add experience before last payroll generated date"
                f" {last_paid_date}."
            ]
        )

    def test_changing_end_date_after_payroll_is_generated_for_that_date(self) -> None:
        """
        [HRIS-2794] If payroll is generated and the employee is updating experience then
        the end date can not be before the last payroll generated date.
        """
        start_date = timezone.now().date() - timezone.timedelta(days=90)
        end_date = timezone.now().date() - timezone.timedelta(days=30)
        experience = self.create_experience(start_date=start_date, end_date=end_date)

        last_paid_date = end_date + timezone.timedelta(days=20)
        new_end_date = end_date + timezone.timedelta(days=10)

        data = self.get_data(
            config={
                'start_date': start_date,
                'end_date': new_end_date,
                'is_current': False
            }
        )
        url = self.get_url(experience_id=experience.id)

        with mock.patch(
            'irhrs.payroll.utils.helpers.get_last_payroll_generated_date',
            return_value=last_paid_date
        ):
            response = self.json_put(url, json.dumps(data))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['end_date'],
            [
                "This value can not be before last payroll generated date"
                f" {last_paid_date}."
            ]
        )

    def test_end_date_required_for_non_contract_not_current_experience(self) -> None:
        """
        [HRIS-2794] If the employment type selected is not contract and is current = false then
        the end date field should be available.
        """
        data = self.get_data(config={"is_current": False})

        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['end_date'],
            ["End date required for previous experiences."]
        )

    def test_end_date_not_allowed_for_current_non_contract_experience(self) -> None:
        """
        [HRIS-2794] If the employment type selected is not contract and is current = true then the
        end date field should not be available.
        """

        end_date = timezone.now().date() + timezone.timedelta(days=10)

        data = self.get_data(config={'is_current': True, 'end_date': end_date})

        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['end_date'],
            ['End date cannot be set for active experience except contract status']
        )

    def test_end_date_is_allowed_for_current_contract_experience(self) -> None:
        """
        [HRIS-2794] If the employment type selected is of contract then the
        end date field should be available.
        """
        employment_status = self.get_employment_status(is_contract=True)
        end_date = timezone.now().date() + timezone.timedelta(days=10)

        data = self.get_data(
            config={
                'is_current': True,
                'employment_status': employment_status.slug,
                'end_date': end_date
            }
        )

        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 201)

    def test_end_date_is_required_for_current_contract_experience(self) -> None:
        """
        [HRIS-2794] If the employment type selected is of contract then the
        end date field should be required.
        """
        employment_status = self.get_employment_status(is_contract=True)

        data = self.get_data(
            config={
                'is_current': True,
                'employment_status': employment_status.slug,
                'end_date': None
            }
        )

        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['end_date'],
            ['End date must be set if employment status is contract']
        )

    def test_changing_first_experience_end_date_if_second_is_available(self) -> None:
        """
        [HRIS-2794] First employment experience end date  can not be changed if second
        employment experience is available.
        """
        exp1_start_date = timezone.now().date() - timezone.timedelta(days=90)
        exp1_end_date = timezone.now().date() - timezone.timedelta(days=60)
        exp2_start_date = timezone.now().date() - timezone.timedelta(days=59)

        exp1 = self.create_experience(
            start_date=exp1_start_date,
            end_date=exp1_end_date,
        )
        self.create_experience(
            start_date=exp2_start_date,
            joined_date=exp1_start_date,
        )

        data = self.get_data(
            config={
                'start_date': exp1_start_date,
                'end_date': exp1_end_date - timezone.timedelta(days=1),
                'is_current': False
            }
        )

        response = self.json_put(self.get_url(experience_id=exp1.id), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["end_date"],
            ["Can not change end date when another experience exists after this experience."]
        )

    def test_changing_division_when_core_task_is_assigned(self) -> None:
        """
        [HRIS-2794] If core task is assigned to employee then division can not be updated
        """
        start_date = timezone.now().date() - timezone.timedelta(days=90)
        end_date = timezone.now().date() - timezone.timedelta(days=60)

        experience = self.create_experience(start_date=start_date, end_date=end_date)
        new_division = OrganizationDivisionFactory(organization=self.organization)

        data = self.get_data(
            config={
                'division': new_division.slug,
                'start_date': start_date,
                'end_date': end_date,
                'is_current': False
            }
        )
        with mock.patch(
            'irhrs.users.api.v1.serializers.experience'
            '.UserExperienceSerializer.has_user_assigned_core_task',
            return_value=True
        ):
            response = self.json_put(self.get_url(experience_id=experience.id), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["division"],
            ["You can not change division of experience whose core task is assigned."]
        )

    def test_not_setting_probation_end_date_for_in_probation_true(self) -> None:
        """
        [HRIS-2794] If probation = true then the end date field should be displayed
        """
        data = self.get_data(config={'in_probation': True, 'probation_end_date': None})
        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['probation_end_date'],
            ['Probation end date is required if user is in probation.']
        )

    def test_setting_probation_end_date_for_in_probation_false(self) -> None:
        """
        [HRIS-2794] If probation = false then the end date field should not be required
        """
        probation_end_date = timezone.now().date() + timezone.timedelta(days=90)
        data = self.get_data(
            config={
                'in_probation': False,
                'probation_end_date': probation_end_date
            }
        )
        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['probation_end_date'],
            ['Probation end date can not be set for user not in probation.']
        )

    def test_end_date_can_not_be_before_start_date(self) -> None:
        """
        [HRIS-2794] End date can not be before start date.
        """
        start_date = timezone.now().date()
        end_date = timezone.now().date() - timezone.timedelta(days=40)

        data = self.get_data(
            config={
                'is_current': False,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['start_date'],
            ['Start date must be smaller than end date.']
        )

    def test_deleting_experience_when_payroll_is_generated(self) -> None:
        """
        [HRIS-2794] If payroll is generated for specific experience then employees should not
        be able to delete it.
        """
        experience = self.create_experience()

        last_paid_date = timezone.now().date() + timezone.timedelta(days=10)

        with mock.patch(
            'irhrs.payroll.utils.helpers.get_last_payroll_generated_date',
            return_value=last_paid_date
        ):
            response = self.client.delete(self.get_url(experience_id=experience.id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['detail'],
            'Could not delete experience. Payroll has been generated using this experience.'
        )

    def test_assigning_same_dates_for_multiple_experiences_of_a_user(self) -> None:
        """
        [HRIS-2794] Same date can not be used in multiple experiences for a single user.
        """
        # First create an experience and then try to
        self.create_experience()
        data = self.get_data()

        response = self.json_post(self.get_url(), json.dumps(data))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['start_date'],
            ['Start date must be greater than previous experience start date.']
        )

    def test_overlapping_start_date_of_new_experience_and_end_date_of_old_experience(self) -> None:
        """
        [HRIS-2794] Old experience end date and new experience start date can not overlap.
        """
        old_start_date = timezone.now().date() - timezone.timedelta(days=90)
        old_end_date = timezone.now().date() - timezone.timedelta(days=30)

        self.create_experience(start_date=old_start_date, end_date=old_end_date)

        new_start_date = timezone.now().date() - timezone.timedelta(days=35)
        data = self.get_data(config={'start_date': new_start_date})

        response = self.json_post(self.get_url(), json.dumps(data))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['start_date'],
            [f'This user already has an experience beyond {new_start_date}']
        )

    def test_automatic_end_date_to_last_experience_if_new_experience_created(self) -> None:
        """
        [HRIS-2794] If an employee creates new employee experience then the end date should be
        automatically added in previous experience.
        """
        past_start_date = timezone.now().date() - timezone.timedelta(days=60)
        past_experience = self.create_experience(start_date=past_start_date)

        new_start_date = timezone.now().date()
        expected_past_end_date = new_start_date - timezone.timedelta(days=1)
        data = self.get_data(
            config={"start_date": new_start_date}
        )

        response = self.json_post(self.get_url(), json.dumps(data))

        self.assertEqual(response.status_code, 201)

        past_experience.refresh_from_db()
        self.assertEqual(past_experience.end_date, expected_past_end_date)
        self.assertFalse(past_experience.is_current)
