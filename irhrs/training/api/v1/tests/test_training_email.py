from datetime import timedelta
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.training.api.v1.tests.factory import (
    TrainingFactory,
    UserTrainingFactory,
    TrainerFactory
)
from irhrs.training.models import UserTraining, UserTrainingRequest
from irhrs.training.models.helpers import ONSITE, PENDING, PUBLIC

User = get_user_model()


def can_send_email(user, email_type):
    return True


def is_email_setting_enabled_in_org(org, email_type):
    return True


class TestTrainingEmail(RHRSTestCaseWithExperience):
    users = [
        ('admin@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
        ('trainer@email.com', 'secretThing', 'Male', 'Clerk'),
        ('coordinator@email.com', 'secretThing', 'Male', 'Clerka'),
        ('normal@email.com', 'secretThing', 'Male', 'Clerkb'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.user1 = self.created_users[1]
        self.user2 = self.created_users[2]
        self.training = TrainingFactory(
            training_type__organization=self.organization,
            meeting_room__meeting_room__organization=self.organization,
        )
        self.trainer1 = TrainerFactory(
            organization=self.organization
        )
        self.trainer2 = TrainerFactory(
            organization=self.organization
        )
        UserTrainingFactory(training=self.training, user=self.user1)
        UserTrainingFactory(training=self.training, user=self.user2)

    @property
    def members(self):
        return [('members', self.user1.id)]

    @property
    def two_members(self):
        return [('members', self.user1.id), ('members', self.user2.id)]
    # ------ Test assign training email ------

    def assign_training_url(self, kwargs):
        url = reverse(
            'api_v1:training:training-assign-members',
            kwargs=kwargs
        )
        return url

    @property
    def assign_training_payload(self):
        data = {
            "user": [
                self.user1.id
            ]
        }
        return data

    def test_assign_training_email(self):
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': self.training.slug,
        }
        # removes all members from training
        UserTraining.objects.all().delete()
        assign_training_url = self.assign_training_url(kwargs)
        self.client.force_login(self.admin)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                assign_training_url,
                data=self.assign_training_payload,
                format="json"
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(
            self.training.members.filter(id=self.user1.id).exists()
        )

        # At least one email has been sent
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.user1.email])
        self.assertEqual(mail_instance.subject, "New training assigned.")
        self.assertEqual(
            mail_instance.body,
            f"'{self.training.name}' has been assigned to you."
        )

    def update_training_url(self, kwargs):
        url = reverse(
            'api_v1:training:training-detail',
            kwargs=kwargs
        )
        return url

    @property
    def update_training_payload(self):
        tomorrow = get_today(with_time=True, reset_hours=True)
        meeting_room_id = self.training.meeting_room.meeting_room.id
        payload = {
            "name": "Training Room Test",
            "description": "UT for training room",
            "start": tomorrow + timedelta(hours=14),
            "end": tomorrow + timedelta(hours=20),
            "training_type": self.training.training_type.slug,
            "nature": ONSITE,
            "location": "Kathmandu",
            "budget_allocated": 5000,
            "status": PENDING,
            "coordinator": "",
            "visibility": PUBLIC,
            "meeting_room": meeting_room_id
        }
        return payload

    def test_update_training_delete_members_email(self):
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': self.training.slug,
        }
        update_training_url = self.update_training_url(kwargs)
        self.client.force_login(self.admin)
        data = [(k, v) for k, v in self.update_training_payload.items()]

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.put(
                update_training_url,
                data=urlencode(data),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.training.refresh_from_db()
        self.assertTrue(
            self.training.location == self.update_training_payload["location"]
        )

        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(set(mail_instance.to), {self.user1.email, self.user2.email})
        self.assertEqual(mail_instance.subject, "Removed from training.")
        training_name = self.update_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"You have been removed from training '{training_name}'."
        )

    def test_update_training_add_members_email(self):
        # first delete training membership
        UserTraining.objects.filter(user=self.user2).delete()
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': self.training.slug,
        }
        update_training_url = self.update_training_url(kwargs)
        self.client.force_login(self.admin)
        data = [(k, v) for k, v in self.update_training_payload.items()]

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.put(
                update_training_url,
                data=urlencode(data + self.two_members),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.training.refresh_from_db()
        self.assertTrue(
            self.training.location == self.update_training_payload["location"]
        )
        self.assertEqual(len(mail.outbox), 2)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.user2.email])
        self.assertEqual(mail_instance.subject, "New training assigned.")
        self.update_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"'{self.training.name}' has been assigned to you."
        )
    # # ------ Test training request by user sends email to HR ---------

    def request_training_url(self, kwargs):
        url = reverse(
            'api_v1:training:training-join',
            kwargs=kwargs
        )
        return url

    @property
    def request_training_payload(self):
        data = {
            "remarks": "I need this training for skills bro!"
        }
        return data

    def test_request_training_email(self):
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': self.training.slug,
        }
        request_training_url = self.request_training_url(kwargs)
        # removes all members from training
        UserTraining.objects.all().delete()
        self.client.force_login(self.user1)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                request_training_url,
                data=self.request_training_payload,
                format="json"
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        training_request = UserTrainingRequest.objects.get(user=self.user1)
        self.assertTrue(
            training_request
        )

        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.admin.email])
        self.assertEqual(mail_instance.subject,
                         f"New training request from {self.user1.full_name}"
                         )
        self.assertEqual(
            mail_instance.body,
            f"{self.user1.full_name} has requested for training '{self.training.name}'."
        )

    # ------ Test cancelling training sends mail to user ----
    def cancel_training_url(self, kwargs):
        url = reverse(
            'api_v1:training:training-detail',
            kwargs=kwargs
        )
        return url

    def test_cancel_training_email(self):
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': self.training.slug,
        }
        cancel_training_url = self.cancel_training_url(kwargs) + "?as=hr"
        self.client.force_login(self.admin)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.delete(
                cancel_training_url,
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(
            set(mail_instance.to),
            {self.user1.email, self.user2.email}
        )
        self.assertEqual(mail_instance.subject, "Training cancelled.")
        self.assertEqual(
            mail_instance.body,
            f"Training '{self.training.name}' has been cancelled."
        )

    # Test while assigning/removing trainers,
    # the trainers are notified
    def create_training_url(self, kwargs):
        url = reverse(
            'api_v1:training:training-list',
            kwargs=kwargs
        )
        return url

    @property
    def create_training_payload(self):
        tomorrow = get_today(with_time=True, reset_hours=True)
        meeting_room_id = self.training.meeting_room.meeting_room.id
        payload = {
            "name": "Training Room Test",
            "description": "UT for training room",
            "start": tomorrow + timedelta(hours=14),
            "end": tomorrow + timedelta(hours=20),
            "training_type": self.training.training_type.slug,
            "nature": ONSITE,
            "location": "Kathmandu",
            "budget_allocated": 5000,
            "status": PENDING,
            "coordinator": "",
            "visibility": PUBLIC,
            "meeting_room": meeting_room_id
        }
        return payload

    @property
    def internal_trainer(self):
        return [('internal_trainers', self.created_users[3].id)]

    @property
    def external_trainer(self):
        return [('external_trainers', self.trainer1.id)]

    @property
    def two_external_trainers(self):
        return [
            ('external_trainers', self.trainer1.id),
            ('external_trainers', self.trainer2.id)
        ]

    def test_internal_trainer_email(self):
        kwargs = {
            'organization_slug': self.organization.slug,
        }
        create_url = self.create_training_url(kwargs)
        payload = [(k, v) for k, v in self.create_training_payload.items()]
        self.client.force_login(self.admin)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.post(
                create_url,
                data=urlencode(payload + self.internal_trainer),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.created_users[3].email])
        self.assertEqual(mail_instance.subject, "New Training Assigned.")
        training_name = self.create_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"You have been assigned to training '{training_name}' as a trainer."
        )
        created_training_slug = response.json()['slug']

        # After unassigning internal trainer
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': created_training_slug,
        }
        update_training_url = self.update_training_url(kwargs)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            response = self.client.put(
                update_training_url,
                data=urlencode(payload),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(mail.outbox), 2)
        mail_instance = mail.outbox[1]

        self.assertEqual(mail_instance.to, [self.created_users[3].email])
        self.assertEqual(mail_instance.subject, "Training unassigned.")
        training_name = self.create_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"You have been removed from training '{training_name}' as a trainer."
        )

    def test_external_trainer_email(self):
        kwargs = {
            'organization_slug': self.organization.slug,
        }
        create_url = self.create_training_url(kwargs)
        payload = [(k, v) for k, v in self.create_training_payload.items()]
        self.client.force_login(self.admin)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email), \
             patch(
                'irhrs.core.utils.email.is_email_setting_enabled_in_org',
                is_email_setting_enabled_in_org
        ):
            response = self.client.post(
                create_url,
                data=urlencode(payload + self.two_external_trainers),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(len(mail.outbox), 1)
        mail_instance = mail.outbox[0]
        self.assertEqual(
            set(mail_instance.to),
            {self.trainer1.email, self.trainer2.email}
        )
        self.assertEqual(mail_instance.subject, "New Training Assigned.")
        training_name = self.create_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"You have been assigned to training '{training_name}' as a trainer."
        )
        created_training_slug = response.json()['slug']
        # clear outbox for new set of tests
        mail.outbox.clear()

        # After unassigning external
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': created_training_slug,
        }
        update_training_url = self.update_training_url(kwargs)

        # unassign one trainer
        with patch('irhrs.core.utils.email.can_send_email', can_send_email), \
             patch(
                'irhrs.core.utils.email.is_email_setting_enabled_in_org',
                is_email_setting_enabled_in_org
        ):
            response = self.client.put(
                update_training_url,
                data=urlencode(payload + self.external_trainer),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        updated_training_name = response.json()['name']
        self.assertEqual(len(mail.outbox), 2)
        mail_instance = mail.outbox[0]

        self.assertEqual(mail_instance.to, [self.trainer2.email])
        self.assertEqual(mail_instance.subject, "Training unassigned.")
        training_name = self.create_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"You have been removed from training '{training_name}' as a trainer."
        )

        mail_instance = mail.outbox[1]

        self.assertEqual(mail_instance.to, [self.trainer1.email])
        self.assertEqual(mail_instance.subject, "Training updated.")
        training_name = self.create_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"Some details on training '{updated_training_name}' have been updated."
        )

    def test_removed_member_email(self):
        kwargs = {
            'organization_slug': self.organization.slug,
            'slug': self.training.slug,
        }
        update_training_url = self.update_training_url(kwargs)
        payload = [(k, v) for k, v in self.update_training_payload.items()]
        self.client.force_login(self.admin)
        with patch('irhrs.core.utils.email.can_send_email', can_send_email),\
             patch(
                'irhrs.core.utils.email.is_email_setting_enabled_in_org',
                is_email_setting_enabled_in_org
        ):
            response = self.client.put(
                update_training_url,
                data=urlencode(payload + self.members),
                content_type='application/x-www-form-urlencoded'
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(len(mail.outbox), 2)
        mail_instance = mail.outbox[0]
        self.assertEqual(mail_instance.to, [self.user2.email])
        self.assertEqual(mail_instance.subject, "Removed from training.")
        training_name = self.create_training_payload['name']
        self.assertEqual(
            mail_instance.body,
            f"You have been removed from training '{training_name}'."
        )
