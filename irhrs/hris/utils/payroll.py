"""@irhrs_docs"""
import typing
from datetime import date

from django.db.models import Count

from irhrs.hris.models import EmploymentReview
from django.contrib.auth import get_user_model

USER = get_user_model()

def get_employment_review_status_summary(
        organization_slug: str, start: date,
        end: date, user_filter: dict,
        exclude_filter: typing.Union[dict, None] = None
):
    """
    Employment review summary

    -------------------------
    :param organization_slug: organization slug of user
    :param start: start of range for timesheet_for
    :param end: end of range for timesheet_for
    :param user_filter: dictionary of filters to be applied on USER model
    :param exclude_filter: dictionary of filters to be excluded on USER model
    :return: counts of employment review category

    .. code-block:: python

        [{'change_type__title': 'Change Type Title', 'count': 1}, ..]

    """
    fil = dict(detail__organization__slug=organization_slug)
    fil.update(user_filter)

    review_filter = {f"employee__{key}": value for key, value in fil.items()}
    review_filter.update({
        "detail__new_experience__start_date__range": [start, end]
    })
    qs = EmploymentReview.objects.filter(**review_filter)
    if exclude_filter:
        qs = qs.exclude(**exclude_filter)

    from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
    user_id = qs.values_list(
        'employee', flat=True)
    user_list = UserThinSerializer(
        USER.objects.filter(id__in=user_id),
        fields=('id', 'full_name', 'profile_picture', 'job_title', 'organization', 'is_current', 'is_online'),
        many=True).data

    stat = qs.order_by('change_type__title').values(
        'change_type__title',
    ).annotate(count=Count('id', distinct=True))

    return {
        "users": user_list,
        "stat": stat
    }
