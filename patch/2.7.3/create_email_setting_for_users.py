from django.contrib.auth import get_user_model

from irhrs.hris.models.email_setting import EmailSetting

USER = get_user_model()


def email_setting_for_user():
    users = USER.objects.filter(is_active=True, is_blocked=False)
    email_settings = []
    for user in users:
        email_settings.append(
            EmailSetting(user=user)
        )
    EmailSetting.objects.bulk_create(email_settings)
    print('Created Email Setting.')
