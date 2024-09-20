"""@irhrs_docs"""
import logging
from collections import defaultdict
from functools import lru_cache

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import FilteredRelation, Q, F

from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.graph import traverse
from irhrs.users.models import UserSupervisor

logger = logging.getLogger(__name__)

User = get_user_model()


def find_all_subordinates(supervisor_id):
    """find all subordinates of a user"""
    user_supervisors = cache.get('user_subordinates', ...)
    if user_supervisors is ...:
        set_subordinate_cache()
        user_supervisors = cache.get('user_subordinates')
    return user_supervisors.get(supervisor_id, set())


def find_subordinates_excluding_self(supervisor_id):
    sub_ordinates = find_all_subordinates(supervisor_id)
    sub_ordinates.remove(supervisor_id) if supervisor_id in sub_ordinates else None
    return sub_ordinates


def set_subordinate_cache():
    relations = UserSupervisor.objects.all().only('supervisor_id', 'user_id')

    tmp = defaultdict(set)
    user_subordinates = dict()
    ignored = defaultdict(set)

    # fill the tmp with immediate subordinates
    for relation in relations.iterator():
        tmp[relation.supervisor_id].add(relation.user_id)

    for supervisor_id in tmp:
        traverse(supervisor_id, tmp, visited=user_subordinates, ignored=ignored)

    logger.info("Setting supervisor cache")
    cache.set('user_subordinates', user_subordinates)
    logger.info("Supervisor Cache set")
    del tmp
    del ignored


def set_immediate_subordinates_and_supervisor_cache(system_admin=None):
    relations = UserSupervisor.objects.filter(
        authority_order=1,
        user__user_experiences__is_current=True,
        user__is_active=True,
        user__is_blocked=False
    ).only('supervisor_id', 'user_id')

    user_immediate_subordinates = defaultdict(set)
    user_supervisor = {}
    sys_admin = system_admin or get_system_admin()  # real hr bot
    for relation in relations.iterator():
        if relation.supervisor_id != sys_admin.id:
            user_immediate_subordinates[relation.supervisor_id].add(relation.user_id)
            user_supervisor[relation.user_id] = relation.supervisor_id

    cache.set('user_immediate_subordinates', user_immediate_subordinates)
    cache.set('user_supervisor', user_supervisor)


def find_immediate_subordinates(supervisor):
    """ find immediate subordinates for user"""
    user_immediate_subordinates = cache.get('user_immediate_subordinates', ...)
    if user_immediate_subordinates is ...:
        set_immediate_subordinates_and_supervisor_cache()
        user_immediate_subordinates = cache.get('user_immediate_subordinates')

    return user_immediate_subordinates.get(supervisor, [])


def find_supervisor(user):
    """ find supervisor for user"""
    user_supervisor = cache.get('user_supervisor', ...)
    if user_supervisor is ...:
        set_immediate_subordinates_and_supervisor_cache()
        user_supervisor = cache.get('user_supervisor')
    return user_supervisor.get(user, None)


def set_subordinate_according_to_organization(system_admin=None):
    relations = UserSupervisor.objects.filter(
        authority_order=1,
        user__user_experiences__is_current=True,
        user__is_active=True,
        user__is_blocked=False
    ).only('supervisor_id', 'user_id')

    user_immediate_subordinates = defaultdict(set)
    user_supervisor = {}
    sys_admin = system_admin or get_system_admin()  # real hr bot
    for relation in relations.iterator():
        in_same_org = relation.supervisor.detail.organization == relation.user.detail.organization
        if relation.supervisor_id != sys_admin.id and in_same_org:
            user_immediate_subordinates[relation.supervisor_id].add(relation.user_id)
            user_supervisor[relation.user_id] = relation.supervisor_id

    cache.set('organization_specific_subordinates', user_immediate_subordinates)
    cache.set('organization_specific_supervisor', user_supervisor)


def find_org_specific_subordinates(user):
    """ find supervisor for user"""
    user_supervisor = cache.get('organization_specific_subordinates', ...)
    if user_supervisor is ...:
        set_subordinate_according_to_organization()
        user_supervisor = cache.get('organization_specific_subordinates')
    return user_supervisor.get(user, [])


def find_org_specific_supervisor(user):
    """ find supervisor for user"""
    user_supervisor = cache.get('organization_specific_supervisor', ...)
    if user_supervisor is ...:
        set_subordinate_according_to_organization()
        user_supervisor = cache.get('organization_specific_supervisor')
    return user_supervisor.get(user, None)


def set_supervisor_permissions(paginated_queryset: list, supervisor: int, user_field: str) -> list:
    """
    sets permissions attribute to paginated queryset
    """
    user_id_attr = f'{user_field}_id' if user_field else 'id'

    user_ids = {
        nested_getattr(item, user_id_attr)
        for item in paginated_queryset
    }

    users = User.objects.filter(id__in=user_ids)

    permissions = list(users.annotate(
        _supervisors=FilteredRelation(
            'supervisors',
            condition=Q(supervisors__supervisor=supervisor)
        )
    ).annotate(
        _can_approve=F('_supervisors__approve'),
        _can_deny=F('_supervisors__deny'),
        _can_forward=F('_supervisors__forward')
    ).values('id', '_can_approve', '_can_deny', '_can_forward'))

    permissions_map = {
        u['id']: {
            'approve': u['_can_approve'],
            'deny': u['_can_deny'],
            'forward': u['_can_forward']
        }
        for u in permissions
    }
    for item in paginated_queryset:
        setattr(
            item,
            'permissions',
            permissions_map[nested_getattr(item, user_id_attr)]
        )

    return paginated_queryset


# TODO: implement cache with expiry @lru_cache
def authority_exists(user, supervisor, action):
    return UserSupervisor.objects.filter(
        user=user,
        supervisor=supervisor,
        **{action: True}
    ).exists()


def get_next_level_supervisor(user, supervisor):
    """Return next level supervisor given pair of current user supervisor"""
    current_level = UserSupervisor.objects.filter(
        user=user,
        supervisor=supervisor
    ).first()
    if not current_level:
        return None

    next_authority = UserSupervisor.objects.filter(
        user=user,
        authority_order=current_level.authority_order + 1
    ).first()

    return next_authority.supervisor if next_authority else None
