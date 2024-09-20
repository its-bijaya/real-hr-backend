from django.db.models import Sum, Value, Count, Q
from django.db.models.functions import Coalesce

from irhrs.assessment.models.assessment import AssessmentQuestions
from irhrs.questionnaire.models.helpers import RADIO, CHECKBOX
from irhrs.websocket.helpers import send_for_group as websocket_group


def send_assessment_notification(user, msg):
    websocket_group(
        str(user.id),
        msg,
        msg_type='assessment'
    )


def calculate_total_weight(assessment_set, with_count=False):
    """
    returns count as first and total_weight as second for with_count True
    else returns total_weight

    :param assessment_set: AssessmentSet
    :param with_count: Bool
    :return: dict_list or int
    """
    # calculating total weight of questions for an assessment set
    questions = AssessmentQuestions.objects.filter(
        assessment_section__assessment_set=assessment_set
    ).aggregate(
        count=Count('question__id'),
        total_weight=Coalesce(
            Sum(
                'question__weightage',
                filter=Q(question__answer_choices__in=[CHECKBOX, RADIO])
            ),
            Value(0)
        )
    )
    if with_count:
        return questions.values()
    return questions.get('total_weight')


def add_weightage_for_assessment_set(assessment_set):
    count, total_weight = calculate_total_weight(assessment_set, with_count=True)
    marginal_weight = (assessment_set.marginal_percentage * total_weight) / 100

    assessment_set.total_weightage = total_weight
    assessment_set.total_questions = count
    assessment_set.marginal_weightage = round(marginal_weight)
    assessment_set.save()
