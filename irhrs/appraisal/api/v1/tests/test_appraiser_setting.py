from datetime import timedelta
from dateutil.relativedelta import relativedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import SubPerformanceAppraisalSlotFactory, \
    AppraisalFactory, DeadlineExceedScoreDeductionConditionFactory, AppraisalSettingFactory, \
    SubPerformanceAppraisalSlotModeFactory, PerformanceAppraisalYearFactory
from irhrs.appraisal.constants import SELF_APPRAISAL, SUPERVISOR_APPRAISAL, PEER_TO_PEER_FEEDBACK, \
    SUBORDINATE_APPRAISAL, PERCENTAGE
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlotMode
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import OrganizationBranchFactory, \
    OrganizationDivisionFactory, EmploymentLevelFactory, EmploymentStatusFactory, FiscalYearFactory
from irhrs.questionnaire.api.v1.tests.factory import QuestionFactory
from irhrs.users.models import UserSupervisor, UserExperience, UserDetail

User = get_user_model()


def question_set():
    return {
        "title": "Default Set",
        "sections": [
            {
                "title": "Generic Question Set",
                "questions": [
                    {
                        "order": 1,
                        "question": {
                            "id": 225,
                            "score": 1,
                            "title": "<p>how do yo rate you skills?</p>",
                            "answers": [],
                            "remarks": "",
                            "weightage": None,

                            "description": "",
                            "rating_scale": 5,
                            "is_open_ended": False,
                            "answer_choices": "rating-scale",
                            "remarks_required": False,
                        },
                        "is_mandatory": False,
                    },
                    {
                        "order": 2,
                        "question": {
                            "id": 226,
                            "score": 2,
                            "title": "<p>How do you rate your performance</p>",
                            "answers": [],
                            "remarks": "",
                            "weightage": None,
                            "description": "",
                            "rating_scale": 5,
                            "is_open_ended": False,
                            "answer_choices": "rating-scale",
                            "remarks_required": False,
                        },
                        "is_mandatory": False,
                    },
                ],
                "description": "",
            }
        ],
        "description": "",
    }


class AppraiserSettingBaseMixin(RHRSTestCaseWithExperience):
    organization_name = "Necrophos"
    users = [
        ('admin@gmail.com', 'hellonepal', 'Male', 'Manager'),
        ('luffy@onepiece.com', 'passwordissecret', 'Female', 'Supervisor'),
        ('guest@admin.com', 'guestnotallowed', 'Other', 'Employee')
    ]
    fake = Factory.create()
    appraisal_type = [
        SELF_APPRAISAL, SUPERVISOR_APPRAISAL,
        PEER_TO_PEER_FEEDBACK, SUBORDINATE_APPRAISAL
    ]

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.users = User.objects.filter(detail__organization=self.organization)
        self.fiscal_year = FiscalYearFactory(
            organization=self.organization,
            start_at=get_today(),
            end_at=get_today() + relativedelta(years=1)
        )
        self.performance_appraisal_year = PerformanceAppraisalYearFactory(
            year=self.fiscal_year,
            organization=self.organization
        )

        self.performance_appraisal_slot = SubPerformanceAppraisalSlotFactory(
            performance_appraisal_year=self.performance_appraisal_year
        )
        for user in self.users[1:]:
            UserSupervisor.objects.create(
                user=user,
                supervisor=self.users[0],
                user_organization=self.organization,
                supervisor_organization=self.organization
            )
        for appraisal_type in self.appraisal_type:
            SubPerformanceAppraisalSlotMode.objects.create(
                appraisal_type=appraisal_type,
                weightage=25,
                sub_performance_appraisal_slot=self.performance_appraisal_slot
            )

    def get_appraisal_setting_factory(self):
        appraisal_setting_factory = AppraisalSettingFactory(
            duration_of_involvement=3,
            duration_of_involvement_type='Months'
        )
        appraisal_setting_factory.branches.add(
            OrganizationBranchFactory(organization=self.organization)
        )
        appraisal_setting_factory.divisions.add(
            OrganizationDivisionFactory(organization=self.organization)
        )
        appraisal_setting_factory.employment_levels.add(
            EmploymentLevelFactory(organization=self.organization)
        )
        appraisal_setting_factory.employment_types.add(
            EmploymentStatusFactory(organization=self.organization)
        )
        return appraisal_setting_factory


class TestSupervisorAppraiserSetting(AppraiserSettingBaseMixin):
    appraisal_type = [SUPERVISOR_APPRAISAL]

    def setUp(self):
        super().setUp()

    def url(self, **kwargs):
        if not kwargs:
            return reverse(
                'api_v1:appraisal:supervisor-appraiser-setting-list',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
                }
            )
        return reverse(
            'api_v1:appraisal:supervisor-appraiser-setting-assign-action',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                **kwargs
            }
        )

    def test_list(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 3)

    def test_bulk_action(self):
        # bulk assign action
        kwargs = {
            'action': 'assign',
            'action_type': 'bulk'
        }
        response = self.client.post(
            self.url(**kwargs),
            data={'authority_level': '1'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Appraisal.objects.count(), 2)

        # bulk unassign action
        kwargs.update({'action': 'unassign'})
        response = self.client.post(
            self.url(**kwargs),
            data={'authority_level': '1'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appraiser_count = Appraisal.objects.filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            appraisal_type=SUPERVISOR_APPRAISAL
        ).count()
        self.assertEqual(appraiser_count, 0)

    def test_individual_action(self):
        # individual assign action
        kwargs = {
            'action': 'assign',
            'action_type': 'individual'
        }
        response = self.client.post(
            self.url(**kwargs),
            data={'authority_level': '1', 'user': self.users[1].id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Appraisal.objects.count(), 1)

        # individual unassign action
        kwargs.update({'action': 'unassign'})
        response = self.client.post(
            self.url(**kwargs),
            data={'authority_level': '1', 'user': self.users[1].id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appraiser_count = Appraisal.objects.filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            appraisal_type=SUPERVISOR_APPRAISAL
        ).count()
        self.assertEqual(appraiser_count, 0)


class TestAppraisalSettingFilter(AppraiserSettingBaseMixin):
    def setUp(self):
        super().setUp()

    def url(self):
        appraisal = self.get_appraisal_setting_factory()
        appraisal.branches.all().delete()
        appraisal.divisions.all().delete()
        appraisal.employment_levels.all().delete()
        appraisal.employment_types.all().delete()
        appraisal.save()

        slot_id = appraisal.sub_performance_appraisal_slot.id

        return reverse(
            'api_v1:appraisal:peer-to-peer-appraiser-setting-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': slot_id
            }
        )

    def test_appraiser_setting_filter(self):
        # joined_date and start_date changed to test the appraiser setting
        # similar to this test, we can test for self-appraisal, subordinate-appraisal and
        # supervisor-appraisal

        user_id = User.objects.first().id
        exp_user = UserExperience.objects.get(user=user_id)
        exp_user.start_date = get_today() - timedelta(days=1240)
        user_detail = UserDetail.objects.get(user=user_id)
        user_detail.joined_date = get_today() - timedelta(days=1240)
        exp_user.save()
        user_detail.save()

        response = self.client.get(
            self.url()
        )

        self.assertEqual(
            response.data.get('count'),
            1
        )


class TestPeerToPeerAppraiserSetting(AppraiserSettingBaseMixin):
    appraisal_type = [PEER_TO_PEER_FEEDBACK]

    def setUp(self):
        super().setUp()

    def url(self):
        return reverse(
            'api_v1:appraisal:peer-to-peer-appraiser-setting-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
            }
        )

    def test_create(self):
        # test for positive test
        response = self.client.post(
            self.url(),
            data={
                'appraisee': self.users[0].id,
                'appraisers': self.users.values_list('id', flat=True)[1:],
                'add_default': True,
                'remarks': 'This is test remarks.'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        count = len(response.data.get('appraisers'))
        self.assertEqual(
            count, 2
        )

        # test for evaluatee within evaluators
        response = self.client.post(
            self.url(),
            data={
                'appraisee': self.users[0].id,
                'appraisers': self.users.values_list('id', flat=True),
                'add_default': True,
                'remarks': 'This is test remarks.'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertListEqual(
            response.json().get("appraisee"),
            ["Appraisee can't be assigned as appraisers."]
        )
        self._test_list()

    def _test_list(self):
        response = self.client.get(
            self.url()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 3)


class TestAppraisalSave(AppraiserSettingBaseMixin):
    def test_save_performance_appraisal(self):
        slug = self.organization.slug
        appraisal = AppraisalFactory(
            appraisee_id=self.admin.id, appraiser_id=self.admin.id, answer_committed=False,
            question_set=question_set(),
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            start_date=get_today()
        )
        slot_id = appraisal.sub_performance_appraisal_slot.id

        url = reverse(
            'api_v1:appraisal:appraisee-with-respect-to-appraiser-answer',
            kwargs={
                'appraisee_id': self.admin.id,
                'appraiser_id': self.admin.id,
                'organization_slug': slug,
                'sub_performance_appraisal_slot_id': slot_id
            }
        ) + "?appraisal_type=self_appraisal&as=appraiser&draft=True"
        data = {
            "question_set": question_set(),
            "answer_committed": False
        }
        response = self.client.post(
            url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        appraisal = Appraisal.objects.first()
        self.assertTrue(appraisal.is_draft)
        self.assertFalse(appraisal.answer_committed)
        self.assertFalse(appraisal.approved)

        url = reverse(
            'api_v1:appraisal:appraisee-question-set-count-list',
            kwargs={
                'action_type': 'statistics',
                'organization_slug': slug,
                'sub_performance_appraisal_slot_id': slot_id
            }
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        # check if saved count is correct or not
        expected_output = {'saved': 1, 'received': 0, 'sent': 0, 'approved': 0}
        self.assertEqual(
            response.json().get('results')[0].get('question_set_count').get(SELF_APPRAISAL),
            expected_output
        )

        url = reverse(
            'api_v1:appraisal:appraiser-with-respect-to-appraisee-list',
            kwargs={
                'appraisee_id': self.admin.id,
                'organization_slug': slug,
                'sub_performance_appraisal_slot_id': slot_id
            }
        ) + '?appraisal_type=self_appraisal&status=saved'
        response = self.client.get(url, format='json')
        # check if saved count is correct or not
        expected_output = {
            "total": 1,
            "sent": 0,
            "saved": 1,
            "approved": 0,
            "received": 0
        }
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('stats'),
            expected_output
        )
        self.assertEqual(
            response.json().get('results')[0].get('status'),
            'saved'
        )

        url = reverse(
            'api_v1:appraisal:overview-report-list',
            kwargs={
                'organization_slug': slug
            }
        ) + f'?as=hr&slot={slot_id}'

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        expected_output = {
            "Self Appraisal": {
                "eligible_employees": 1,
                "non_eligible_employees": 2,
                "saved": 1,
                "pending": 1,
                "approved": 0,
                "submitted_on_time": 0,
                "submitted_after_deadline": 0
            }
        }
        self.assertEqual(
            response.json().get('appraisal_type_stats')[0],
            expected_output
        )


class TestAppraisalApprove(AppraiserSettingBaseMixin):
    def url(self, **kwargs):
        if not kwargs:
            return reverse(
                'api_v1:appraisal:appraiser-with-respect-to-appraisee-approve-given-answer',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                }
            )
        return reverse(
            'api_v1:appraisal:appraiser-with-respect-to-appraisee-approve-given-answer',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                **kwargs
            }
        )

    def test_approve_given_answer(self):
        appraisal = AppraisalFactory(
            appraisee_id=self.admin.id, appraiser_id=self.admin.id, answer_committed=True,
            question_set=question_set(), total_score=10,
            sub_performance_appraisal_slot=self.performance_appraisal_slot
        )
        url = self.url(
            appraiser_id=self.admin.id,
            appraisee_id=self.admin.id,
            sub_performance_appraisal_slot_id=appraisal.sub_performance_appraisal_slot.id
        ) + "?appraisal_type=self_appraisal"
        data = {
            "approve": True
        }
        response = self.client.post(
            url,
            data=data,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_score_deduction_condition(self):
        appraisal = AppraisalFactory(
            appraisee_id=self.admin.id,
            appraiser_id=self.admin.id,
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            answer_committed=True,
            deadline=get_today(with_time=True),
            committed_at=get_today(with_time=True) + timedelta(days=2),
            approved_at=get_today(with_time=True) + timedelta(days=2),
            question_set=question_set(),
            total_score=10
        )

        DeadlineExceedScoreDeductionConditionFactory(
            sub_performance_appraisal_slot=appraisal.sub_performance_appraisal_slot,
            total_exceed_days_from=1,
            total_exceed_days_to=2,
            deduction_type=PERCENTAGE,
            deduct_value=10
        )

        url = self.url(
            appraiser_id=self.admin.id,
            appraisee_id=self.admin.id,
            sub_performance_appraisal_slot_id=appraisal.sub_performance_appraisal_slot.id
        ) + "?appraisal_type=self_appraisal"

        self.client.post(
            url,
            data={
                "approve": True
            },
            format='json'
        )
        final_score = Appraisal.objects.first().final_score
        self.assertEqual(
            final_score,
            2.7
        )

class TestSelfAppraiserSetting(AppraiserSettingBaseMixin):
    def setUp(self):
        super().setUp()


    def url(self, **kwargs):
        if not kwargs:
            return reverse(
                'api_v1:appraisal:appraisee-with-respect-to-appraiser-resend-form',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
                }
            )
        return reverse(
            'api_v1:appraisal:appraiser-with-respect-to-appraisee-resend-form',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
                **kwargs
            }
        )

    def test_resend_pa_form_with_reason(self):
        appraisal = AppraisalFactory(appraisee_id=self.admin.id, appraiser_id=self.admin.id)
        data = {
            "reason": "Resent"
        }
        url = self.url(appraiser_id=self.admin.id,
                       appraisee_id=self.admin.id,
                       sub_performance_appraisal_slot_id=appraisal.sub_performance_appraisal_slot.id
                       ) + "?appraisal_type=self_appraisal"
        response = self.client.post(url,
                                    data=data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        response = self.client.post(url,
                                    data={},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_resend_pa_form_without_reason(self):
        appraisal = AppraisalFactory(appraisee_id=self.admin.id, appraiser_id=self.admin.id)
        data = {
            "reason": "Resent"
        }
        url = self.url(appraiser_id=self.admin.id,
                       appraisee_id=self.admin.id,
                       sub_performance_appraisal_slot_id=appraisal.sub_performance_appraisal_slot.id
                       ) + "?appraisal_type=self_appraisal"

        response = self.client.post(url,
                                    data={},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
