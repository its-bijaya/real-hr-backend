from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.recruitment.constants import ABOVE, BELOW, EQUALS, ATTACHMENT_MAX_UPLOAD_SIZE, PROGRESS, \
    PENDING
from irhrs.recruitment.models import Salary, Location, Job


def get_or_create_salary(validated_data):
    """
    Get or create salary with given details
    :param validated_data:
    :return:
    """
    salary = Salary.objects.filter(**validated_data).first()
    if salary:
        return salary
    return Salary.objects.create(**validated_data)


def get_or_create_location(validated_data):
    """
    Get or create location with given details
    :param validated_data:
    :return:
    """
    location = Location.objects.filter(**validated_data).first()
    if location:
        return location
    return Location.objects.create(**validated_data)


def filter_salary_range(queryset, value, unit, salary_field=''):
    """
    Filter salary range
    :param queryset: Queryset to filter
    :type queryset: Queryset
    :param value: slice
    :type value: slice
    :param unit: salary unit
    :type unit: str
    :param salary_field: field or path to reach salary instance
        concatenated with __ as in Queryset filter
    :type salary_field: str
    :return: filtered queryset
    """
    if value:
        # filter for range type of salary
        if salary_field:
            salary_field = f"{salary_field}__"

        both_max_min_fil_dict = {
            f'{salary_field}minimum__isnull': False,
            f'{salary_field}maximum__isnull': False,
        }

        # filter for salary having above operator
        above_filter = {
            f'{salary_field}minimum__isnull': False,
            f'{salary_field}operator': ABOVE,
        }

        # filter for salary having below operator
        below_filter = {
            f'{salary_field}minimum__isnull': False,
            f'{salary_field}operator': BELOW,
        }

        # filter for salary having equals operator
        equals_filter = {
            f'{salary_field}minimum__isnull': False,
            f'{salary_field}operator': EQUALS,
        }

        # salary unit filter
        unit_q = Q(**{f'{salary_field}unit': unit})

        if value.start is not None and value.stop is not None:
            # if both start and end are passed
            both_max_min_fil_dict.update({
                f'{salary_field}maximum__gte': value.start,
                f'{salary_field}minimum__lte': value.stop,
            })
            above_filter.update({
                f'{salary_field}minimum__lte': value.stop
            })
            below_filter.update({
                f'{salary_field}minimum__gte': value.start
            })
            equals_filter.update({
                f'{salary_field}minimum__range':
                    (value.start, value.stop)
            })

        elif value.start is not None:
            both_max_min_fil_dict.update({
                f'{salary_field}maximum__gte': value.start,
            })
            below_filter.update({
                f'{salary_field}minimum__gte': value.start
            })
            equals_filter.update({
                f'{salary_field}minimum__gte': value.start
            })

        elif value.stop is not None:
            both_max_min_fil_dict.update({
                f'{salary_field}minimum__lte': value.stop
            })
            above_filter.update({
                f'{salary_field}minimum__lte': value.stop
            })
            equals_filter.update({
                f'{salary_field}minimum__lte': value.stop
            })

        if value.start is not None or value.stop is not None:
            fil = unit_q & Q(
                Q(**both_max_min_fil_dict) | Q(**above_filter)
                | Q(**below_filter) | Q(**equals_filter)
            )
            queryset = queryset.filter(fil)
    return queryset


def validate_attachment(attachment):
    if attachment.size > ATTACHMENT_MAX_UPLOAD_SIZE:
        raise serializers.ValidationError(
            _(
                'File Size Should not Exceed '
                f'{ATTACHMENT_MAX_UPLOAD_SIZE / (1024 * 1024)} MB'
              )
        )
    return attachment


def get_no_objection_info(stage, job=None, apply_id=None):
    """
    :param stage: No Objection stage
    :param job: Job Object
    :param apply_id: Job Apply id
    :return:
    """
    from irhrs.recruitment.models import NoObjection

    fil = dict()
    if job:
        fil['job'] = job

    if apply_id:
        fil['job_apply'] = apply_id

    no_objection = NoObjection.objects.filter(
        stage=stage,
    ).filter(**fil).order_by('-created_at').first()

    return {
        'id': no_objection.id if no_objection else None,
        'status': no_objection.status if no_objection else 'Not Initialized',
        'remarks': no_objection.remarks if no_objection else ''
    }


def raise_exception_if_job_apply_is_not_in_completed_step(klass, job: Job):
    if klass.objects.filter(
        job_apply__job=job, status__in=[PENDING, PROGRESS]
    ).exists():
        raise ValidationError({
            "non_field_errors": "All the candidates are not in completed state."
        })
