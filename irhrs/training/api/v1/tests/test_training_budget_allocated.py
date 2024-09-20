from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory, \
    EmploymentJobTitleFactory, MeetingRoomFactory
from irhrs.training.api.v1.tests.factory import TrainingTypeFactory, TrainingFactory
from irhrs.training.constants import NRS
from irhrs.training.models import Training
from irhrs.training.models.helpers import ONSITE, PENDING, PUBLIC
from irhrs.users.api.v1.tests.factory import UserFactory

USER = get_user_model()


class TestTrainingAllocatedBudget(RHRSTestCaseWithExperience):
    users = [
        ('admin@gmail.com', 'admin', 'Female', 'Admin'),
        ('trainer@email.com', 'trainer', 'Male', 'Clerk'),
        ('coordinator@email.com', 'coordinator', 'Female', 'Clerka'),
        ('normal@email.com', 'user', 'Male', 'Clerkb'),
    ]
    organization_name = "aayubank"

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.training_type = TrainingTypeFactory(
            organization=self.organization,
            budget_limit=1200,
            amount_type=NRS
        )
        self.branch = OrganizationBranchFactory(
            organization=self.organization
        )
        self.job_title = EmploymentJobTitleFactory(organization=self.organization)
        self.meeting_room = MeetingRoomFactory(
            organization=self.organization,
            branch=self.branch
        )
        self.start = get_today().strftime("%Y-%m-%d %H:%M:%S")
        self.end = (get_today() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.user = UserFactory()
        self.user.detail.branch = self.branch
        self.user.detail.job_title = self.job_title
        self.user.detail.save()

        self.url = reverse(
            "api_v1:training:training-list",
            kwargs={
               'organization_slug': self.organization.slug
            }
        )

        self.training = TrainingFactory(
                name="Training Test",
                training_type=self.training_type
            )

    @property
    def members(self):
        return [('members', self.coordinator.id), ('members', self.admin.id)]

    @property
    def coordinator(self):
        return USER.objects.get(email='coordinator@email.com')

    def payload(self, start, end, nature=ONSITE):
        meeting_room_id = ""
        if nature == ONSITE:
            meeting_room_id = self.meeting_room.id
        return {
            "name": "Training Room Test",
            "description": "UT for training room",
            "start": start,
            "end": end,
            "training_type": self.training_type.slug,
            "nature": nature,
            "location": "Kathmandu",
            "budget_allocated": 5000,
            "status": PENDING,
            "coordinator": self.coordinator.id,
            "visibility": PUBLIC,
            "meeting_room": meeting_room_id
        }

    def training_edit_url(self, slug):
        return reverse(
            'api_v1:training:training-type-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': slug
            }
        ) + '?as=hr'

    def put_url(self, slug):
        return reverse(
            'api_v1:training:training-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': slug
            }
        ) + '?as=hr'

    def edit_payload(self):
        return {
            "amount_type": "NRS",
            "budget_limit": 100,
            "slug": self.training_type.slug,
            "title": "Training Room Test",
            "trainings": [
                {
                    "end": self.training.end,
                    "name": self.training.name,
                    "start": self.training.start,
                    "slug": self.training.slug,
                    "status": self.training.status

                }
            ],
            "used_budget": 120
        }

    def get_payload_data(self, data):
        return [(key, value) for key, value in data.items()] + self.members

    def test_budget_allocation_of_training(self):
        data = self.payload(self.start, self.end)
        data = self.get_payload_data(data)
        response = self.client.post(
            self.url,  data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('budget_allocated')[0],
            'Total budget allocated exceeded allocated budget for training type. Available budget is 1200.0'
        )

    def test_valid_budget_allocation_breakdown(self):
        request = self.payload(self.start, self.end)
        request['budget_allocated'] = 1000
        request['program_cost'] = 100
        request['tada'] = 500
        request['accommodation'] = 200
        request['trainers_fee'] = 200
        request['others'] = 0
        datas = self.get_payload_data(request)
        response = self.client.post(
            self.url, data=urlencode(datas),
            content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json().get('name'), 'Training Room Test'
        )

    def test_invalid_budget_allocation_breakdown(self):
        datas = self.payload(self.start, self.end)
        datas['budget_allocated'] = 1000
        datas['program_cost'] = 200
        datas['tada'] = 500
        datas['accommodation'] = 1205
        datas['trainers_fee'] = 100
        datas['others'] = 0
        datas = self.get_payload_data(datas)
        response = self.client.post(
            self.url,  data=urlencode(datas),
            content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('error')[0],
            'Sum of budget breakdown 2005.0 exceeded allocated budget for training type. Available budget is 1000.0'
        )

    def test_valid_training_type_update(self):
        url = self.training_edit_url(self.training_type.slug)
        data = self.edit_payload()
        data['budget_limit'] = 400

        response = self.client.patch(
            url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_training_type_update(self):
        url = self.training_edit_url(self.training_type.slug)
        response = self.client.patch(
            url, self.edit_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('budget_limit')[0],
            'Budget limit cannot be less than used budget which is 120'
        )

    def test_start_end_date(self):
        slug = Training.objects.first().slug
        data = self.payload(self.end, self.start)
        data['budget_allocated'] = 1000
        data = self.get_payload_data(data)

        response = self.client.put(
            self.put_url(slug),
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json().get('start')[0],
            'Start date can\'t be greater than end date'
        )
