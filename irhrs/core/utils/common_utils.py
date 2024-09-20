"""@irhrs_docs"""

from functools import reduce
from itertools import zip_longest

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.fields import DurationField

from irhrs.core.constants.user import OTHER

now = timezone.now


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def nested_getattr(instance: object, attributes: str, separator='.', default=None, call=True):
    """
    Returns nested getattr and returns default if not found
    :param instance: object to get nested attributes from
    :param attributes: separator separated attributes
    :param separator: separator between nested attributes.
    :param default: default value to return if attribute was not found
    :param call: flag that determines whether to call or not if callable
    :return:
    """
    nested_attrs = attributes.split(separator)
    nested_attrs.insert(0, instance)
    try:
        attr = reduce(
            lambda instance_, attribute_: getattr(instance_, attribute_),
            nested_attrs
        )
        if call and callable(attr):
            return attr()
        return attr
    except AttributeError:
        return default


def get_system_admin():
    """
    Creates a System Admin for notifications.
    """
    _USER = get_user_model()
    email = getattr(settings, 'SYSTEM_BOT_EMAIL', 'irealhrbot@irealhrsoft.com')
    system_bot = cache.get('SYSTEM_BOT')
    if system_bot:
        return system_bot
    try:
        user = _USER.objects.get(
            email=email
        )

    except _USER.DoesNotExist:

        bot_name = getattr(settings, 'SYSTEM_BOT_NAME', 'RealHR Soft')
        __names = bot_name.split()
        if len(__names) >= 2:
            first_name = __names[0]
            last_name = __names[1]
        else:
            first_name = 'RealHR'
            last_name = "Bot"

        profile_pic = None
        profile_pic_name = getattr(settings, 'SYSTEM_BOT_PROFILE_IMAGE', None)
        if profile_pic_name:
            profile_pic = staticfiles_storage.open(profile_pic_name)

        user = _USER.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password='None',
            profile_picture=profile_pic
        )

        if profile_pic:
            profile_pic.close()

        from irhrs.users.models import UserDetail
        from irhrs.core.constants.user import OTHER
        ud = UserDetail.objects.create(
            gender=OTHER,
            date_of_birth=timezone.now().date(),
            joined_date=timezone.now().date(),
            user=user
        )
        ud.save()
    cache.set('SYSTEM_BOT', user)
    return user


def get_payroll_dummy_user(pre_employment):
    """
    Because the Employee Salary Calculator in Payroll requires a User object and its dependencies,
    We reserve a virtual user for this and process the pre-employment user through this virtual user.
    :param pre_employment: To be on-boarded user into the system.
    :return: Modifies the reserved user according to the information provided in Pre Employment.
    """
    _USER = get_user_model()
    try:
        # Test if the user exists at first.
        payroll_user = _USER.objects.get(
            email='payroll.dummyuser@realhrsoft.com'
        )
    except _USER.DoesNotExist:
        from irhrs.users.models import UserDetail
        # We create payroll_user here.
        payroll_user = _USER.objects.create_user(
            email='payroll.dummyuser@realhrsoft.com',
            password="payroll.dummyuser@realhrsoft.com",
            first_name='Payroll',
            middle_name='Dummy',
            last_name='User',
        )
        UserDetail.objects.create(
            user=payroll_user,
            date_of_birth=timezone.now(),
            gender=OTHER
        )
    # We begin the cleanup by removing experiences.
    from irhrs.organization.models import FiscalYear
    this_fiscal = FiscalYear.objects.current(
        pre_employment.organization
    )
    # payroll_user.detail.marital_status = pre_employment.
    payroll_user.detail.gender = pre_employment.gender
    payroll_user.user_experiences.all().delete()
    payroll_user.detail.joined_date = this_fiscal.applicable_from
    payroll_user.user_experiences.create(
        start_date=this_fiscal.applicable_from,
        current_step=pre_employment.step,
        is_current=True,
        job_title=pre_employment.job_title,
        organization=pre_employment.organization,
        division=pre_employment.division,
        employee_level=pre_employment.employment_level,
        employment_status=pre_employment.employment_status,
        branch=pre_employment.branch
    )
    return payroll_user


def echo(request, status, *args, **kwargs):
    status_code = 200
    if status.isdigit():
        x = int(status)
        if 100 <= x < 600:
            status_code = x
    return HttpResponse(
        content=f'You requested for {status_code} page',
        status=status_code
    )


def get_patch_attr(
        attribute, validated_data, serializer
):
    """
    Use this method for obtaining attribute instead of
    `validated_data.get(attr)`
    :param attribute: name of the attribute e.g. `pk`
    :param validated_data: dict of validated_data
    :param serializer: serializer instance i.e. `self`
    :return: attribute from validated_data or self.instance if the method is
    `PATCH`. Does not care about instance if `PUT`.
    """
    instance = serializer.instance
    attr = validated_data.get(attribute)
    if not instance or attribute in validated_data:
        return attr
    return attr if attr else getattr(instance, attribute, None)


def this_month_range():
    start = now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = start + relativedelta(months=1) - timezone.timedelta(days=1)
    return start, end


def prettify_headers(headers):
    return [' '.join(head.split('_')).title() for head in headers]


class HumanizedDurationField(DurationField):
    """
    Structures the DurationField as HH:MM:SS instead of default "ss" (seconds).
    """
    def to_representation(self, value):
        from irhrs.attendance.utils.attendance import humanize_interval
        return humanize_interval(value, absolute=False)


def nested_get(dictionary, attribute_list, separator='.'):
    """
    Returns the nested value by parsing keys in iteration.
    Example:
    ```
    dictionary = {
        'a': {
            'b': {
                'c': {
                    'd': 'Desired Value'
                    }
                }
            }
        }
    }
    ```
    If we wanted to get the value of 'd', we could use:
    `nested_get(dictionary, 'a.b.c.d', separator='.')`
    :param dictionary: The nested dictionary
    :param attribute_list: The path to the desired key
    :param separator: How the attributes can be differentiated.
    :return: nested value or None
    """
    curr = dictionary
    attributes = attribute_list.split(separator)
    for attribute in attributes:
        if not isinstance(curr, dict):
            return curr
        res = curr.get(attribute)
        curr = res
    return curr


def get_prefetched_attribute(instance, attribute, default=None):
    """
    Return prefetched attribute from instance
    :param instance: instance
    :param attribute: attribute to prefetch
    :param default: default value if attribute is not prefetched
    :return: prefetched attribute or default
    """
    _prefetched_objects_cache = getattr(instance, '_prefetched_objects_cache', {})

    value = _prefetched_objects_cache.get(attribute, ...)

    if value is ...:
        if callable(default):
            value = default()
        else:
            value = default

    return value


def get_users_list_from_permissions(permission_list, organization, exclude_users=None):
    """
    Return list of users who have atleast 1 permission from `permission_list`
    in `organization`.

    exclude_users = list of user ids to exclude
    """
    from irhrs.permission.models.hrs_permisssion import OrganizationGroup, HRSPermission
    from irhrs.core.utils.organization import get_switchable_users
    User = get_user_model()
    organization_groups_with_perm = OrganizationGroup.objects.filter(
        organization=organization,
        permissions__code__in=[x.get('code') for x in permission_list]
    )
    groups_with_perms = set(
        [
            org_group.group for org_group
            in organization_groups_with_perm
         ]
    )
    users_with_perm = User.objects.filter(
        groups__in=groups_with_perms
    ).current()

    if exclude_users:
        users_with_perm = users_with_perm.exclude(id__in=exclude_users)

    # users must have switchable permission in organization
    switchable_users = get_switchable_users(organization).values_list('id')
    final_users = users_with_perm.filter(
        id__in=switchable_users
    )
    return final_users if final_users else []
