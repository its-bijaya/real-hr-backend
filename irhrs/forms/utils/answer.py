import re
import os
import sys
import base64
from mimetypes import guess_extension

import magic
from jsonschema import validate as validate_schema
from jsonschema.exceptions import ValidationError as SchemaValidationError
from django.conf import settings
from django.db.models import Exists, Q, OuterRef, Subquery
from django.core.files.base import ContentFile
from irhrs.questionnaire.models.questionnaire import Answer, Question
from rest_framework.exceptions import ValidationError

from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_today
from irhrs.core.utils.questions import validate_mandatory_questions
from irhrs.forms.constants import REQUESTED, APPROVED, DENIED
from irhrs.questionnaire.models.helpers import FILE_UPLOAD
from irhrs.forms.tasks.notification import send_notification_if_all_users_submitted
from irhrs.permission.constants.permissions import (
    FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS,
    FORM_PERMISSION,
    FORM_READ_ONLY_PERMISSION,
)
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
from irhrs.core.constants.payroll import (
    EMPLOYEE,
    ALL,
    FIRST,
    SECOND,
    THIRD
)
from irhrs.forms.models import (
    Form,
    UserForm,
    UserFormAnswerSheet,
    FormQuestion,
    UserFormIndividualQuestionAnswer,
    AnonymousFormIndividualQuestionAnswer,
    FormAnswerSheetApproval,
    AnonymousFormAnswerSheet,
    AnswerSheetStatus
)
from irhrs.users.models import UserSupervisor
from irhrs.forms.utils.approval import (
    get_next_approvers,
    get_next_approval_level
)

from irhrs.notification.utils import add_notification
from irhrs.notification.utils import notify_organization


char_types = (
    RATING_SCALE, LONG, SHORT, DATE, TIME, DURATION,
    DATE_TIME, DATE_WITHOUT_YEAR, DATE_TIME_WITHOUT_YEAR
)

grid_types = (
    MULTIPLE_CHOICE_GRID, CHECKBOX_GRID
)


def save_answer_to_db(context, answer_sheet, question_answer_json):
    if not question_answer_json:
        return
    sections = question_answer_json.get('sections')
    answers_list = []
    form = context.get('form')
    individual_qa_model = (
        AnonymousFormIndividualQuestionAnswer if form.is_anonymously_fillable
        else UserFormIndividualQuestionAnswer
    )
    for section in sections:
        questions = section.get('questions')
        if not questions:
            continue

        for question in questions:
            answer = question.get('question').get('answers')
            answer_choice = question.get('question').get('answer_choices')
            if not answer and answer_choice in char_types:
                answer = ['']
            form_question_id = question.get('id')
            individual_qa = individual_qa_model(
                answers=answer,
                question_id=form_question_id,
                answer_sheet=answer_sheet
            )
            answers_list.append(individual_qa)
        individual_qa_model.objects.filter(
            answer_sheet=answer_sheet
        ).delete()
        individual_qa_model.objects.bulk_create(answers_list)

def validate_answers(question_answer_json):
    if not question_answer_json:
        return
    sections = question_answer_json.get('sections')
    for section in sections:
        questions = section.get('questions')
        if not questions:
            continue

        for question in questions:
            form_question_id = question.get('id')
            form_questions = FormQuestion.objects.filter(id=form_question_id)
            if form_questions.exists():
                is_mandatory = form_questions.first().is_mandatory
            else:
                raise ValidationError({
                    "error": "Incorrect form quesiton id."
                })
            form_question = form_questions.first()
            extra_kwargs = {
                "form_question": form_question
            }
            question_answer = question.get('question')
            validate_mandatory_questions(question_answer, is_mandatory, **extra_kwargs)


def save_file_for_form(viewset, question, answer):
    """
    Decode base64, save the file and return
    details in an appropriate format
    """

    file_content = answer.get('file_content')
    file_name = answer.get('file_name')

    if file_content and file_name:
        try:
            mime_string, actual_content = file_content.split(',')
            decoded_file_content = base64.b64decode(actual_content)
            if mime_string:
                # search for the mime type string in the base64 encoded data
                mime_search = re.search('data:(.+?);', mime_string)
                if mime_search:
                    mime = mime_search.group(1)
                    guessed_ext = guess_extension(mime)
                    ext = guessed_ext[1:] if guessed_ext else ''
            else:
                file_mime_type = magic.from_buffer(decoded_file_content, mime=True)
                ext = guess_extension(file_mime_type) or ''
        except (AttributeError, ValueError, IndexError):
            raise ValidationError({"error": "File is not encoded correctly."})
        file_name = os.path.splitext(file_name)[0] + '.' + (ext or '')
        if ext not in settings.ACCEPTED_FILE_FORMATS_LIST:
            raise ValidationError({
                "error": "File type not supported."
            })

        attachment = ContentFile(decoded_file_content, name=file_name)

        # max size is 5 MB
        if sys.getsizeof(attachment) > 5242880:
            raise ValidationError({
                "error": "File size cannot be greater than 5 MB."
            })
        question_id = question.get('question').get('id')
        order = question.get('order')
        question = Question.objects.get(id=question['question']['id'])
        answer_obj = Answer.objects.create(
            question_id=question_id,
            order=order,
            attachment=attachment
        )
        saved_file_name = os.path.basename(answer_obj.attachment.url)
        return [
            {
                "file_name": file_name,
                "saved_file_name_only": saved_file_name,
                "file_url": answer_obj.attachment.url
            }
        ]

    return [
        {
            "file_name": "",
            "file_url": ""
        }
    ]

def save_files_from_answers(viewset, question_answer_json):
    """
    Iterate through the json and if answer type is file-upload,
    then save the base64 content in a file field and modify the json
    to store the file url instead of file content.
    """
    if not question_answer_json:
        return
    sections = question_answer_json.get("sections")
    for section_index, section in enumerate(sections):
        questions = section.get("questions")
        if not questions:
            continue

        for question_index, question in enumerate(questions):
            answer_type = question.get("question").get("answer_choices")
            answer = question.get("question").get("answers")
            if answer_type == FILE_UPLOAD:
                if answer:
                    file_url = answer[0].get('file_url')
                    if file_url:
                        continue
                    file_detail = save_file_for_form(viewset, question, answer[0])
                    question_answer_json["sections"][section_index]["questions"][
                        question_index
                    ]["question"]["answers"] = file_detail
    return question_answer_json


def save_answer(viewset, form, answer_sheet=None):
    question_answer = viewset.request.data.get('question')
    is_draft = viewset.request.data.get('is_draft', True)
    user = viewset.request.user
    assignment_exists = UserForm.objects.filter(user=user, form=form).exists()
    submission_exists = UserFormAnswerSheet.objects.filter(
        is_draft=False,
        user=user,
        form=form
    ).exists()
    if not form.is_multiple_submittable and submission_exists:
        raise ValidationError({
            "error": "This form is not multiple submittable and a submission already exists."
        })

    if form.is_archived:
        raise ValidationError({
            "error": "Cannot submit answers on archived form."
        })
    if not assignment_exists:
        raise ValidationError({
            "error": "Current user is not assigned to this form."
        })

    # if user clicks "save as draft" but a draft already exists,
    # set `answer_sheet` variable to existing draft for single submit
    if not answer_sheet and is_draft and not form.is_multiple_submittable:
        answer_sheet_draft = UserFormAnswerSheet.objects.filter(
            user=user,
            form=form,
            is_draft=True
        ).first()
        if answer_sheet_draft:
            answer_sheet = answer_sheet_draft

    if form.deadline:
        if get_today(with_time=True) > form.deadline:
            error = f"Deadline '{form.deadline.date()}' for form {form.name} has expired."
            raise ValidationError({
                "error": error
            })
    question_answer = save_files_from_answers(viewset, question_answer)
    answer_sheet_creation = dict(
        user=user,
        form=form,
        is_draft=True
    )
    if not is_draft:
        validate_answers(question_answer)
        answer_sheet_creation.update({"is_draft": False})

    # if answer_sheet already exists(PUT request), dont create again
    if not answer_sheet:
        answer_sheet = UserFormAnswerSheet.objects.create(**answer_sheet_creation)

    context = viewset.get_serializer_context()
    context.update({
        "organization": viewset.organization,
        "form": form
    })

    save_answer_to_db(context, answer_sheet, question_answer)

    if is_draft:
        result = dict(answer_sheet_id=answer_sheet.id)
        return result


    AnswerSheetStatus.objects.create(
        answer_sheet=answer_sheet,
        approver=user,
        approval_level=None,
        action=REQUESTED,
        remarks=f"Submitted form {form.name}"
    )
    notify_organization(
        text=(
            f"Form '{answer_sheet.form.name}' has been submitted."
        ),
        action=answer_sheet,
        organization=viewset.organization,
        actor=user,
        url=f'/admin/{viewset.organization.slug}/form/response',
        permissions=[
            FORM_PERMISSION,
            FORM_READ_ONLY_PERMISSION,
            FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS
        ]
    )
    if not answer_sheet.form.form_approval_setting.exists():
        # if approval setting is not present
        AnswerSheetStatus.objects.create(
            answer_sheet=answer_sheet,
            approver=get_system_admin(),
            approval_level=None,
            action=APPROVED,
            remarks=f"Approved by system (no approval settings present)."
        )
        answer_sheet.is_approved = True
        answer_sheet.is_draft = False
        answer_sheet.save()
        send_notification_if_all_users_submitted(answer_sheet)
    else:
        approval_levels = answer_sheet.form.form_approval_setting.all()
        answer_sheet_approvals = []
        numbers_map = {
            FIRST: 1,
            SECOND: 2,
            THIRD: 3,
        }
        supervisors = UserSupervisor.objects.filter(
            user=user,
        )
        # create denormalized sheet approvalfor all approval objects
        # during the time of form creation
        for approval in approval_levels:
            sheet_approval = FormAnswerSheetApproval.objects.create(
                approve_by=approval.approve_by,
                supervisor_level=approval.supervisor_level,
                answer_sheet=answer_sheet,
                approval_level=approval.approval_level
            )
            if approval.approve_by == EMPLOYEE:
                sheet_approval.employees.set([approval.employee])
            else:
                if approval.supervisor_level == ALL:
                    if supervisors.exists():
                        sheet_approval.employees.set(supervisors.values('supervisor')[:])
                else:
                    supervisor_level = numbers_map[approval.supervisor_level]
                    if supervisors.filter(authority_order=supervisor_level).exists():
                        supervisor_obj = supervisors.filter(authority_order=supervisor_level)
                        if supervisor_obj:
                            sheet_approval.employees.set([supervisor_obj.first().supervisor])

        next_approver = get_next_approvers(answer_sheet)
        if not next_approver:
            AnswerSheetStatus.objects.create(
                answer_sheet=answer_sheet,
                approver=get_system_admin(),
                approval_level=None,
                action=APPROVED,
                remarks=f"Approved by system(no approvers are applicable)."
            )
            answer_sheet.is_approved = True
            answer_sheet.is_draft = False
            answer_sheet.save()
        else:
            next_approval_level = get_next_approval_level(answer_sheet)
            if next_approval_level:
                answer_sheet.next_approval_level = next_approval_level.approval_level
                answer_sheet.save()
        add_notification(
            text=(
                f"Form '{answer_sheet.form.name}' has been submitted."
            ),
            action=answer_sheet,
            recipient=next_approver,
            actor=user,
            url='/user/form-request'
        )
        answer_sheet.is_draft = False
        answer_sheet.save()
    result = dict(answer_sheet_id=answer_sheet.id)
    return result


def is_form_filled_yet(form):
    user_filled_answersheet_exists = (
        UserFormAnswerSheet.objects.filter(
            form=form,
            is_draft=False
        ).exists()
    )
    anonymous_filled_answersheet_exists = (
        AnonymousFormAnswerSheet.objects.filter(
            form=form,
        ).exists()
    )
    return any([user_filled_answersheet_exists,
                anonymous_filled_answersheet_exists])


def get_form_queryset_for_user(qs=None, filters=None, user=None):
    if not qs:
        qs = Form.objects.filter(is_archived=False)

    if filters:
        qs = qs.filter(**filters)

    if user:
        qs = qs.filter(
            form_assignments__user=user,
        )

    qs = qs.filter(
        # only display forms which have not exceeded deadlines
        Q(
            deadline__isnull=True
        ) |
        Q(
            deadline__gte=get_today(with_time=True)
        )
    ).annotate(
        latest_answer_sheet=Subquery(
            UserFormAnswerSheet.objects.filter(
                form=OuterRef('id'),
                user=user,
            ).order_by('created_at').values('id')[:1]
        )
    ).annotate(
        was_latest_sheet_denied=Exists(
            UserFormAnswerSheet.objects.filter(
                id__in=OuterRef('latest_answer_sheet'),
            ).filter(
                is_draft=False,
                status__action=DENIED
            )
        )
    ).annotate(
        answer_sheet_in_progress_exists=Exists(
            UserFormAnswerSheet.objects.filter(
                form=OuterRef('id'),
                user=user,
                is_approved=False,
                is_draft=False
            ).filter(
                ~Q(status__action=DENIED)
            )
        )
    ).annotate(
        answer_sheet_draft_exists=Exists(
            UserFormAnswerSheet.objects.filter(
                form=OuterRef('id'),
                user=user,
                is_draft=True
            )
        )
    ).annotate(
        answer_sheet_exists=Exists(
            UserFormAnswerSheet.objects.filter(
                form=OuterRef('id'),
                user=user,
            )
        )
    ).annotate(
        approved_answer_sheet_exists=Exists(
            UserFormAnswerSheet.objects.filter(
                form=OuterRef('id'),
                user=user,
                is_approved=True
            )
        )
    )


    # Every form has an `is_multiple_submittable` property which allows a
    # form to be submitted multiple times.
    # If is_multiple_submittable is set to `False` and the user submitted a form
    # but his/her form got rejected, he/she should be able to submit the form again
    # irrespective of the `is_multiple_submittable` flag until his/her form gets
    # approved. If form approval is pending or if there is atleast
    # one approval, don't display the form again.

    qs = qs.filter(
        Q(
            Q(
                # Q(answer_sheet_draft_exists=False) |
                Q(
                    was_latest_sheet_denied=True,
                    approved_answer_sheet_exists=False,
                    answer_sheet_draft_exists=False,
                    answer_sheet_in_progress_exists=False
                ) |
                ~Q(answer_sheet_exists=True)
            ) &
            Q(is_multiple_submittable=False)
        ) |
        Q(
            is_multiple_submittable=True
        )
    )
    return qs
