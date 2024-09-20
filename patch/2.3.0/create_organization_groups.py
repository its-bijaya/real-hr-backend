"""
Create Organization vs Group scenario.
"""
from django.contrib.auth.models import Group

from irhrs.organization.models import Organization

from irhrs.permission.signals import seed_organization_vs_group
seed_organization_vs_group(
    group_list=Group.objects.all(),
    org_list=[None, *Organization.objects.all()]
)
