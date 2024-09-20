from django import template

from irhrs.permission.constants.groups import ADMIN, HR_ADMIN, ORG_HEAD, \
    DIVISION_HEAD, BRANCH_MANAGER, NORMAL_USER

initial_groups = [
    ADMIN,
    HR_ADMIN,
    ORG_HEAD,
    DIVISION_HEAD,
    BRANCH_MANAGER,
    NORMAL_USER
]

register = template.Library()


@register.simple_tag()
def is_editable(name):
    return name != ADMIN


@register.simple_tag()
def is_deletable(name):
    return name not in initial_groups
