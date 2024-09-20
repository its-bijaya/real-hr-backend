import json

from django.contrib.auth import get_user_model

from irhrs.organization.models import Organization
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


def add_organization_to_user(employee_data):
    users = User.objects.filter(detail__organization__isnull=True).order_by('id')
    organizations = Organization.objects.all()
    organization_data = {org.slug: org for org in organizations}

    _data_changed_users = []
    _data_unchanged_users = []

    def change_organization(_user):
        org_slug = employee_data.get(_user.full_name.title(), None)
        if org_slug and org_slug in organization_data:
            _user.detail.organization = organization_data.get(org_slug)
            _user.detail.save()
            _data_changed_users.append(_user)
        else:
            _data_unchanged_users.append(_user)

    for user in users:
        if not user.user_experiences.exists():
            change_organization(user)
        else:
            experience = user.user_experiences.order_by('-start_date').first()
            org = experience.organization
            if org:
                user.detail.organization = org
                user.detail.save()
                _data_changed_users.append(user)
            else:
                change_organization(user)

    print(
        json.dumps(
            {
                'count': len(_data_changed_users) + len(_data_unchanged_users),
                'total_changed': len(_data_changed_users),
                'total_unchanged': len(_data_unchanged_users),
                'data_changed_users': UserThinSerializer(
                    _data_changed_users,
                    many=True,
                    fields=['id', 'full_name', 'organization']
                ).data,
                'data_unchanged_users': UserThinSerializer(
                    _data_unchanged_users,
                    many=True,
                    fields=['id', 'full_name']
                ).data,
            },
            indent=4,
            default=str
        )
    )
