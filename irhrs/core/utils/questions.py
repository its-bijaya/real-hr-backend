
from jsonschema import validate as validate_schema
from jsonschema.exceptions import ValidationError as SchemaValidationError
from rest_framework.exceptions import ValidationError


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


char_types = (
    RATING_SCALE, LONG, SHORT, DATE, TIME, DURATION,
    DATE_TIME, DATE_WITHOUT_YEAR, DATE_TIME_WITHOUT_YEAR
)

grid_types = (
    MULTIPLE_CHOICE_GRID, CHECKBOX_GRID
)


def validate_mandatory_mcq(choices, is_mandatory=False):
    if is_mandatory:
        for choice in choices:
            if choice.get("is_correct") is True:
                return
        raise ValidationError({
            "error": "One or more mandatory question don't have an answer."
        })


def validate_char_types(answer, is_mandatory=False):
    if is_mandatory:
        if not any(answer):
            raise ValidationError({
                "error": "One or more mandatory question don't have an answer."
            })


def validate_file_upload(answer, is_mandatory=False):
    if is_mandatory:
        if not answer:
            raise ValidationError({
                "error": "File upload question is mandatory."
            })
        file_name = answer[0].get('file_name')
        if not file_name:
            raise ValidationError({
                "error": "File field cannot be empty."
            })


def validate_grid_type(answer, form_question, is_mandatory=False):
    question_type = form_question.question.answer_choices
    all_rows_mandatory = form_question.question.extra_data.get(
        "all_rows_mandatory", False
    )

    answer_schema = {
        "type": "object",
        "properties": {
            "answers": {
                "type": "object",
                "patternProperties": {
                    "^.+$": {
                        "type": "array"
                    },
                }
            }
        }
    }
    try:
        validate_schema(answer, answer_schema)
    except SchemaValidationError as schema_error:
        raise ValidationError({"error": schema_error.message})

    if all_rows_mandatory:
        choices = form_question.question.extra_data.get(
            "rows", list()
        )
        unanswered_choices = [
            (choice not in answer.keys() or not answer.get(choice))
            for choice in choices
        ]
        if any(unanswered_choices):
            raise ValidationError({"error": "All rows are mandatory"})

    if question_type == MULTIPLE_CHOICE_GRID:
        # only allow single answer(radio button) to be selected
        # for multichoice grid
        if any([len(val) > 1 for val in answer.values()]):
            raise ValidationError({
                "error": ("Multiple choice grid does not allow "
                          "choosing more than one subchoice.")
            })


def validate_mandatory_questions(question_answer, is_mandatory=False, **kwargs):
    answer_type = question_answer.get('answer_choices')
    answer = question_answer.get('answers', [])
    if answer_type in [RADIO, CHECKBOX]:
        validate_mandatory_mcq(answer, is_mandatory)
    elif answer_type in char_types:
        validate_char_types(answer, is_mandatory)
    elif answer_type in grid_types:
        form_question = kwargs.get('form_question')
        validate_grid_type(
            answer,
            form_question,
            is_mandatory,
        )
    elif answer_type == FILE_UPLOAD:
        validate_file_upload(answer, is_mandatory=is_mandatory)

    if is_mandatory and not answer:
        raise ValidationError({
            "error": "One or more mandatory question don't have an answer."
        })
