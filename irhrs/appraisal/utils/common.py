from functools import reduce
from rest_framework.exceptions import ValidationError

from irhrs.appraisal.models.performance_appraisal import (
    SubPerformanceAppraisalSlotWeight,
    SubPerformanceAppraisalSlot
)
from irhrs.users.models.user import User


def _validate_total_weight(attrs):
    total_weightage = reduce(
        lambda x, y: x + y,
        map(
            lambda x: x.get('weightage'),
            attrs
        )
    )
    if total_weightage != 100:
        raise ValidationError({
            'weightage': ['Total weightage must be 100.']
        })


def _validate_overlapped_data(data, from_key, to_key, message):
    for index, datum in enumerate(data):
        if index > 0:
            if datum[from_key] <= data[index - 1].get(to_key):
                raise ValidationError({
                    'non_field_errors': [message]
                })


def _validate_repeated_data(data, key, message):
    """
    This util is used to test whether there is repeated data or not
    :param data: list of dict
    :param key: string that is used to extract data from data dict
    :param message: string that carries some information about error
    :return
    """
    extracted_data = [datum.get(key) for datum in data]
    if extracted_data and len(extracted_data) != len(set(extracted_data)):
        raise ValidationError({key: [message]})


def get_user_appraisal_score_for_slot(user: User, slot_id: str) -> dict:
    """List all the score/percentage of all appraisal_type for given slot

    :param user: User instance whose percentage is to be calculated
    :param slot_id: Slot id whose percentage is to be calculated
    :returns : dictionary of percentage of  all the appraisal_type and total percentage of slot

    """
    sub_performance_appraisal_slot_weight = SubPerformanceAppraisalSlotWeight.objects.filter(
        appraiser=user,
        sub_performance_appraisal_slot=slot_id
    ).values_list('percentage', flat=True).first()

    if not sub_performance_appraisal_slot_weight:
        sub_performance_appraisal_slot_weight = "N/A"

    return {
        'self_appraisal': user.self_appraisal,
        'supervisor_appraisal': user.supervisor_appraisal,
        'subordinate_appraisal': user.subordinate_appraisal,
        'peer_to_peer_feedback': user.peer_to_peer_feedback,
        'total_average': sub_performance_appraisal_slot_weight
    }


def get_user_appraisal_score_for_year(user, year_id):
    slot_scores = list(user.sub_performance_appraisal_slot_weights.all())
    slots = SubPerformanceAppraisalSlot.objects.filter(
        performance_appraisal_year__id=year_id
    ).values_list('title', flat=True)
    slot_modes_weightage = dict()
    final_average_score = 0
    for item in slot_scores:
        title = item.sub_performance_appraisal_slot.title
        slot_modes_weightage[title] = item.percentage
        final_average_score += (
            slot_modes_weightage[title] / 100 * item.sub_performance_appraisal_slot.weightage
        )

    data = {
        slot: slot_modes_weightage.get(slot, 0) for slot in slots
    }
    data.update({
        'total_average_score': float(format(final_average_score, '.2f'))
    })
    return data
