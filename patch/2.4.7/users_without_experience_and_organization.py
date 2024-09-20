import json

from django.contrib.auth import get_user_model

from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


def users_without_experience_and_organization():
    users = User.objects.filter(detail__organization__isnull=True).order_by('id')
    users_with_experience = users_without_exp = []

    for user in users:
        if not user.user_experiences.exists():
            users_without_exp.append(user)
        else:
            users_with_experience.append(user)

    print(
        json.dumps(
            {
                'count': len(users_without_exp),
                'users': UserThinSerializer(
                    users_without_exp,
                    many=True,
                    fields=['id', 'full_name']
                ).data,
                'users_with_exp': UserThinSerializer(
                    users_with_experience,
                    many=True,
                    fields=['id', 'full_name']
                ).data,
            },
            indent=4,
            default=str
        )
    )
