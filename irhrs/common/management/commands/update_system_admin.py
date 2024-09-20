from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import BaseCommand

from irhrs.core.utils import get_system_admin

USER = get_user_model()


class Command(BaseCommand):
    help = "Checks the system for necessary dependencies"

    def handle(self, *args, **options):
        bot_email_from_settings = getattr(settings, 'SYSTEM_BOT_EMAIL',
                                          'irealhrbot@irealhrsoft.com')
        old_email = options.get('old_email', None)
        bot_email = old_email or bot_email_from_settings

        try:
            user = USER.objects.get(email=bot_email)
        except USER.DoesNotExist:
            # If user does not exists, create a user and return
            assert old_email is None, f'User with {old_email} does not exist.'
            get_system_admin()
            return

        new_email = options.get('new_email')

        if new_email:
            assert bot_email_from_settings == new_email,\
                f"New email {new_email} is not set in settings SYSTEM_BOT_EMAIL"

        bot_name = getattr(settings, 'SYSTEM_BOT_NAME', 'RealHR Soft')

        __names = bot_name.split()
        first_name = __names[0]
        if len(__names) >= 2:
            last_name = __names[1]
        else:
            last_name = ""

        if new_email:
            user.email = new_email

        user.first_name = first_name
        user.last_name = last_name
        user.middle_name = ''

        profile_pic = None
        profile_pic_name = getattr(settings, 'SYSTEM_BOT_PROFILE_IMAGE', None)
        if profile_pic_name:
            profile_pic = staticfiles_storage.open(profile_pic_name)

        user.profile_picture = profile_pic
        user.save()

        if profile_pic:
            profile_pic.close()

        print(f"Successfully update bot account <{user}>.")

    def add_arguments(self, parser):
        parser.add_argument('--old-email',
                            help="Old email of system bot to update.",
                            )
        parser.add_argument('--new-email',
                            help="New email of system bot.",
                            )
        super().add_arguments(parser)

