import base64
import logging
import os

from django.contrib.auth import get_user_model
from django.utils import timezone

from config.settings import STATIC_ROOT, GIFT_CARD_CONFIG
from irhrs.core.constants.user import MALE, FEMALE, OTHER
from irhrs.noticeboard.utils.gift_card_generator import (GenerateCards)

logger = logging.getLogger(__name__)

User = get_user_model()


def calculate_anniversary(joined_date):
    """
    Calculate the number of worked years
    :param in_date: joined date for the user
    :return: number of worked year (integer)
    """
    present_year = timezone.now().astimezone().year
    joined_year = joined_date.year
    return present_year - joined_year


def get_profile_picture(user):
    """
    To get profile picture for user if exists else default image with respect
    to gender of user
    :param user: instance of user model
    :return: absolute url for the profile picture (string)
    """
    profile_picture = user.profile_picture_thumb_raw

    def _get_default_profile_picture(img):
        with open(os.path.join(STATIC_ROOT, img), 'rb') as _profile_picture:
            return base64.b64encode(_profile_picture.read()).decode('utf-8')

    if isinstance(profile_picture, str):
        return _get_default_profile_picture(img=profile_picture)

    try:
        return base64.b64encode(profile_picture.read()).decode('utf-8')
    except (ValueError, FileNotFoundError):
        logger.info(
            f'Profile picture for {user} not found'
        )
        img = {
            MALE: 'images/default/male.png',
            FEMALE: 'images/default/female.png',
            OTHER: 'images/default/other.png'
        }
        return _get_default_profile_picture(
            img=img.get(
                user.detail.gender if hasattr(user, 'detail') else MALE
            )
        )


def generate_birthday_card():
    """
    Task for generating anniversary greeting card for users

    :return:
    """

    users = User.objects.filter(detail__date_of_birth__day=timezone.now().astimezone().day,
                                detail__date_of_birth__month=timezone.now().astimezone().month,
                                is_active=True, is_blocked=False,
                                user_experiences__is_current=True)
    generate_card = GenerateCards(
        config_data=GIFT_CARD_CONFIG.get('birthday'),
        users=users
    )
    generate_card.generate_birthday_and_anniversary_card()


def generate_anniversary_card():
    """
    Task for generating anniversary greeting card for users

    :return:
    """
    users = User.objects.select_related('detail').filter(
        detail__joined_date__day=timezone.now().astimezone().day,
        detail__joined_date__month=timezone.now().astimezone().month,
        is_active=True, is_blocked=False,
        user_experiences__is_current=True
    )

    # generate anniversary card
    _old_users = users.filter(detail__joined_date__year__lt=timezone.now().astimezone().year)
    if _old_users:
        generate_card = GenerateCards(
            config_data=GIFT_CARD_CONFIG.get('anniversary'),
            users=_old_users
        )
        generate_card.generate_birthday_and_anniversary_card()

    # generate welcome card
    _new_users = users.filter(detail__joined_date__year=timezone.now().astimezone().year)
    if _new_users:
        generate_card = GenerateCards(
            config_data=GIFT_CARD_CONFIG.get('welcome'),
            users=_new_users
        )
        generate_card.generate_birthday_and_anniversary_card()


def generate_gift_card():
    generate_birthday_card()
    generate_anniversary_card()
