from django.contrib.auth import get_user_model

USER = get_user_model()
old_email_to_username_map = {
    'old@email.com': 'new.username'
}

for old_email, new_username in old_email_to_username_map.items():
    try:
        user = USER.objects.get(email=old_email)
        old_username = user.username
    except USER.DoesNotExist:
        print(old_email, 'does not belong to a user')
        continue
    user.username = new_username
    user.save()
    print(
        old_username,
        '-->',
        new_username
    )
