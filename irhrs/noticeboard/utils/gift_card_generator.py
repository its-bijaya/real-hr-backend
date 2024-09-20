import logging
import os
import uuid

import svgwrite
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

import irhrs.noticeboard.utils.svg_transform as st
from config.settings import APPS_DIR, MEDIA_ROOT
from irhrs.core.constants.common import OTHER
from irhrs.core.constants.noticeboard import AUTO_GENERATED
from irhrs.core.constants.organization import ANNIVERSARY_EMAIL, BIRTHDAY_EMAIL
from irhrs.core.constants.user import MALE, FEMALE
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.common import get_today
from irhrs.core.utils.custom_mail import custom_mail
from irhrs.core.utils.email import can_send_email
from irhrs.noticeboard.models import Post, PostAttachment
from irhrs.notification.utils import add_notification

logger = logging.getLogger(__name__)


class SvgDrawing:
    """
    this SvgDrawing context manager helps to create
    base file for svg
    """

    def __init__(self, filename, size):
        self.filename = filename
        self.size = size
        self.file = None

    def __enter__(self):
        dwg = svgwrite.Drawing(self.filename, self.size)
        self.file = dwg
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            os.remove(self.filename)
        except FileNotFoundError:
            pass


def merge_svg(static_path, dummy=None):
    """
    It helps to merge two SVG files. It merges generated svg with respective
    SVG templates

    :param static_path: relative path for static files
    :type static_path: string

    :param dummy: it hold the string specifying whether to generate birthday
                card or anniversary card
    :type dummy: string

    :return:
    """
    dummy_svg = st.formfile_custom(
        os.path.join(static_path, f'samples/{dummy}.svg'))
    generated_svg = st.formfile_custom(
        os.path.join(static_path, 'samples/generated.svg'))

    dummy_svg.append(generated_svg)

    file_path = MEDIA_ROOT + f'uploads/noticeboard/attachments/'
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    output_path = file_path + f"{uuid.uuid4().hex}.svg"
    dummy_svg.save(output_path)
    return output_path.split('media/')[1]


def birthday_gift_card(name, image=None):
    """
    This method helps to create birthday gift card.
    It generates SVG file for specified user.

    :param name: name of the user whose card needs to be generated
    :type name: string

    :param image: absolute path of the image (profile picture or any other
                    image that need's to be displayed)
    :type image: string

    :return: relative path for created birthday gift card
    """
    static_path = os.path.join(APPS_DIR, 'static')
    with SvgDrawing(
        filename=os.path.join(static_path, 'samples/generated.svg'),
        size=('840px', '728px')) as dwg:
        clip_path = dwg.defs.add(dwg.clipPath(id="myCircle"))
        clip_path.add(dwg.circle(center=(475, 525), r=35))
        if image:
            dwg.add(
                dwg.image('data:image/png;base64,' + image,
                          insert=(440, 490), size=("70px", "70px"),
                          clip_path="url(#myCircle)"))

        add_name(dwg=dwg, full_name=name, x_ordinate=530, y_ordinate=515)
        dwg.save()
        return merge_svg(static_path, dummy='birthday')


def anniversary_gift_card(name, image, anniversary):
    """
    This method helps to create birthday gift card.
    It generates SVG file for specified user.

    :param name: name of the user whose card needs to be generated
    :type name: string

    :param image: absolute path of the image (profile picture or any other
                    image that need's to be displayed)
    :type image: string

    :param anniversary: it represent how many year an user has worked
    :type anniversary: integer

    :return: relative path for created birthday gift card
    """
    static_path = os.path.join(APPS_DIR, 'static')
    with SvgDrawing(filename=os.path.join(static_path, 'samples/generated.svg'),
                    size=('840px', '728px')) as dwg:
        clip_path = dwg.defs.add(dwg.clipPath(id="myCircle"))
        clip_path.add(dwg.circle(center=(460, 400), r=35))
        if image:
            dwg.add(dwg.image('data:image/png;base64,' + str(image),
                              insert=(425, 365), size=("70px", "70px"),
                              clip_path="url(#myCircle)"))

        dwg.add(
            dwg.text(anniversary, x=[610 if anniversary < 10 else 585], y=[250],
                     font_weight="bold", font_size="95px",
                     font_family="Poppins", fill="white"))

        add_name(dwg=dwg, full_name=name, x_ordinate=505, y_ordinate=390)
        dwg.save()
        return merge_svg(static_path, dummy='anniversary')


def add_name(dwg, full_name, x_ordinate, y_ordinate):
    """
    to add name on svg file according  to the length of full_name
    :param dwg: svg canvas name
    :param full_name: name of user
    :param x_ordinate: x co-ordinate for name to be display
    :param y_ordinate: y co-ordinate for name to be display
    :return: none
    """
    if len(full_name) > 31:
        for index, name in enumerate(full_name.split()):
            dwg.add(
                dwg.text(name, x=[x_ordinate],
                         y=[y_ordinate + index * 20],
                         font_weight="bold",
                         font_size="23px",
                         font_family="Poppins", fill="black"))
    else:
        dwg.add(
            dwg.text(full_name, x=[x_ordinate], y=[y_ordinate + 20],
                     font_weight="bold",
                     font_size="23px",
                     font_family="Poppins", fill="black"))


class GenerateCards:
    image = None
    texts = None

    def __init__(self, config_data=None, users=None):
        # The config data is defined at: config/settings/configurations.py
        self.config_data = config_data
        self.thumb_width = config_data.get('thumbnail').get('width')
        self.event = config_data.get('event')
        self.template = os.path.join(
            os.path.join(APPS_DIR, 'static'),
            f'samples/{config_data.get("template")}'
        )
        self.thumb_coordinate = config_data.get('thumbnail').get('position')
        self.message = config_data.get('message')
        self.users = users
        self.alignment = config_data.get('alignment')

    def generate_circle_thumbnail(self):
        with Image.open(self.image) as im:
            im_square = self.crop_max_square(im).resize((self.thumb_width, self.thumb_width),
                                                        Image.LANCZOS)
            im_thumb = self.mask_circle_transparent(im_square, 4)
            # im_thumb.save('circular_thumb.png', quality=95)
            return im_thumb

    def crop_max_square(self, pil_img):
        return self.crop_center(pil_img, min(pil_img.size), min(pil_img.size))

    @staticmethod
    def crop_center(pil_img, crop_width, crop_height):
        img_width, img_height = pil_img.size
        return pil_img.crop(((img_width - crop_width) // 2,
                             (img_height - crop_height) // 2,
                             (img_width + crop_width) // 2,
                             (img_height + crop_height) // 2))

    @staticmethod
    def mask_circle_transparent(pil_img, blur_radius=0, offset=0):
        offset = blur_radius * 2 + offset
        # creates new canvas with transparent fill
        # here first parameter is used for mode of image. Here 'l' defines black and white mode
        # second parameter defines size of canvas
        # third parameter is used for transparency 0 means 100 % transparent
        # where as 100 means 0% transparent
        mask = Image.new("L", pil_img.size, 0)
        draw = ImageDraw.Draw(mask)

        if offset != 0:
            draw.ellipse((offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset),
                         fill=255)

        result = pil_img.copy()
        result.putalpha(mask)

        return result

    def generate_texts(self, config_data, user):
        text = config_data.get('texts')
        name = config_data.get('name')
        name.update(
            {
                'title': f'Dear {user.full_name},' if self.event.lower() == "birthday" else user.full_name
            }
        )
        if self.event == 'welcome':
            job_title = config_data.get('job_title', None)
            if job_title:
                job_title.update({
                    'title': nested_getattr(user, 'detail.job_title.title') or 'N/A'
                })
                text.append(job_title)
            division = config_data.get('division', None)
            if division:
                division.update({
                    'title': nested_getattr(user, 'detail.division.name') or 'N/A'
                })
                text.append(division)
            employment_level = config_data.get('employment_level', None)
            if employment_level:
                employment_level.update({
                    'title': nested_getattr(user, 'detail.employment_level.title') or 'N/A'
                })
                text.append(employment_level)
            organization = config_data.get('organization', None)
            if organization:
                organization.update({
                    'title': nested_getattr(user, 'detail.organization.name') or 'N/A'
                })
                text.append(organization)

        anniversary_wish = config_data.get('anniversary_wish', None)
        if anniversary_wish and self.event == 'anniversary':
            anniversary_year = self.calculate_anniversary(user.detail.joined_date)
            anniversary_wish.update(
                {
                    'title': '{} {} of Excellence'.format(
                        anniversary_year,
                        'Years' if anniversary_year > 1 else 'Year'
                    ),
                    'years': anniversary_year
                }
            )
            text.append(anniversary_wish)
        text.append(name)
        return text

    def add_images(self, img2, user_obj):
        with Image.open(self.template) as img1:
            img1.paste(img2, tuple(self.thumb_coordinate), img2)
            image_canvas = ImageDraw.Draw(img1)
            self.add_text(image_canvas)
            final_image = img1.convert('RGB')

            file_path = MEDIA_ROOT + f'uploads/noticeboard/attachments/'
            if not os.path.exists(file_path):
                os.makedirs(file_path)

            output_path = file_path + f"{uuid.uuid4().hex}.jpeg"
            final_image.save(output_path, 'JPEG', quality=50)
            return output_path.split('media/')[1]

    def add_text(self, image):
        """
        color must me tuple of three parameters (x, y, z) 'RBG format'
        """
        for text in self.texts:
            title = text.get('title')
            font_path = os.path.join(
                os.path.join(APPS_DIR, 'static'),
                f'samples/{text.get("font")}'
            )
            font = ImageFont.truetype(font_path,
                                      text.get('font_size'))
            image.text(
                self.calculate_coordinate_for_text(*text.get('coordinates'),
                                                   font.getsize(title)[0]),
                title, fill=tuple(text.get('color')), font=font
            )

    def calculate_coordinate_for_text(self, x, y, text_size):
        offset = 0
        if self.alignment == "center":
            offset = text_size // 2
        elif self.alignment == "right":
            offset = text_size
        return x - offset, y

    @staticmethod
    def calculate_anniversary(joined_date):
        """
        Calculate the number of worked years
        :param joined_date: joined date for the user
        :return: number of worked year (integer)
        """
        present_year = timezone.now().astimezone().year
        joined_year = joined_date.year
        return present_year - joined_year

    @staticmethod
    def get_profile_picture(user):
        """
        To get profile picture for user if exists else default image with respect
        to gender of user
        :param user: instance of user model
        :return: absolute url for the profile picture (string)
        """
        try:
            profile_picture = user.profile_picture.path
        except ValueError:
            profile_picture = None
        if not profile_picture or not os.path.exists(profile_picture):
            logger.info(
                f'Profile picture for {user} not found'
            )
            static_root = os.path.join(APPS_DIR, 'static')
            img = {
                MALE: static_root + '/images/default/male.png',
                FEMALE: static_root + '/images/default/female.png',
                OTHER: static_root + '/images/default/other.png'
            }
            return img.get(user.detail.gender if hasattr(user, 'detail') else MALE)
        return profile_picture

    @staticmethod
    def get_unique_post_generated_users(users, config_data):
        post_generated_users = Post.objects.filter(
            created_at__date=get_today(), user_tags__in=users, category=AUTO_GENERATED
        )
        unique_post_generated_users = post_generated_users.filter(
            post_content__startswith=config_data['message']
        ).values_list('user_tags', flat=True)
        return unique_post_generated_users

    def generate_birthday_and_anniversary_card(self):
        unique_post_generated_users = self.get_unique_post_generated_users(self.users, self.config_data)

        for user in self.users:
            if user.id not in unique_post_generated_users:
                self.texts = self.generate_texts(self.config_data, user)
                self.image = self.get_profile_picture(user=user)
                image_path = self.add_images(self.generate_circle_thumbnail(), user)
                self.post_on_noticeboard(self.message, image_path, user, self.texts)
                logger.info(
                    f"{self.event.upper()} post generated for {user}"
                )

    def post_on_noticeboard(self, message, image_path, user=None, texts=None):
        post = Post.objects.create(
            post_content=message,
            category=AUTO_GENERATED,
            posted_by=get_system_admin()
        )
        post_attachment = PostAttachment(post=post, caption='')
        post_attachment.image = image_path
        post_attachment.save()

        if user:
            post.user_tags.add(user)

            if self.config_data.get('event') == 'anniversary':
                years = texts[0].get('years') if texts else \
                    self.calculate_anniversary(user.detail.joined_date)

                # https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
                ordinal = (
                    lambda n: "%d%s" % (
                        n,
                        # (n // 10 % 10 != 1) => Digit at 10th place is 1 (exception) all th
                        # (n % 10 < 4) * n % 10 => Index st nd rd by index for less than 4
                        # If above two conditions are true uses index (1=>st, 2=>nd, 3=>rd) else
                        # Uses default 0=>st
                        "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
                )(years)

                wish = f"Congratulations {user.full_name} on your {ordinal} work anniversary."
                email_type = ANNIVERSARY_EMAIL
            else:
                wish = f"Happy Birthday {user.full_name}."
                email_type = BIRTHDAY_EMAIL
            add_notification(
                text=f"{wish} Your {self.config_data.get('event')} card has been posted on"
                     f" noticeboard.",
                actor=get_system_admin(),
                action=post,
                recipient=user,
                url=f"/user/posts/{post.id}/"
            )

            if can_send_email(user, email_type):
                info_email = getattr(settings, 'INFO_EMAIL', 'noreply@realhrsoft.com')

                message = wish
                html_message = render_to_string(
                    'notifications/notification_base.html',
                    context={
                        'message': wish
                    }
                )
                subject = f"{self.config_data.get('event').title()} wish"

                custom_mail(
                    subject=subject,
                    message=message,
                    html_message=html_message,
                    from_email=info_email,
                    recipient_list=[user.email]
                )


