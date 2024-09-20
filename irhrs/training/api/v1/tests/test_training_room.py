from datetime import timedelta
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import MeetingRoomFactory, OrganizationBranchFactory, \
    EmploymentJobTitleFactory
from irhrs.organization.models import MeetingRoomStatus
from irhrs.training.api.v1.tests.factory import TrainingTypeFactory
from irhrs.training.constants import NRS
from irhrs.training.models import Training
from irhrs.core.utils.training import set_training_members
from irhrs.training.models.helpers import ONSITE, PENDING, PUBLIC, OFFSITE
from irhrs.users.api.v1.tests.factory import UserDetailFactory, UserFactory

USER = get_user_model()


class TestTrainingRoom(RHRSTestCaseWithExperience):
    users = [
        ('admin@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('trainer@email.com', 'secretThing', 'Male', 'Clerk'),
        ('coordinator@email.com', 'secretThing', 'Male', 'Clerka'),
        ('normal@email.com', 'secretThing', 'Male', 'Clerkb'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )
        self.training_type = TrainingTypeFactory(
            organization=self.organization,
            budget_limit=50000,
            amount_type=NRS
        )
        self.branch = OrganizationBranchFactory(organization=self.organization)
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

    @property
    def coordinator(self):
        return USER.objects.get(email='coordinator@email.com')

    @property
    def training_url(self):
        return reverse(
            'api_v1:training:training-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def training_put_url(self, slug):
        return reverse(
            'api_v1:training:training-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'slug': slug
            }
        )
    
    def delete_members_from_training_url(self, kwargs):
        return reverse(
            "api_v1:training:training-deleted-members",
            kwargs=kwargs
        )

    @property
    def members(self):
        return [('members', self.coordinator.id), ('members', self.admin.id)]

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

    def test_training_room(self):
        url = self.training_url + '?as=hr'
        data = self.payload(self.start, self.end)
        data = [(key, value) for key, value in data.items()] + self.members

        # create training with Meeting Room
        response = self.client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        response_members_set = set(response.json().get('members'))
        output_members_list = [self.coordinator.id, self.admin.id]
        output_members_set = set(output_members_list)
        self.assertEqual(
            response_members_set,
            output_members_set
        )

        # Recreate training with same meeting room which provides 400 error
        bad_response = self.client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(
            bad_response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            bad_response.json().get('meeting_room'),
            [f'Meeting Room for {self.start}+05:45 - {self.end}+05:45 is not available.']
        )

        # availability of meeting room after the training is completed
        start = (get_today(with_time=True) + timedelta(days=1, hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        end = (get_today(with_time=True) + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        data = self.payload(start, end)
        data.update({
            'branch': self.branch.slug
        })
        data = [(key, value) for key, value in data.items()] + self.members

        response = self.client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        # Here, self.user was in self.branch so training was assigned to self.user too.
        response_members_set = set(response.json().get('members'))
        output_members_list = [self.coordinator.id, self.admin.id, self.user.id]
        output_members_set = set(output_members_list)
        self.assertEqual(
            response_members_set,
            output_members_set
        )

        # check if offsite nature requires meeting room or not
        response_with_nature_offsite = self.client.post(
            url,
            data=self.payload(self.start, self.end, nature=OFFSITE)
        )
        self.assertEqual(
            response_with_nature_offsite.status_code,
            status.HTTP_201_CREATED
        )

    def test_assign_member_to_training(self):
        """
        Test Scenarios

        1. hr should be able assign training in bulk by Job title, Division, Employment level,
        Branch and Employment type.

        2. hr should also be able to assign training employee wise (UT covered in above test_case)

        3. hr should be able to assign training based of multiple options like employee wise,
        Job title, Division, Employment level, Branch and Employment type.

        4. system should assign training only once to a user if the user belongs to multiple
        options. i.e. user is in both options, division and job title.

        Below UT has covered for Job title and Branch, similarly we can cover for all other
        ascpects such as Division, Employment type and Employment level
        """

        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        user4 = UserFactory()
        branch1 = OrganizationBranchFactory(organization=self.organization)
        job_title1 = EmploymentJobTitleFactory(organization=self.organization)
        user1.detail.branch = branch1
        user1.detail.job_title = job_title1
        user1.detail.save()
        user2.detail.branch = branch1
        user2.detail.job_title = job_title1
        user2.detail.save()
        user3.detail.branch = branch1
        user3.detail.job_title = job_title1
        user3.detail.save()
        user4.detail.job_title = job_title1
        user4.detail.save()

        url = self.training_url + '?as=hr'
        data = self.payload(self.start, self.end)
        branch = [('branch', self.branch.slug), ('branch', branch1.slug)]
        job_title = [('job_title', self.job_title.slug), ('job_title', job_title1.slug)]
        data = [(key, value) for key, value in data.items()] + self.members + branch + job_title
        response = self.client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        # self.coordinator.id, self.admin.id are the members sent from self.payload
        # self.user.id is employee under self.branch and self.job_title
        # user1.id, user2.id, user3.id are employees under branch1 and job_title1
        # user4.id us employee under job_title1
        self.assertEqual(
            len(response.json().get('members')),
            7
        )
        response_user_set = set(response.json().get('members'))
        output_set_list = [
            self.coordinator.id, self.admin.id, self.user.id, user1.id, user2.id,
            user3.id, user4.id
        ]
        output_user_set = set(output_set_list)
        self.assertEqual(
            response_user_set,
            output_user_set
        )

        slug = Training.objects.first().slug
        put_url = self.training_put_url(slug) + '?as=hr'
        data5 = self.payload(self.start, self.end)
        branch = [('branch', branch1.slug)]
        job_title = [('job_title', job_title1.slug)]
        data3 = [(key, value) for key, value in data5.items()] + self.members + branch + job_title
        response = self.client.put(
            put_url,
            data=urlencode(data3),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        response_user_set = set(response.json().get('members'))
        output_set_list = [
            self.coordinator.id, self.admin.id, user1.id, user2.id, user3.id, user4.id
        ]
        output_user_set = set(output_set_list)
        self.assertEqual(
            response_user_set,
            output_user_set
        )

    def test_put_request_for_assigning_employee(self):
        data = self.payload(self.start, self.end)
        branch = [('branch', self.branch.slug), ]
        data = [(key, value) for key, value in data.items()] + self.members
        url = self.training_url + '?as=hr'

        created = self.client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )

        slug = Training.objects.first().slug
        put_url = self.training_put_url(slug) + '?as=hr'
        data2 = data + branch
        response = self.client.put(
            put_url,
            data=urlencode(data2),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        response_user_set = set(response.json().get('members'))
        output_set_list = [
            self.coordinator.id, self.admin.id, self.user.id
        ]
        output_user_set = set(output_set_list)
        self.assertEqual(
            response_user_set,
            output_user_set
        )

        response = self.client.put(
            put_url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        response_user_set = set(response.json().get('members'))
        output_set_list = [
            self.coordinator.id, self.admin.id
        ]
        output_user_set = set(output_set_list)
        self.assertEqual(
            response_user_set,
            output_user_set
        )

    def test_delete_member_from_training(self):
        data = self.payload(self.start, self.end)
        branch = [('branch', self.branch.slug), ]
        data = [(key, value) for key, value in data.items()] + self.members
        url = self.training_url + '?as=hr'

        created = self.client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
        data = {
            "user": self.admin.id
        }
        slug = Training.objects.first().slug
        url = self.training_put_url(slug)
        response = self.client.get(
            url,
            format="json"
        )
        members = response.data['members']
        old_members = []
        for member in members:
            old_members.append(member['full_name'])
        kwargs={
                'organization_slug': self.organization.slug,
                'slug': slug
            }
        url = self.delete_members_from_training_url(kwargs)
        
        response = self.client.post(
            url,
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
        # This function is used to update member in cache 
        set_training_members()
        self.assertEqual(
            response.data,
            "Member is deleted from training.",
            response.json()
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            response.json()
        )

        url = self.training_put_url(slug)
        response = self.client.get(
            url,
            format="json"
        )

        members = response.data['members']
        members_after_delete = []
        for member in members:
            members_after_delete.append(member['full_name'])
        
        self.assertNotEqual(
            set(old_members),
            set(members_after_delete),
            response.json()
        )
