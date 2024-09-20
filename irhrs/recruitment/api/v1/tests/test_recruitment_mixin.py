from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.organization.api.v1.tests.factory import EmploymentJobTitleFactory, \
    EmploymentStatusFactory, EmploymentLevelFactory
from irhrs.recruitment.constants import MORNING
from irhrs.recruitment.models import Job


class TestRecruitmentMixin(RHRSAPITestCase):
    organization_name = "Aayulogic"
    users = [
        ('admin@example.com', 'admin', 'Male'),
        ('normal@example.com', 'normal', 'Male'),
        ('intern@example.com', 'normal', 'Male'),
        ('trainee@example.com', 'normal', 'Female'),
    ]

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
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
            education_degree="Bachelor",
            education_program=None,
        )

    @property
    def answer_payload(self):
        return {
            "id": 1,
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
