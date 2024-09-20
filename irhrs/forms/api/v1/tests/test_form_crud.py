import base64
from os import path
from django.contrib.auth import get_user_model
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.forms.constants import APPROVED, DENIED
from irhrs.questionnaire.models.helpers import FILE_UPLOAD
from irhrs.questionnaire.api.v1.tests.factory import QuestionFactory
from irhrs.forms.api.v1.tests.factory import (
    FormFactory,
    UserFormFactory,
    UserFormAnswerSheetFactory,
    FormQuestionFactory,
    FormQuestionSectionFactory,
    FormQuestionSetFactory,
    FormApprovalSettingLevelFactory,
    FormAnswerSheetApprovalFactory,
)
from irhrs.core.constants.payroll import (
    SUPERVISOR,
    EMPLOYEE,
    ALL,
    FIRST,
    SECOND,
    THIRD
)
from irhrs.users.models import UserSupervisor
from irhrs.forms.models import (
    UserForm,
    UserFormAnswerSheet,
    AnonymousFormAnswerSheet,
    FormQuestionSet,
    FormQuestionSection,
    FormApprovalSettingLevel,
)


USER = get_user_model()


class TestForms(RHRSAPITestCase):
    users = [
        ("hr@email.com", "secret", "Male"),
        ("engineer@email.com", "secret", "Male"),
        ("accountant@email.com", "secret", "Male"),
        ("clerk@email.com", "secret", "Male"),
        ("luffy@email.com", "secret", "Male"),
    ]
    organization_name = "Google Inc."

    def setUp(self):
        super().setUp()
        self.user1 = self.created_users[1]
        self.user2 = self.created_users[2]
        self.user3 = self.created_users[3]
        self.user4 = self.created_users[4]

    def test_form_list_url_works(self):
        url = reverse(
            "api_v1:forms:forms-list",
            kwargs={"organization_slug": self.organization.slug},
        )
        self.client.force_login(self.user1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_form_creation_works(self):
        payload = {
            "name": "Covid Form",
            "deadline": None,
            "disclaimer_text": "I agree",
            "is_muliple_submittable": False,
            "is_anonymously_fillable": False,
            "is_archived": False,
        }

        url = reverse(
            "api_v1:forms:forms-list",
            kwargs={"organization_slug": self.organization.slug},
        )
        self.client.force_login(self.admin)
        res = self.client.post(url, data=payload, format="json")
        self.assertEqual(res.status_code, 201)

    def test_form_question_set_creation_works(self):
        QuestionFactory(category__organization=self.organization)
        QuestionFactory()
        payload = {"name": "set A", "description": "This is set A", "sections": []}
        url = reverse(
            "api_v1:forms:form-question-set-list",
            kwargs={"organization_slug": self.organization.slug},
        )
        self.client.force_login(self.admin)
        res = self.client.post(url, data=payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            FormQuestionSet.objects.filter(name=res.json()["name"]).exists()
        )

    def test_form_question_section_creation_works(self):
        question_set = FormQuestionSetFactory()
        payload = {
            "title": "dasd",
            "description": "sad",
            "total_weightage": 0,
            "marginal_weightage": 0,
        }

        url = reverse(
            "api_v1:forms:form-question-section-list",
            kwargs={
                "organization_slug": self.organization.slug,
                "question_set": question_set.id,
            },
        ) + "?as=hr"
        self.client.force_login(self.admin)
        res = self.client.post(url, data=payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            FormQuestionSection.objects.filter(title=res.json()["title"]).exists()
        )

    def test_form_approval_creation_works(self):
        self.form_one = FormFactory(
            name="Covid-19 Form",
            organization=self.organization,
        )
        payload = {
            "approvals": [
                {
                    "approve_by": "Employee",
                    "supervisor_level": None,
                    "employee": self.user1.id,
                }
            ],
        }
        url = reverse(
            "api_v1:forms:form-approval-setting-list",
            kwargs={
                "organization_slug": self.organization.slug,
                "form": self.form_one.id,
            },
        )
        self.client.force_login(self.admin)
        res = self.client.post(url, data=payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            FormApprovalSettingLevel.objects.filter(form__id=self.form_one.id).exists()
        )

    def test_form_assign_works(self):
        self.form_one = FormFactory(
            name="Covid-19 Form",
            organization=self.organization,
        )
        payload = {
            "users": [self.user1.id, self.user2.id],
        }
        url = reverse(
            "api_v1:forms:forms-assignment-list",
            kwargs={
                "organization_slug": self.organization.slug,
                "form_id": self.form_one.id,
            },
        )
        self.client.force_login(self.admin)
        res = self.client.post(url, data=payload, format="json")
        self.assertTrue(res.status_code, 200)
        self.assertTrue(
            UserForm.objects.filter(form=self.form_one, user=self.user1).exists()
        )
        self.assertTrue(
            UserForm.objects.filter(form=self.form_one, user=self.user2).exists()
        )

    def test_form_assigned_to_user_list_works(self):
        self.form1 = FormFactory(organization=self.organization)
        self.form2 = FormFactory(organization=self.organization)

        UserFormFactory(form=self.form1, user=self.user1)

        url = reverse(
            "api_v1:forms:forms-list",
            kwargs={"organization_slug": self.organization.slug},
        )
        self.client.force_login(self.user1)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 1)

        # check that count is 2 if viewed by HR
        hr_url = url + "?as=hr"
        self.client.force_login(self.admin)
        res = self.client.get(hr_url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 2)

    def _create_form_questions(self, is_anonymously_fillable=False):
        question_ids = []
        question_section = FormQuestionSectionFactory()
        # create 5 questions
        for question in range(5):
            form_question = FormQuestionFactory(question_section=question_section)
            question_ids.append(form_question.id)

        form_details = dict(
            organization=self.organization,
            question_set=question_section.question_set,
            is_draft=False
        )
        if is_anonymously_fillable:
            form_details.update({"is_anonymously_fillable": True})
        form = FormFactory(**form_details)
        return form, question_ids

    @property
    def question_answer_payload(self):
        file_upload_question = QuestionFactory(
            answer_choices=FILE_UPLOAD
        )
        # with self.get_blob('minimal.pdf') as pdf:
        #     base_64_header = 'data:application/pdf;base64,'
        #     pdf_file_decoded = base_64_header + base64.b64encode(pdf.read()).decode('utf-8')
        #     image_data = pdf_file_decoded

        payload = {
            "is_draft": False,
            "question": {
                    "description": "",
                    "id": 16,
                    "name": "Job Vacancy Questions",
                    "sections": [
                        {
                            "description": "",
                            "id": 11,
                            "questions": [
                                {
                                    "id": file_upload_question.id,
                                    "is_mandatory": False,
                                    "order": 1,
                                    "question": {
                                        "answer_choices": "file-upload",
                                        "answers": [{
                                            "file_name": "",
                                            "file_content": ""
                                        }],
                                        "category": {
                                            "slug": "vacancy-questions",
                                            "title": "Vacancy Questions",
                                        },
                                        "description": "",
                                        "id": self.question_ids[0],
                                        "is_open_ended": True,
                                        "order": 1,
                                        "question_type": "vacancy",
                                        "rating_scale": 5,
                                        "title": "<p>What is you hobby?</p>",
                                        "weightage": 0,
                                    },
                                },
                                {
                                    "id": 53,
                                    "is_mandatory": False,
                                    "order": 1,
                                    "question": {
                                        "answer_choices": "short-text",
                                        "answers": ["sd"],
                                        "category": {
                                            "slug": "vacancy-questions",
                                            "title": "Vacancy Questions",
                                        },
                                        "description": "",
                                        "id": self.question_ids[0],
                                        "is_open_ended": True,
                                        "order": 1,
                                        "question_type": "vacancy",
                                        "rating_scale": 5,
                                        "title": "<p>What is you hobby?</p>",
                                        "weightage": 0,
                                    },
                                },
                                {
                                    "id": 55,
                                    "is_mandatory": False,
                                    "order": 3,
                                    "question": {
                                        "answer_choices": "single-mcq",
                                        "answers": [
                                            {
                                                "id": 307,
                                                "is_correct": False,
                                                "order": 0,
                                                "remarks": "",
                                                "title": "Bhaktapur",
                                            },
                                            {
                                                "id": 308,
                                                "is_correct": False,
                                                "order": 0,
                                                "remarks": "",
                                                "title": "Kathmandu",
                                            },
                                            {
                                                "id": 309,
                                                "is_correct": True,
                                                "order": 0,
                                                "remarks": "",
                                                "title": "New Delhi",
                                            },
                                            {
                                                "id": 310,
                                                "is_correct": False,
                                                "order": 0,
                                                "remarks": "",
                                                "title": "Senghai",
                                            },
                                        ],
                                        "category": {
                                            "slug": "vacancy-questions",
                                            "title": "Vacancy Questions",
                                        },
                                        "description": "",
                                        "id": self.question_ids[1],
                                        "is_open_ended": True,
                                        "order": 3,
                                        "question_type": "vacancy",
                                        "rating_scale": 5,
                                        "title": "<p>What is the capital city of Nepal?</p>",
                                        "weightage": 0,
                                    },
                                },
                                {
                                    "id": 59,
                                    "is_mandatory": False,
                                    "order": 7,
                                    "question": {
                                        "answer_choices": "rating-scale",
                                        "answers": [5],
                                        "category": {
                                            "slug": "vacancy-questions",
                                            "title": "Vacancy Questions",
                                        },
                                        "description": "",
                                        "id": self.question_ids[2],
                                        "is_open_ended": True,
                                        "order": 7,
                                        "question_type": "vacancy",
                                        "rating_scale": 10,
                                        "temp_score": 5,
                                        "title": "<p>Rate you skill from 1 to 10.</p>",
                                        "weightage": 0,
                                    },
                                },
                            ],
                            "title": "Job Vacancy Questions",
                        }
                    ],
                }
        }
        return payload


    def test_answer_sheet_url_works(self):
        self.form, self.question_ids = self._create_form_questions()

        answer_sheet = UserFormAnswerSheetFactory(
            form=self.form,
            user=self.user1,
            is_draft=False,
        )

        # test list
        url = reverse(
            "api_v1:forms:forms-answer-sheets-list",
            kwargs={"organization_slug": self.organization.slug}
        ) + "?as=hr"
        self.client.force_login(self.admin)
        res = self.client.get(url, format="json")
        self.assertTrue(res.status_code, 200)
        self.assertTrue(res.json()['count'], 1)
        self.assertEqual(
            res.json()['results'][0]['status'],
            APPROVED
        )

        # test retrieve
        url = reverse(
            "api_v1:forms:forms-answer-sheets-detail",
            kwargs={
                "organization_slug": self.organization.slug,
                "pk": answer_sheet.id
            }
        )
        self.client.force_login(self.user1)
        res = self.client.get(url, format="json")
        self.assertTrue(res.status_code, 200)
        self.assertTrue(
            res.json()['status'],
            APPROVED
        )

    def assign_supervisor(self):
        """ user3 has 2 supervisors, user 1 and admin"""
        supervisors = [
            UserSupervisor(
                user=self.user3,
                supervisor=self.user1,
                authority_order=1,
                approve=True, deny=True, forward=False
            ),
            UserSupervisor(
                user=self.user3,
                supervisor=self.admin,
                authority_order=2,
                approve=True, deny=True, forward=False
            )
        ]
        UserSupervisor.objects.bulk_create(supervisors)

    def test_answer_sheet_approval_works(self):
        self.form, self.question_ids = self._create_form_questions()
        self.assign_supervisor()
        answer_sheet = UserFormAnswerSheetFactory(
            form=self.form,
            user=self.user3,
        )
        FormApprovalSettingLevelFactory(
            form=self.form,
            approve_by=SUPERVISOR,
            supervisor_level=SECOND,
            approval_level=1
        )
        FormApprovalSettingLevelFactory(
            form=self.form,
            employee=self.user4,
            approve_by=EMPLOYEE,
            approval_level=2
        )
        sheet_approval_1 = FormAnswerSheetApprovalFactory.create(
            answer_sheet=answer_sheet,
            approve_by=EMPLOYEE,
            approval_level=1
        )
        sheet_approval_1.employees.set([self.admin])
        sheet_approval_2 = FormAnswerSheetApprovalFactory.create(
            answer_sheet=answer_sheet,
            approve_by=EMPLOYEE,
            approval_level=2
        )
        sheet_approval_2.employees.set([self.user4])
        url = reverse(
            "api_v1:forms:forms-answer-sheets-take-action",
            kwargs={
                "organization_slug": self.organization.slug,
                "pk": answer_sheet.id
            }
        )
        payload = {
            "action": APPROVED,
            "remarks": "DONE"
        }
        print('---------- 1st approval')
        self.client.force_login(self.admin)
        res = self.client.post(
            url,
            data=payload,
            format="json"
        )
        print(res.json())
        print('---------- 2nd approval')
        self.client.force_login(self.user4)
        res = self.client.post(
            url,
            data=payload,
            format="json"
        )
        print(res.json())
        print('---------- 3rd approval')
        self.client.force_login(self.user2)
        res = self.client.post(
            url,
            data=payload,
            format="json"
        )
        print(res.json())
        self.assertEqual(res.status_code, 400)

    def test_anonymous_form_url_works(self):
        self.form_one = FormFactory(
            name="Covid-19 Form",
            organization=self.organization,
            is_anonymously_fillable=True
        )

        url = reverse(
            "api_v1:forms:anonymous-form-detail",
            kwargs={
                "organization_slug": self.organization.slug,
                "uuid": self.form_one.uuid,
            },
        )
        res = self.client.get(url)
        self.assertTrue(res.status_code, 200)
        print(res.json())


    def test_non_anonymous_form_update_to_anonymous_works(self):
        self.form = FormFactory(
            name="Covid-19 Form",
            organization=self.organization,
        )
        UserFormFactory(form=self.form, user=self.user1)
        UserFormAnswerSheetFactory(
            form=self.form,
            user=self.user1,
            is_draft=False
        )
        url = reverse(
            "api_v1:forms:forms-detail",
            kwargs={
                "organization_slug": self.organization.slug,
                "pk": self.form.id
            },
        ) + "?as=hr"
        payload = {
            "name": "Covid Form",
            "description": "YOYO",
            "disclaimer_text": "I agree. Do you?",
            "is_anonymously_fillable": True,
            "is_archived": False,
        }
        self.client.force_login(self.admin)
        response = self.client.patch(
            url,
            data=payload,
            format="json"
        )
        print(response.json())
        self.assertEqual(response.status_code, 400)
        # delete all answer sheets but assignment exists
        answer_sheets = UserFormAnswerSheet.objects.all()
        answer_sheets.delete()
        payload = {
            "name": "Covid Form",
            "description": "YOYO",
            "disclaimer_text": "I agree. Do you?",
            "is_archived": False,
            "is_anonymously_fillable": True,
        }
        response = self.client.patch(
            url,
            data=payload,
            format="json"
        )
        self.assertTrue(response.status_code, 200)
        self.assertEqual(
            self.form.form_assignments.all().count(),
            0
        )
