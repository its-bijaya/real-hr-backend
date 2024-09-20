"""@irhrs_docs"""
from django.contrib.auth import get_user_model

USER = get_user_model()


def get_switchable_users(organization):
    """Return switchable users for given organization"""
    return USER.objects.filter(organization__can_switch=True, organization__organization=organization)
