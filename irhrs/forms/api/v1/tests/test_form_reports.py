import json
from os import path
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.questionnaire.models.questionnaire import Answer
from irhrs.questionnaire.models.helpers import (
    CHECKBOX,
    RADIO,
    SHORT,
    LONG,
    RATING_SCALE,
    DATE,
    TIME,
    DURATION,
    DATE_TIME,
    DATE_WITHOUT_YEAR,
    DATE_TIME_WITHOUT_YEAR,
    FILE_UPLOAD,
    MULTIPLE_CHOICE_GRID,
    CHECKBOX_GRID,
)
from irhrs.forms.api.v1.tests.payloads.user_1_payload \
    import payload as payload_1
from irhrs.forms.api.v1.tests.payloads.user_2_payload \
    import payload as payload_2
from irhrs.forms.api.v1.tests.payloads.user_3_payload \
    import payload as payload_3
from irhrs.forms.models import (
    UserFormIndividualQuestionAnswer,
    FormQuestion
)
from irhrs.forms.api.v1.tests.factory import (
    FormFactory,
    FormQuestionSetFactory,
    FormQuestionFactory,
    UserFormAnswerSheetFactory,
)


class TestFormReports(RHRSAPITestCase):
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
        # There will be three answer sheets in total
        self._populate_question_answers()

    def _create_questions(self):
        # create 12 questions with id 1 to 12
        form_questions = []
        FormQuestion.objects.all().delete()
        question_texts = [
            "Where do you live?",
            "Whats your favorite food?",
            "Whats your name?",
            "Explain about the sun.",
            "How much do you like chocolate?",
            "When did you last come to office?",
            "What time did you punch in at?",
            "How much time will it take to complete form reports?",
            "When does the world cup final start?",
            "In which day did the last world cup final take place?",
            "In which day and time did the last world cup final take place?",
            "Upload doctors appointment.",
            "Rate the following people(choose only one).",
            "Rate the following people(tick which apply).",
        ]
        self.answer_choices = [
            CHECKBOX,
            RADIO,
            SHORT,
            LONG,
            RATING_SCALE,
            DATE,
            TIME,
            DURATION,
            DATE_TIME,
            DATE_WITHOUT_YEAR,
            DATE_TIME_WITHOUT_YEAR,
            FILE_UPLOAD,
            MULTIPLE_CHOICE_GRID,
            CHECKBOX_GRID,
        ]
        self.question_set = FormQuestionSetFactory()
        for index, answer_choice in enumerate(self.answer_choices):
            question = FormQuestionFactory(
                id=(index+1),
                question__title=question_texts[index],
                question__answer_choices=answer_choice,
                question_section__question_set=self.question_set
            )
            if answer_choice == CHECKBOX:
                self._create_multiple_mcq_answer_choices(question)
            elif answer_choice == RADIO:
                self._create_single_answer_choices(question)
            elif answer_choice in [CHECKBOX_GRID, MULTIPLE_CHOICE_GRID]:
                self._create_grid_questions(question)

            form_questions.append(question)
        return form_questions

    def _create_grid_questions(self, form_question):
        question = form_question.question
        question.extra_data = {
            "rows": ["Ram", "Shyam", "Hari"],
            "columns": ["Wise", "Stupid", "Cool"],
            "all_rows_mandatory": False
        }
        question.save()

    def _create_multiple_mcq_answer_choices(self, question):
        choices = ["Kathmandu", "Bhaktapur", "Lalitpur", "Gorkha"]
        for choice in choices:
            Answer.objects.create(
                question=question.question,
                order=1,
                title=choice
            )

    def _create_single_answer_choices(self, question):
        choices = ["Ice-cream", "Rice", "Coffee"]
        for choice in choices:
            Answer.objects.create(
                question=question.question,
                order=1,
                title=choice
            )

    def populate_individual_question_answers(self, questions, answer_sheet, payload):
        for ques, ans in zip(questions, payload):
            UserFormIndividualQuestionAnswer.objects.create(
                question=ques,
                answer_sheet=answer_sheet,
                answers=ans["answers"]
            )

    def _create_sheets(self):
        sheets = []
        users = [self.user1, self.user2, self.user3]
        for user in users:
            sheet = UserFormAnswerSheetFactory(
                user=user,
                form=self.report_form,
                is_approved=True,
            )
            sheets.append(sheet)
        return sheets

    def _populate_question_answers(self):
        payloads = [payload_1, payload_2, payload_3]
        questions = self._create_questions()
        self.report_form = FormFactory(
            name="Report form",
            organization=self.organization,
            question_set=self.question_set
        )
        sheets = self._create_sheets()
        for sheet, payload in zip(sheets, payloads):
            self.populate_individual_question_answers(
                answer_sheet=sheet,
                questions=questions,
                payload=payload
            )

    def test_multiple_select_aggregation_works(self):
        url = reverse(
            "api_v1:forms:forms-report-list",
            kwargs={
                "organization_slug": self.organization.slug,
                "form_id": self.report_form.id,
            },
        ) + "?as=hr"
        self.client.force_login(self.admin)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_users_from_answer_api_for_grid_type_works(self):
        url = reverse(
            "api_v1:forms:forms-report-return-users",
            kwargs={
                "organization_slug": self.organization.slug,
                "form_id": self.report_form.id,
                "question_id": self.answer_choices.index(CHECKBOX_GRID) + 1
            },
        )
        self.client.force_login(self.admin)
        payload = {
            "Hari": ["Cool"]
        }
        res = self.client.post(
            url,
            data=payload,
            format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            len(res.json()['users']),
            2
        )

    def test_users_from_answer_api_works(self):
        url = reverse(
            "api_v1:forms:forms-report-return-users",
            kwargs={
                "organization_slug": self.organization.slug,
                "form_id": self.report_form.id,
                "question_id": self.answer_choices.index(CHECKBOX) + 1
            },
        )
        self.client.force_login(self.admin)
        payload = {
            "answers": "Kathmandu"
        }
        res = self.client.post(
            url,
            data=payload,
            format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            len(res.json()['users']),
            1
        )

    def test_list_paginated_answer_response_api_works(self):
        url = reverse(
            "api_v1:forms:forms-report-list-response",
            kwargs={
                "organization_slug": self.organization.slug,
                "form_id": self.report_form.id,
                "question_id": self.answer_choices.index(LONG) + 1
            },
        )
        self.client.force_login(self.admin)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)


    def test_list_aggregated_paginated_answer_response_api_works(self):
        url = reverse(
            "api_v1:forms:forms-report-list-aggregated-response",
            kwargs={
                "organization_slug": self.organization.slug,
                "form_id": self.report_form.id,
                "question_id": self.answer_choices.index(DATE) + 1
            },
        )
        self.client.force_login(self.admin)
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        expected_result = [
            {'answer': [], 'count': 1},
            {'answer': '2021-01-01', 'count': 2}
        ]
        self.assertListEqual(
            res.json()['results'],
            expected_result
        )
