from copy import deepcopy

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import AppraisalFactory, \
    SubPerformanceAppraisalSlotModeFactory, PerformanceAppraisalYearFactory, \
    SubPerformanceAppraisalSlotFactory
from irhrs.appraisal.constants import (
    SELF_APPRAISAL,
    SUBORDINATE_APPRAISAL,
    SUPERVISOR_APPRAISAL,
    PEER_TO_PEER_FEEDBACK
)
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalYearWeight
from irhrs.appraisal.models.question_set import PerformanceAppraisalQuestionSet
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.questionnaire.api.v1.tests.factory import QuestionCategoryFactory, QuestionFactory
from irhrs.questionnaire.models.helpers import PERFORMANCE_APPRAISAL, LONG

User = get_user_model()


class TestPerformanceAppraisalQuestionSet(RHRSTestCaseWithExperience):
    organization_name = "Necrophos"
    users = [
        ('admin@gmail.com', 'hellonepal', 'Male', 'Manager'),
        ('luffy@onepiece.com', 'passwordissecret', 'Female', 'Supervisor'),
        ('bill@onepiece.com', 'passwordissecret', 'Female', 'Supervisor'),
    ]
    fake = Factory.create()

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.users = User.objects.all()
        self.question_category = QuestionCategoryFactory(
            category=PERFORMANCE_APPRAISAL,
            organization=self.organization
        )
        self.question = QuestionFactory(
            answer_choices=LONG,
            question_type=PERFORMANCE_APPRAISAL,
            organization=self.organization,
            category=self.question_category
        )
        self.performance_appraisal_year = PerformanceAppraisalYearFactory()
        self.performance_appraisal_slot = SubPerformanceAppraisalSlotFactory(
            performance_appraisal_year=self.performance_appraisal_year
        )
        SubPerformanceAppraisalSlotModeFactory(
            sub_performance_appraisal_slot=self.performance_appraisal_slot,
            appraisal_type=SELF_APPRAISAL,
            weightage=100
        )

    @property
    def data(self):
        return {
            'name': self.fake.word(),
            'description': self.fake.word(),
            'questions': [self.question.id],
            'sections': []
        }

    def url(self, pk=None):
        kwargs = {'organization_slug': self.organization.slug}
        view_name = 'api_v1:appraisal:appraisal-question-set' + ('-detail' if pk else '-list')
        if pk:
            kwargs['pk'] = pk
        return reverse(view_name, kwargs=kwargs)

    def do_create(self, data):
        return self.client.post(
            self.url(),
            data=data,
            format='json'
        )

    def test_create(self):
        data = deepcopy(self.data)
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_pa_questions_without_open_ended_field(self):
        payload = {
            "title": "<p>open ended question<br></p>",
            "description": "open ended question",
            "answer_choices": "short-text",
            "weightage": 0,
            "category": self.question_category.slug,
            "order": "0",
            "answers": [],
        }
        url = self.create_questionnaire_url
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_pa_questions_without_weightage_field(self):
        payload = {
            "title": "<p>no weightage question<br></p>",
            "description": "no weightage question",
            "answer_choices": "short-text",
            "category": self.question_category.slug,
            "order": "0",
            "answers": [],
        }
        url = self.create_questionnaire_url
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @property
    def create_questionnaire_url(self):
        return reverse(
            'api_v1:questionnaire:questions-repo-list',
            kwargs={
                'organization_slug': self.organization.slug,
            }
        )

    def test_update(self):
        new_data = deepcopy(self.data)
        new_data.update({
            'name': self.fake.word(),
            'questions': []
        })

        self.do_create(self.data)
        instance = PerformanceAppraisalQuestionSet.objects.first()
        response = self.client.put(
            self.url(pk=instance.id),
            data=new_data,
            format='json'
        )

        instance.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_destroy(self):
        self.do_create(self.data)
        instance = PerformanceAppraisalQuestionSet.objects.first()
        response = self.client.delete(
            self.url(pk=instance.id),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list(self):
        self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def appraiser_with_appraisee_url(self, appraisee_id):
        return reverse(
            'api_v1:appraisal:appraiser-with-respect-to-appraisee-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'appraisee_id': appraisee_id,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
            }
        ) + '?appraisal_type=self_appraisal'

    @property
    def send_answer_url(self):
        return reverse(
            'api_v1:appraisal:appraisee-with-respect-to-appraiser-answer',
            kwargs={
                'organization_slug': self.organization.slug,
                'appraiser_id': self.admin.id,
                'appraisee_id': self.admin.id,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
            }
        ) + '?appraisal_type=self_appraisal'

    def test_score_displays_correctly_in_percentage(self):
        total_scores = [6, 3, 0]
        for user, total_score in zip(self.created_users, total_scores):
            AppraisalFactory(
                sub_performance_appraisal_slot=self.performance_appraisal_slot,
                question_set=self.question_payload,
                start_date=get_today(with_time=True),
                deadline=get_today(with_time=True) + relativedelta(days=1),
                answer_committed=True,
                committed_at=get_today(with_time=True) + relativedelta(hours=1),
                approved_at=None,
                total_score=total_score,
                score_deduction_factor=0,
                appraisee_id=user.id,
                appraiser_id=user.id
            )

        self.client.post(self.send_answer_url, data=self.question_payload, format="json")
        self.client.post(self.approve_url(self.admin.id))
        response = self.client.get(self.appraiser_with_appraisee_url(self.admin.id))
        self.assertEqual(response.json().get('results')[0]['percentage_score'], 50)
        self.client.force_login(self.created_users[1])
        self.client.post(self.approve_url(self.created_users[1].id))
        self.client.get(self.appraiser_with_appraisee_url(self.created_users[1].id))
        self.client.force_login(self.created_users[2])
        self.client.post(self.approve_url(self.created_users[2].id))
        self.client.get(self.appraiser_with_appraisee_url(self.created_users[2].id))

        self.client.force_login(self.admin)
        yearly_response = self.client.get(
            self.yearly_url
        )
        # value before sorting
        self.assertEqual(
            yearly_response.json().get("results")[0].get("full_name"), "admin admin")
        self.assertEqual(
            yearly_response.json().get("results")[1].get("full_name"), "luffy luffy")
        slot_response = self.client.get(
            self.slot_url
        )
        # data Before sorting
        self.assertEqual(
            slot_response.json().get("results")[0].get('full_name'),
            "admin admin"
        )
        self.assertEqual(
            slot_response.json().get("results")[1].get('full_name'),
            "luffy luffy"
        )
        ordering_url = self.slot_url + "&ordering=-score"
        slot_response = self.client.get(
            ordering_url
        )
        # data after sorting
        self.assertEqual(
            slot_response.json().get("results")[0].get('full_name'),
            "luffy luffy"
        )
        self.assertEqual(
            slot_response.json().get("results")[1].get('full_name'),
            "admin admin"
        )

        yearly_ordering_url = self.yearly_url + "&ordering=-score"
        yearly_response = self.client.get(
            yearly_ordering_url
        )
        # data after sorting
        self.assertEqual(
            yearly_response.json().get("results")[0].get("full_name"),
            "luffy luffy"
        )
        self.assertEqual(
            yearly_response.json().get("results")[1].get("full_name"),
            "admin admin"
        )

        first_user_total_average_score_of_slot = slot_response.json().get('results')[0] \
            .get('score').get('total_average')
        first_user_total_average_score_of_year = yearly_response.json().get('results')[0] \
            .get('score').get(self.performance_appraisal_slot.title)
        self.assertEqual(
            first_user_total_average_score_of_year,
            first_user_total_average_score_of_slot
        )

        second_user_total_average_score_of_slot = slot_response.json().get('results')[1] \
            .get('score').get('total_average')
        second_user_total_average_score_of_year = yearly_response.json().get('results')[1] \
            .get('score').get(self.performance_appraisal_slot.title)
        self.assertEqual(
            second_user_total_average_score_of_year,
            second_user_total_average_score_of_slot
        )

        first_user_total_average_score_of_year = yearly_response.json().get('results')[1] \
            .get('score').get('total_average_score')
        second_user_total_average_score_of_year = yearly_response.json().get('results')[0] \
            .get('score').get('total_average_score')

        first_user_yearly_percentage_from_db = SubPerformanceAppraisalYearWeight.objects.get(
            appraiser=self.admin
        ).percentage
        second_user_yearly_percentage_from_db = SubPerformanceAppraisalYearWeight.objects.get(
            appraiser=self.created_users[1]
        ).percentage

        self.assertEqual(
            first_user_total_average_score_of_year,
            first_user_yearly_percentage_from_db
        )

        self.assertEqual(
            second_user_total_average_score_of_year,
            second_user_yearly_percentage_from_db
        )

        slot_detail_response = self.client.get(
            self.slot_detail_url(self.admin.id)
        )

        self.assertEqual(
            slot_detail_response.json().get('average'),
            50
        )
        slot_detail_response = self.client.get(
            self.slot_detail_url(self.created_users[2].id)
        )
        # When Appraisal total is passed 0 we dont have any zero division error
        self.assertEqual(
            slot_detail_response.json().get('average'),
            0
        )

    @property
    def question_payload(self):
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
                            "is_mandatory": True,
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
                            "is_mandatory": True,
                        },
                    ],
                    "description": "",
                }
            ],
            "description": "",
        }

    @property
    def send_question_set(self):
        return reverse(
            'api_v1:appraisal:performance-appraisal-form-design-send-question-set',
            kwargs={
                'organization_slug': self.organization.slug,
            }
        )

    def approve_url(self, user_id):
        return reverse(
            'api_v1:appraisal:appraiser-with-respect-to-appraisee-approve-given-answer',
            kwargs={
                'organization_slug': self.organization.slug,
                'appraiser_id': user_id,
                'appraisee_id': user_id,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id
            }
        ) + '?appraisal_type=self_appraisal'

    @property
    def yearly_url(self):
        return reverse(
            'api_v1:appraisal:yearly-report-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'year_id': self.performance_appraisal_year.id,
            }
        ) + "?as=hr"

    @property
    def slot_url(self):
        return reverse(
            'api_v1:appraisal:slot-report-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
            }
        ) + "?as=hr"

    def slot_detail_url(self, appraisee_id):
        return reverse(
            'api_v1:appraisal:slot-report-report-for-appraisee',
            kwargs={
                'appraisal_type': 'self_appraisal',
                'appraisee_id': appraisee_id,
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.performance_appraisal_slot.id,
            }
        ) + "?as=hr"

    def test_summary_report_ordering(self):
        """
        The test covers subordinate appraisal type scenario. Similarly, it should work for other 3
        appraisal types.
        """

        final_scores = [15, 18, 0]
        total_scores = [15, 20, 0]
        appraisal_type = SELF_APPRAISAL
        order_by_mapper = {
            SELF_APPRAISAL: "self_appraisal",
            SUBORDINATE_APPRAISAL: "subordinate_appraisal",
            SUPERVISOR_APPRAISAL: "supervisor_appraisal",
            PEER_TO_PEER_FEEDBACK: 'peer_to_peer_feedback'
        }
        order_by = order_by_mapper[appraisal_type]
        for user, final_score, total_score in zip(self.created_users, final_scores, total_scores):
            AppraisalFactory(
                sub_performance_appraisal_slot=self.performance_appraisal_slot,
                appraisal_type=appraisal_type,
                total_score=total_score,
                final_score=final_score,
                appraisee_id=user.id,
                appraiser_id=user.id
            )
        ordering_url = self.slot_url + f"&ordering=-{order_by}"

        slot_response = self.client.get(ordering_url)
        self.assertEqual(slot_response.status_code, 200)

        results = slot_response.json()['results']
        ordered_scores = [
            (appraisee['full_name'], appraisee['score'][order_by])
            for appraisee in results
        ]
        expected_order = [('admin admin', 100.0), ('luffy luffy', 90.0), ('bill bill', 0.0)]
        self.assertEqual(ordered_scores, expected_order)
