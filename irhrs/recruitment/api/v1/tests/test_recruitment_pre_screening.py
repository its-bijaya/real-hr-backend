from django.urls import reverse
from rest_framework import status


from irhrs.organization.api.v1.tests.factory import EmploymentJobTitleFactory, \
    EmploymentLevelFactory, EmploymentStatusFactory, KnowledgeSkillAbilityFactory
from irhrs.recruitment.models.job import Job
from irhrs.recruitment.models.common import Template
from irhrs.recruitment.constants import APPLIED, COMPLETED, EXTERNAL_USER_LETTER, MORNING, \
    PRE_SCREENING, SCREENED
from irhrs.recruitment.models.question import QuestionSet
from irhrs.recruitment.models import PreScreening
from irhrs.organization.models import organization
from irhrs.recruitment.api.v1.tests.factory import JobApplyFactory, JobFactory
from irhrs.recruitment.constants import PENDING
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.users.models.supervisor_authority import UserSupervisor


class TestRecruitmentPreScreeningAPI(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ('admin@example.com', 'admin', 'Male'),
        ('normal@example.com', 'normal', 'Male'),
    ]

    def setUp(self):
        super().setUp()
        self.job = Job.objects.create(
            title=EmploymentJobTitleFactory(organization=self.organization),
            organization=self.organization,
            vacancies=1,
            employment_status=EmploymentStatusFactory(organization=self.organization),
            preferred_shift=MORNING,
            employment_level=EmploymentLevelFactory(organization=self.organization),
            salary_visible_to_candidate=False,
            alternate_description="Nothing",
            description="",
            hiring_info={"pre_screening_letter": None},
            specification="Assistant",
            is_skill_specific=True,
            education_degree="Bachlor",
            education_program=None,
        )

        self.url = reverse(
            'api_v1:recruitment:pre_screening-list',
            kwargs={
                'job_slug': self.job.slug
            }
        )

        self.initialize_url = reverse(
            'api_v1:recruitment:pre_screening-initialize',
            kwargs={
                'job_slug': self.job.slug
            }
        ) + f'?organization={self.organization.slug}&as=hr'

        self.screened_url_completed = reverse(
            'api_v1:recruitment:pre_screening-list',
            kwargs={
                'job_slug': self.job.slug
            }
        )

    def screened_url(self, pk):
        return reverse(
            'api_v1:recruitment:pre_screening-complete',
            kwargs={
                'job_slug': self.job.slug, 'pk': pk
            }
        )

    def test_recruitment_pre_screening(self):
        self.client.force_login(self.admin)
        self.job.skills.add(KnowledgeSkillAbilityFactory(
            organization=self.organization
        ))
        job_apply = JobApplyFactory(
            job=self.job
        )

        question_set1 = QuestionSet.objects.create(name="Question 1", form_type=PRE_SCREENING,
                                                   is_archived=False)
        template1 = Template.objects.create(
            title="Mail_tempalte",
            message="This is the template for writing Mail",
            type=EXTERNAL_USER_LETTER,
            organization=self.organization
        )

        payload = {
            'responsible_person': self.created_users[1].id,
            'job_apply': job_apply.id,
            'score': 50.0,
            'question_set': question_set1.id,
            'email_template': template1.slug,
        }

        # 1. Should receive candidate in pending tab after initializing the prescreening process
        response = self.client.post(
            self.initialize_url,
            data={
                "score": 50
            },
            format='json',
        )

        self.assertTrue(
            PreScreening.objects.filter(status=PENDING).exists()
        )

        answer_payload = {
            "id": 9,
            "name": "Preliminary shortlisting Questions",
            "score": 8,
            "sections": [
                {
                    "id": 3,
                    "title": "Preliminary shortlisting Questions",
                    "questions": [
                        {
                            "id": 4,
                            "order": 1,
                            "question": {
                                "id": 207,
                                "order": 1,
                                "score": 4,
                                "title": "<p>Rate the overall candidate behavior and attitude.</p>",
                                "answers": [3, 3.5, 1, 1.5, 2, 2.5, 3, 4],
                                "category": {
                                    "slug": "preliminary-shortlisting-assistant",
                                    "title": "Preliminary shortlisting -Assistant"
                                },
                                "weightage": 5,
                                "temp_score": 4,
                                "description": "",
                                "ratingapi_v1:recruitment:pre_screening-detail_scale": 5,
                                "is_open_ended": False,
                                "question_type": "pre_screening",
                                "answer_choices": "rating-scale"
                            },
                            "is_mandatory": False
                        }
                    ],
                    "description": ""
                }
            ],
            "percentage": 80,
            "description": "",
            "total_score": 10,
            "overall_remarks": "<p>He was Good</p>"
        }

        patch_url = reverse(
            'api_v1:recruitment:pre_screening-detail',
            kwargs={
                'job_slug': self.job.slug,
                'pk': PreScreening.objects.first().id
            }
        )

        response = self.client.patch(
            patch_url,
            data={
                "score": 5,
                "data": answer_payload
            },
            format='json'
        )

        self.assertEqual(
            PreScreening.objects.first().score,
            5
        )

        # 2. Should be able to set candidate completed after screened
        payload = {
            'responsible_person': self.created_users[1].id,
            'status': PENDING,
            'data': answer_payload,
            'score': 50.0
        }
        response = self.client.post(
            self.screened_url(PreScreening.objects.first().id),
            data={},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            PreScreening.objects.first().data,
            answer_payload
        )

        self.assertEqual(
            response.json().get('status'),
            'Completed'
        )

        # 3 Should be able to forward candidate to another supervisor
        patch_url_supervisor = reverse(
            'api_v1:recruitment:pre_screening-detail',
            kwargs={
                'job_slug': self.job.slug,
                'pk': PreScreening.objects.first().id
            }
        )

        payload = {
            'assign': True,
            'question_set': 18,
            'responsible_person': self.created_users[1].id,
            'scheduled_at': "2021-10-06T10:18"
        }

        response = self.client.patch(
            patch_url_supervisor,
            data={
                'responsible_person': self.created_users[0].id
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.json().get('responsible_person'),
            PreScreening.objects.first().responsible_person.id
        )

        self.change_supervisor_url = reverse(
            'api_v1:recruitment:pre_screening-list',
            kwargs={
                'job_slug': self.job.slug
            }
        )

        response = self.client.get(
            self.change_supervisor_url
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            PreScreening.objects.first().responsible_person.id,
            response.json().get('results')[0].get('responsible_person').get('id')
        )

        # 4 Assigned supervisor should be able to screen the candidate
        # When candidate is screened by supervisor candidate moves to completed tab within preliminary shortlist
        # We should have candidate in completed tab to pass the test
        person_as_supervisor = UserSupervisor.objects.create(
            user=self.created_users[0],
            supervisor=self.created_users[1],
            user_organization=self.organization,
            supervisor_organization=self.organization
        )

        get_url_candidate_screened = reverse(
            'api_v1:recruitment:pre_screening-detail',
            kwargs={
                'job_slug': self.job.slug,
                'pk': PreScreening.objects.first().id
            }
        )

        payload = {
            'assign': True,
            'question_set': 18,
            'scheduled_at': "2021-10-06T10:18"
        }

        response = self.client.patch(
            get_url_candidate_screened,
            data={
                'responsible_person': self.created_users[1].id
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.json().get('status'),
            COMPLETED
        )

        # 5 Screened candidate should be in forwarded tab of prliminary shortlist and pending tab of fianl shortlist
        payload = {
            "responsible_person": self.created_users[0].id,
            "score": 50,
        }

        self.post_url = reverse(
            'api_v1:recruitment:pre_screening-post_screening_forward',
            kwargs={
                'job_slug': self.job.slug
            }
        )

        response = self.client.post(
            self.post_url,
            payload,
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.json().get('status'),
            'Forwarded'
        )
