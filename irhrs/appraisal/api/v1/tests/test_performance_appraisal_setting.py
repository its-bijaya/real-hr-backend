from copy import deepcopy

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory, \
    AppraisalFactory, PerformanceAppraisalYearFactory
from irhrs.appraisal.constants import SELF_APPRAISAL
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory, \
    OrganizationDivisionFactory, EmploymentStatusFactory, EmploymentLevelFactory, \
    OrganizationFactory

User = get_user_model()


class TestPerformanceAppraisalSetting(RHRSAPITestCase):
    organization_name = "Necrophos"
    users = [
        ('admin@gmail.com', 'hellonepal', 'Male'),
        ('luffy@onepiece.com', 'passwordissecret', 'Female'),
        ('guest@admin.com', 'guestnotallowed', 'Other')
    ]
    fake = Factory.create()

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.users = User.objects.all()
        self.branches = OrganizationBranchFactory(organization=self.organization)
        self.divisions = OrganizationDivisionFactory(organization=self.organization)
        self.employment_levels = EmploymentLevelFactory(organization=self.organization)
        self.employment_types = EmploymentStatusFactory(organization=self.organization)
        self.performance_appraisal_slot = SubPerformanceAppraisalSlotFactory()

    @property
    def data(self):
        return {
            "duration_of_involvement": 12,
            "duration_of_involvement_type": "Months",
            "branches": [self.branches.slug],
            "divisions": [self.divisions.slug],
            "employment_types": [self.employment_types.slug],
            "employment_levels": [self.employment_levels.slug]
        }

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:appraisal-setting-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:appraisal-setting-list',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                    **kwargs
                }
            )

    def do_create(self, data):
        return self.client.post(self.url(), data=data, format='json')

    def test_create(self):
        data = deepcopy(self.data)
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update data
        data.update({
            'duration_of_involvement': 2,
            'duration_of_involvement_type': 'Years',
            'branches': [],
            'divisions': [],
        })
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list(self):
        _ = self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_performance_appraisal_overview(self):
        url = reverse(
            'api_v1:appraisal:overview-report-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )
        per = PerformanceAppraisalYearFactory(organization=self.organization)
        slot = SubPerformanceAppraisalSlotFactory(performance_appraisal_year=per)
        AppraisalFactory(
            appraisee_id=self.admin.id,
            appraiser_id=self.admin.id,
            sub_performance_appraisal_slot=slot,
            answer_committed=True,
            approved=True,
            final_score=50,
            appraisal_type=SELF_APPRAISAL
        )
        PerformanceAppraisalYearFactory(
            organization=self.organization
        )

        instance = Appraisal.objects.first()
        slot_id = instance.sub_performance_appraisal_slot.id

        # positive test case
        valid_url = url + f'?as=hr&slot={slot_id}'
        valid_response = self.client.get(valid_url)
        count = len(valid_response.data.get('appraisal_type_stats'))
        self.assertEqual(count, 1)

        # negative test case
        bad_url = url + f'?as=hr&slot={slot_id+1}'
        bad_response = self.client.get(bad_url)
        count = len(bad_response.data.get('appraisal_type_stats'))
        self.assertEqual(count, 0)
