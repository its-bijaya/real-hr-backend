"""Copy employee code to username (Currently for Laxmi Bank)"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError


User = get_user_model()


def main():
    failed_users = []
    for user in User.objects.all().current().select_related('detail'):
        emp_code = user.detail.code
        if emp_code:
            user.username = emp_code

            try:
                user.save()

            except IntegrityError:
                failed_users.append((user.get('id'), emp_code))

    if len(failed_users) > 1:
        print(f"failed users list are: {failed_users}")


if __name__ == '__main__':
    main()
