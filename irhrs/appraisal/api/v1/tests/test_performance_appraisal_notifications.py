from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory, \
    SubPerformanceAppraisalSlotModeFactory, AppraisalFactory, PerformanceAppraisalYearFactory
from irhrs.appraisal.constants import SELF_APPRAISAL
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.notification.models import Notification
from irhrs.notification.models.notification import OrganizationNotification

User = get_user_model()

class TestPerformanceAppraisalNotification(RHRSAPITestCase):
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
        self.user_db = User.objects.all()
        self.performance_appraisal_slot = SubPerformanceAppraisalSlotFactory()
        SubPerformanceAppraisalSlotModeFactory(
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            start_date=get_today(with_time=True),
            deadline=get_today(with_time=True) + timedelta(days=1),
            appraisal_type=SELF_APPRAISAL
        )
        user_id = self.user_db.get(email=self.users[1][0]).id
        self.appraisal = AppraisalFactory(
            appraiser_id=user_id,
            appraisee_id=user_id,
            sub_performance_appraisal_slot=self.performance_appraisal_slot
        )

    def url(self, reverse_url):
        return reverse(
            reverse_url,
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
            }
        )

    def test_send_question_set_notification(self):
        response = self.client.post(
            self.url('api_v1:appraisal:performance-appraisal-form-design-send-question-set')
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        user = self.user_db.get(email=self.users[1][0])
        self.assertTrue(
            Notification.objects.filter(
                recipient=user,
                text='Performance Appraisal Review Forms has been assigned to you.',
                url=f'/user/pa/appraisal/{self.performance_appraisal_slot.id}/forms'
            ).exists()
        )

    def test_update_date_parameters_notification(self):
        data={
            'appraisal_type': SELF_APPRAISAL,
            'start_date': get_today(with_time=True),
            'deadline': get_today(with_time=True) + timedelta(days=1)
        }
        response = self.client.post(
            self.url('api_v1:appraisal:performance-appraisal-mode-update-date-parameters'),
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        user = self.user_db.get(email=self.users[1][0])
        self.assertTrue(
            Notification.objects.filter(
                recipient=user,
                text=f"Deadline of the {self.appraisal.appraisal_type} has been changed.",
                url=f'/user/pa/appraisal/{self.performance_appraisal_slot.id}/forms'
            ).exists()
        )

    def test_resend_notification(self):
        user = self.user_db.get(email=self.users[1][0])
        url = reverse(
            'api_v1:appraisal:appraiser-with-respect-to-appraisee-resend-form',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                'appraiser_id': user.id,
                'appraisee_id': user.id
            }
        ) + '?appraisal_type=self_appraisal&as=hr'
        data = {
            'reason': 'form resent'
        }
        response = self.client.post(
            url,
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        user = self.user_db.get(email=self.users[1][0])
        self.assertTrue(
            Notification.objects.filter(
                recipient=user,
                text=f'Performance Appraisal Review Form of {user.full_name}'
                     f' has been resent.',
                url=f'/user/pa/appraisal/{self.performance_appraisal_slot.id}/forms'
            ).exists()
        )

    def test_edit_deadline_notification(self):
        url = reverse(
            'api_v1:appraisal:appraisal-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                'action_type': 'edit-deadline'
            }
        )
        user = self.user_db.get(email=self.users[1][0])
        appraisal = AppraisalFactory(
            appraiser_id=user.id,
            appraisee_id=user.id,
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            answer_committed=False,
            approved=False,
            deadline=get_today(with_time=True)
        )
        data = {
            'deadline': get_today(with_time=True) + timedelta(days=1),
            'appraisals': [appraisal.id]
        }
        response = self.client.post(
            url,
            data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=user,
                text=f'Deadline of Performance Appraisal Review Form of {user.full_name}'
                     f' has been changed.',
                url=f'/user/pa/appraisal/{self.performance_appraisal_slot.id}/forms'
            ).exists()
        )


class TestPerformanceAppraisalNotifications(RHRSAPITestCase):
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
        self.user_db = User.objects.all()

        self.year = PerformanceAppraisalYearFactory(
            organization=self.organization
        )
        self.performance_appraisal_slot = SubPerformanceAppraisalSlotFactory(
            performance_appraisal_year=self.year
        )
        SubPerformanceAppraisalSlotModeFactory(
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            start_date=get_today(with_time=True),
            deadline=get_today(with_time=True) + timedelta(days=1),
            appraisal_type=SELF_APPRAISAL
        )
        self.user_id = self.user_db.get(email=self.users[1][0]).id
        self.appraisal = AppraisalFactory(
            appraiser_id=self.user_id,
            appraisee_id=self.user_id,
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            start_date=get_today()
        )

    def url(self):
        return reverse(
            'api_v1:appraisal:appraisee-with-respect-to-appraiser-answer',
            kwargs={
                'appraisee_id': self.user_id,
                'appraiser_id': self.user_id,
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
            }
        )

    def payload(self):
        return {
           "question_set":{
              "title":"Default Set",
              "sections":[
                 {
                    "title":"Generic Question Set",
                    "questions":[
                       {
                          "order":1,
                          "question":{
                             "id":225,
                             "score":3,
                             "title":"<p>how do yo rate you skills?</p>",
                             "answers":[

                             ],
                             "remarks":"",
                             "weightage":None,
                             "temp_score":3,
                             "description":"",
                             "rating_scale":5,
                             "is_open_ended":False,
                             "answer_choices":"rating-scale",
                             "remarks_required":False
                          },
                          "is_mandatory":False
                       },
                       {
                          "order":2,
                          "question":{
                             "id":226,
                             "score":3,
                             "title":"<p>How do you rate your performance</p>",
                             "answers":[

                             ],
                             "remarks":"",
                             "weightage":None,
                             "temp_score":3,
                             "description":"",
                             "rating_scale":5,
                             "is_open_ended":False,
                             "answer_choices":"rating-scale",
                             "remarks_required":False
                          },
                          "is_mandatory":False
                       }
                    ],
                    "description":""
                 }
              ],
              "description":""
           },
           "answer_committed":True
        }

    def test_send_answer_notification(self):
        self.client.login(email=self.users[1][0], password=self.users[1][1])
        url = self.url() + '?appraisal_type=self_appraisal&as=appraiser&draft=False'

        response = self.client.post(
            url,
            data=self.payload(),
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        user = self.user_db.get(email=self.users[1][0])
        self.assertTrue(
            OrganizationNotification.objects.filter(
                recipient=self.organization,
                text=f"{user.full_name} has sent Performance Appraisal Form of "
                     f"{user.full_name}",
                url=f'/admin/{self.organization.slug}/pa/settings/frequency-and-mode/'
                    f'{self.performance_appraisal_slot.id}/pa-status'
            ).exists()
        )
