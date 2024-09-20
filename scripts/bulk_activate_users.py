from django.db import transaction
from django.utils.crypto import get_random_string

from irhrs.users.models.user import User

CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)'

@transaction.atomic
def main():
    # set organization_slug only if you want to activate users of given organization
    organization_slug = ""
    users = User.objects.filter(is_active=False, is_blocked=False)
    if organization_slug:
        users = users.filter(detail__organization__slug=organization_slug)

    for index, user in enumerate(users):
        user.is_active = True
        user.set_password(get_random_string(8, CHARS))
        user.save()
        print(f"Successfully activated account of {user.full_name}")
        print(f"Successfully activated account of {index} users")


if __name__ == "__main__":
    main()
