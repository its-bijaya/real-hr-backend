from django.urls import reverse
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import KPIFactory
from irhrs.appraisal.constants import PENDING, ARCHIVED
from irhrs.appraisal.models.kpi import KPI, IndividualKPI
from irhrs.common.api.tests.common import RHRSAPITestCase, RHRSTestCaseWithExperience
from irhrs.organization.api.v1.tests.factory import EmploymentJobTitleFactory, \
    OrganizationDivisionFactory, EmploymentLevelFactory, FiscalYearFactory
from irhrs.organization.models import EmploymentJobTitle, OrganizationDivision, EmploymentLevel
from irhrs.users.models import UserSupervisor


class TestCreateKpi(RHRSAPITestCase):
    organization_name = 'sambho'

    users = [
        ('admin@email.com', 'password', 'male'),
        ('user@email.com', 'password', 'female')
    ]

    def setUp(self):
        super().setUp()
        for _ in range(3):
            OrganizationDivisionFactory(organization=self.organization)
            EmploymentJobTitleFactory(organization=self.organization)
            EmploymentLevelFactory(organization=self.organization)
        self.client.force_login(self.created_users[0])
        self.job_ids = list(EmploymentJobTitle.objects.values_list('id', flat=True))
        self.division_ids = list(OrganizationDivision.objects.values_list('id', flat=True))
        self.employment_level_ids = list(EmploymentLevel.objects.values_list('id', flat=True))

    def payload(self, job_ids: list, division_ids: list, employment_level_ids: list) -> dict:
        return {
            'title': 'this is test title',
            'success_criteria': 'Employee have to get us more than 20000 clients.',
            'organization': self.organization.id,
            'job_title': job_ids,
            'division': division_ids,
            'employment_level': employment_level_ids,
            'is_archived': False
        }

    @staticmethod
    def kpi_url(method, kwargs):
        return reverse(
            f'api_v1:appraisal:kpi-collection-{method}',
            kwargs=kwargs
        )

    @property
    def get_kpi_list(self):
        return self.kpi_url('list', {'organization_slug': self.organization.slug})

    def test_create_kpi(self):
        payload = self.payload(self.job_ids, self.division_ids,
                               self.employment_level_ids)
        response = self.client.post(
            self.get_kpi_list,
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json()
        )

        response = self.client.get(
            self.get_kpi_list,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        results_length = response.json().get('count')
        kpi_count = KPI.objects.count()
        self.assertEqual(
            results_length,
            kpi_count
        )

        title = response.json().get('results')[0].get('title')
        self.assertEqual(
            title,
            payload.get('title')
        )

    def check_response_and_error_message_of_kpi(self, payload: dict, error_message: dict):
        response = self.client.post(
            self.get_kpi_list,
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.json()
        )
        self.assertEqual(
            response.json(),
            error_message
        )

    def test_kpi_with_bad_payload(self):
        payload = self.payload(self.job_ids, self.division_ids, self.employment_level_ids)
        # payload without title
        payload['title'] = ''
        error_message = {'title': ['This field may not be blank.']}
        self.check_response_and_error_message_of_kpi(payload, error_message)

        # payload without success_criteria

        payload = self.payload(self.job_ids, self.division_ids, self.employment_level_ids)
        payload['success_criteria'] = ''
        error_message = {'success_criteria': ['This field may not be blank.']}
        self.check_response_and_error_message_of_kpi(payload, error_message)

        # payload without jobs
        payload = self.payload([], self.division_ids, self.employment_level_ids)
        error_message = {'job_title': ['This list may not be empty.']}
        self.check_response_and_error_message_of_kpi(payload, error_message)


    def test_update_kpi(self):
        payload = self.payload(self.job_ids, self.division_ids, self.employment_level_ids)
        response = self.client.post(
            self.get_kpi_list,
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json()
        )
        kpi = KPI.objects.filter(title=payload['title']).first()
        kwargs = {'organization_slug': self.organization.slug, 'pk': kpi.id}
        payload['title'] = "this is updated title"
        response = self.client.put(
            self.kpi_url('detail', kwargs),
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )

        title = response.json().get('title')
        self.assertEqual(
            title,
            payload['title']
        )


class TestAssignIndividualKPI(RHRSTestCaseWithExperience):
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('hello@hello.com', 'secretThing', 'Male', 'Clerk'),
        ('helloa@hello.com', 'secretThing', 'Male', 'Clerka'),
        ('hellob@hello.com', 'secretThing', 'Male', 'Clerka'),
    ]
    organization_name = "Helium band"

    def setUp(self):
        super().setUp()
        self.fiscal_year = FiscalYearFactory(organization=self.organization)
        for _, employee in zip(range(4), self.created_users):
            employment_level = EmploymentLevelFactory.create_batch(3,
                                                                   organization=self.organization)
            job_titles = EmploymentJobTitleFactory.create_batch(3, organization=self.organization)
            division = OrganizationDivisionFactory.create_batch(3, organization=self.organization)
            user_detail = employee.detail
            user_detail.job_title = job_titles[1]
            user_detail.employment_level = employment_level[1]
            user_detail.save()
            KPIFactory(
                organization=self.organization,
                job_title=[job_title.id for job_title in job_titles],
                division=[div.id for div in division],
                employment_level=[level.id for level in employment_level]
            )
        self.client.force_login(self.created_users[0])

    @property
    def assign_supervisor(self):
        # this will assign self.created_users[0] supervisor to other users
        for user in self.created_users[1:]:
            UserSupervisor.objects.create(
                user=user,
                supervisor=self.created_users[0],
                approve=True,
                deny=True,
                forward=True,
                authority_order=1
            )

    def individual_kpi_payload(self, user_id: int) -> dict:
        return {
            'title': 'this is for test',
            'user': user_id,
            'fiscal_year': self.fiscal_year.id,
            'status': PENDING

        }

    @staticmethod
    def individual_kpi_url(method: str, kwargs: dict, mode: str = None):
        if not mode:
            mode = 'user'
        return reverse(
            f'api_v1:appraisal:individual-kpi-{method}',
            kwargs=kwargs
        ) + f"?as={mode}"

    def bulk_create_payload(self, kpis: KPI, user_id: int) -> dict:
        payload = {
            'individual_kpi': self.individual_kpi_payload(user_id),
            'extended_kpi': [
                {
                    'kpi': kpi.id,
                    'success_criteria': 'this is for test and it will be same for all',
                    'weightage': 100 / kpis.count()
                } for kpi in kpis
            ]
        }
        return payload

    def bulk_update_payload(self, user_id: int, individual_kpi_id: int, mode: str) -> dict:
        url = self.individual_kpi_url(
            'detail',
            {'organization_slug': self.organization.slug, 'pk': individual_kpi_id},
            mode
        )
        response = self.client.get(
            url,
            format='json'
        )
        extended_individual_kpis = response.json().get('extended_individual_kpis')
        extended_kpis = []
        assigned_kpi_ids = []
        for data in extended_individual_kpis:
            kpi_id = data['kpi']['id']
            extended_kpi = {
                'extended_kpi_id': data.get('id'),
                'kpi': kpi_id,
                'success_criteria': data['success_criteria'] + " this is update success criteria",
            }
            extended_kpis.append(extended_kpi)
            assigned_kpi_ids.append(kpi_id)
        kpis = KPI.objects.exclude(id__in=assigned_kpi_ids)[:2]
        for kpi in kpis:
            extended_kpi = {
                'kpi': kpi.id,
                'success_criteria': 'this is bulk updated success criteria.',
            }
            extended_kpis.append(extended_kpi)
        for extended_kpi in extended_kpis:
            extended_kpi['weightage'] = 100 / len(extended_kpis)
            extended_kpi['individual_kpi'] = individual_kpi_id
        return {
            'individual_kpi': self.individual_kpi_payload(user_id),
            'extended_kpi': extended_kpis
        }

    def bulk_create_url(self, mode):
        return self.individual_kpi_url(
            'bulk-create',
            {'organization_slug': self.organization.slug},
            mode
        )

    def bulk_update_url(self, pk: int, mode: str):
        return self.individual_kpi_url(
            'bulk-update',
            {'organization_slug': self.organization.slug, 'pk': pk},
            mode
        )

    def check_response_and_error_message(self, payload: dict, error_message: dict):
        response = self.client.post(
            self.bulk_create_url('hr'),
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.json()
        )
        self.assertEqual(
            response.json(),
            error_message
        )

    def assign_kpi_to_individual_user(self, user_id: int, kpis: KPI = None):
        if not kpis:
            kpis = KPI.objects.all()[:2]
        response = self.client.post(
            self.bulk_create_url('hr'),
            data=self.bulk_create_payload(kpis, user_id),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.json()
        )
        self.assertEqual(
            response.json(),
            'Kpi assigned successfully'
        )

    def test_bulk_create_individual_kpi(self):
        self.assign_kpi_to_individual_user(self.created_users[1].id)

    def test_bulk_create_individual_kpi_with_bad_payload(self):
        kpis = KPI.objects.all()[:2]
        user = self.created_users[1]

        # payload with no fiscal year
        payload = self.bulk_create_payload(kpis, user.id)
        payload['individual_kpi']['fiscal_year'] = None
        error_message = {'individual_kpi': {'fiscal_year': ['This field may not be null.']}}
        self.check_response_and_error_message(payload, error_message)

        # payload without individual kpi title
        payload = self.bulk_create_payload(kpis, user.id)
        payload['individual_kpi']['title'] = ''
        error_message = {'individual_kpi': {'title': ['This field may not be blank.']}}
        self.check_response_and_error_message(payload, error_message)

        # payload without user
        payload = self.bulk_create_payload(kpis, user.id)
        payload['individual_kpi']['user'] = ''
        error_message = {'individual_kpi': {'user': ['This field may not be null.']}}
        self.check_response_and_error_message(payload, error_message)

        # payload with weightage more than 100
        payload = self.bulk_create_payload(kpis, user.id)
        payload['extended_kpi'][0]['weightage'] = 100
        error_message = {'error': ['Total weightage must be 100%.']}
        self.check_response_and_error_message(payload, error_message)

        # payload with weightage less than 100
        payload['extended_kpi'][0]['weightage'] = 30
        error_message = {'error': ['Total weightage must be 100%.']}
        self.check_response_and_error_message(payload, error_message)

        # payload with string weightage
        payload['extended_kpi'][0]['weightage'] = 'bad payload'
        error_message = {'extended_kpi': [{'weightage': ['A valid integer is required.']}, {}]}
        self.check_response_and_error_message(payload, error_message)

        # payload with float weightage
        payload['extended_kpi'][0]['weightage'] = 30.4
        error_message = {'extended_kpi': [{'weightage': ['A valid integer is required.']}, {}]}
        self.check_response_and_error_message(payload, error_message)

        # payload with negative weightage
        payload['extended_kpi'][0]['weightage'] = -40
        error_message = {
            'extended_kpi': [{'weightage': ['Ensure this value is greater than or equal to 1.']},
                             {}]}
        self.check_response_and_error_message(payload, error_message)

    def test_bulk_update_individual_kpi(self):
        mode = 'hr'
        user = self.created_users[1]
        self.assign_kpi_to_individual_user(user.id)
        individual_kpi = IndividualKPI.objects.filter(
            user_id=user.id,
            fiscal_year_id=self.fiscal_year.id,
            is_archived=False
        ).first()
        payload = self.bulk_update_payload(user.id, individual_kpi.id, mode)
        response = self.client.put(
            self.bulk_update_url(individual_kpi.id, mode),
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json(),
            'Individual KPI updated successfully.'
        )

        # update employee in individual kpi
        payload['individual_kpi']['user'] = self.created_users[2].id
        response = self.client.put(
            self.bulk_update_url(individual_kpi.id, mode),
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json(),
            'Individual KPI updated successfully.'
        )

    def test_bulk_update_employee_who_already_have_individual_kpi_in_that_fiscal_year(self):
        mode = 'hr'
        user1 = self.created_users[1]
        user2 = self.created_users[2]
        self.assign_kpi_to_individual_user(user1.id)
        self.assign_kpi_to_individual_user(user2.id)
        individual_kpi = user1.individual_kpis.filter(
            fiscal_year_id=self.fiscal_year.id,
            is_archived=False
        ).first()

        # update user1 individual kpi with user2
        payload = self.bulk_update_payload(user2.id, individual_kpi.id, mode)
        response = self.client.put(
            self.bulk_update_url(individual_kpi.id, mode),
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )
        self.assertEqual(
            response.json(),
            'Individual KPI updated successfully.'
        )

        previous_individual_kpi_status = user2.individual_kpis.first().status
        self.assertEqual(
            previous_individual_kpi_status,
            ARCHIVED
        )

    def get_individual_kpi(self, user):
        return user.individual_kpis.exclude(status=ARCHIVED).filter(
            fiscal_year_id=self.fiscal_year.id,
            is_archived=False
        ).first()

    # def test_bulk_update_acknowledge_individual_kpi(self):
    #     user = self.created_users[1]
    #     self.assign_kpi_to_individual_user(user.id)
    #     individual_kpi = self.get_individual_kpi(user)
    #     payload = {'status': 'Acknowledged', 'user': user.id}
    #     # Acknowledge by supervisor
    #     self.assign_supervisor
    #     url = self.individual_kpi_url(
    #         'detail',
    #         {
    #             'organization_slug': self.organization.slug,
    #             'pk': individual_kpi.id
    #         },
    #         'supervisor'
    #     )
        # response = self.client.patch(
        #     url,
        #     data=payload,
        #     format='json'
        # )
        # self.assertEqual(
        #     response.status_code,
        #     status.HTTP_400_BAD_REQUEST,
        #     response.json()
        # )
        # self.assertEqual(
        #     response.json(),
        #     {'error': ['you do not have permission to do this action.']}
        # )
        #
        # # Acknowledge by hr
        #
        # url = self.individual_kpi_url(
        #     'detail',
        #     {
        #         'organization_slug': self.organization.slug,
        #         'pk': individual_kpi.id
        #     },
        #     'hr'
        # )
        # response = self.client.patch(
        #     url,
        #     data=payload,
        #     format='json'
        # )
        # self.assertEqual(
        #     response.status_code,
        #     status.HTTP_200_OK,
        #     response.json()
        # )
        # self.assertEqual(
        #     response.json()['status'],
        #     payload['status']
        # )

        # Acknowledge by user
        # self.assign_kpi_to_individual_user(user.id)
        # self.client.logout()
        # self.client.force_login(user)
        # individual_kpi = self.get_individual_kpi(user)
        # url = self.individual_kpi_url(
        #     'detail',
        #     {
        #         'organization_slug': self.organization.slug,
        #         'pk': individual_kpi.id
        #     }
        # )
        #
        # response = self.client.patch(
        #     url,
        #     data=payload,
        #     format='json'
        # )
        # self.assertEqual(
        #     response.status_code,
        #     status.HTTP_200_OK,
        #     response.json()
        # )
        # self.assertEqual(
        #     response.json()['status'],
        #     payload['status']
        # )

    # def test_edit_acknowledged_individual_kpi(self):
    #     user = self.created_users[1]
    #     self.assign_kpi_to_individual_user(user.id)
    #     individual_kpi = self.get_individual_kpi(user)
    #     payload = {'status': 'Confirmed', 'user': user.id}
    #     # Acknowledge by hr
    #     self.assign_supervisor
    #     url = self.individual_kpi_url(
    #         'detail',
    #         {
    #             'organization_slug': self.organization.slug,
    #             'pk': individual_kpi.id
    #         },
    #         'hr'
    #     )
    #     response = self.client.patch(
    #         url,
    #         data=payload,
    #         format='json'
    #     )
    #     self.assertEqual(
    #         response.json()['status'],
    #         payload['status']
    #     )
    #
    #     # update title of individual kpi
    #     payload['title'] = 'this is updated title'
    #     response = self.client.patch(
    #         url,
    #         data=payload,
    #         format='json'
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         status.HTTP_400_BAD_REQUEST,
    #         response.json()
    #     )
    #     self.assertEqual(
    #         response.json(),
    #         {'error': ["Can't update Acknowledged KPI."]}
    #     )

    def test_edit_archived_kpi(self):
        user = self.created_users[1]
        self.assign_kpi_to_individual_user(user.id)
        self.assign_kpi_to_individual_user(user.id)
        individual_kpi = user.individual_kpis.last()
        payload = {'title': 'this is updated title'}
        # Acknowledge by hr
        url = self.individual_kpi_url(
            'detail',
            {
                'organization_slug': self.organization.slug,
                'pk': individual_kpi.id
            },
            'hr'
        )
        response = self.client.patch(
            url,
            data=payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.json()
        )
        self.assertEqual(
            response.json(),
            {'error': ["Can't update Archived KPI."]}
        )

