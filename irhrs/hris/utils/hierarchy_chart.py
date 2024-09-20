from django.conf import settings
from django.contrib.auth import get_user_model

from irhrs.core.utils import get_system_admin
from irhrs.core.utils.subordinates import (
    find_immediate_subordinates,
    find_supervisor, find_org_specific_subordinates, find_org_specific_supervisor)

User = get_user_model()


def get_subordinates(supervisors):
    if getattr(settings, 'ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY', False):
        return find_org_specific_subordinates(supervisors)
    return find_immediate_subordinates(supervisors)


def get_supervisor(user):
    if getattr(settings, 'ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY', False):
        return find_org_specific_supervisor(user)
    return find_supervisor(user)


def build_hierarchy_chart(supervisors, user):
    """
    Generates hierarchy chart for user

    :param supervisors: id of supervisors

    :param user: id of requested user
    :return: dict
    """
    hc_list = []
    sub_ordinates = get_subordinates(supervisors)
    if sub_ordinates:
        system_admin = get_system_admin().id
        sub_ordinates = User.objects.filter(
            id__in=sub_ordinates
        ).exclude(id=user).order_by("first_name", "middle_name", "last_name").current()
        for sub_ordinate in sub_ordinates:
            r = get_relationship(sub_ordinate.id,
                                 system_admin=system_admin)
            hc_list.append({'user': sub_ordinate,
                            'relationship': r})
    return hc_list


def get_relationship(user, system_admin) -> str:
    """
    generates relationship for the user
    :param user: accepts int() which is id for user
    :param system_admin: accepts int() which is id for system admin
    :return: returns three digit string combination of 0 and 1,example: 001
    where, 1st digit deals with parent, 2nd digit deals with  sibling and
    3rd digit deals with children.
    """
    if not user == system_admin:
        supervisor = get_supervisor(user)
        _map = {True: '1', False: '0'}
        return f'{_map[bool(supervisor) and not supervisor == system_admin] }' \
               f'{_map[len(get_subordinates(supervisor)) > 1]}' \
               f'{_map[len(get_subordinates(user)) > 0]}'

    return '001'
