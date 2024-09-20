import os
import uuid
from datetime import date, datetime
from typing import Union

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.cache import cache
from django.db import models
from django.db.models import Q, Func
from django.db.models.functions import Cast
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from sorl import thumbnail

from config.settings import STATIC_ROOT
from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.common.models import ReligionAndEthnicity
from irhrs.core.constants.common import NATIONALITY_CHOICES
from irhrs.core.validators import MinMaxValueValidator
from irhrs.core.constants.user import (
    NEPAL, COUNTRY_CHOICE, GENDER_CHOICES, MARITAL_STATUS_CHOICES, SINGLE,
    SELF,
    PARTING_REASON_CHOICES,
    MALE, FEMALE, OTHER, NOT_ACTIVATED, BLOCKED, ACTIVE_USER, PERMANENT)
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import (
    get_upload_path, get_today,
    get_complete_url)
from irhrs.core.validators import (
    validate_religion, validate_ethnicity, validate_past_date,
    validate_text_only, validate_user_birth_date, validate_extension_number,
    validate_image_file_extension, validate_names_only)
from irhrs.users.utils import profile_completeness as get_profile_completeness, verify_login_change, \
    set_user_organization_permission_cache, send_logged_out_signal
from ..constants import EXTERNAL_USER_TYPE, APPLICANT
from ..managers import UserManager, UserDetailManager


INITIAL_EMPLOYEE_CODE = getattr(settings, 'INITIAL_EMPLOYEE_CODE', 'EMP')

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        _('user email'), max_length=255, unique=True,
    )
    username = models.CharField(
        _('user username'), max_length=255, unique=True, null=True
    )
    first_name = models.CharField(_('First Name'), max_length=150,
                                  validators=[validate_names_only])
    middle_name = models.CharField(_('Middle Name'), max_length=150,
                                   blank=True,
                                   validators=[validate_names_only])
    last_name = models.CharField(_('Last Name'), max_length=150,
                                 validators=[validate_names_only],
                                 blank=True)
    profile_picture = thumbnail.ImageField(
        upload_to=get_upload_path, blank=True,
        validators=[validate_image_file_extension]
    )
    _cover_picture = thumbnail.ImageField(
        upload_to=get_upload_path, db_column='cover_picture', blank=True,
        validators=[validate_image_file_extension]
    )
    signature = thumbnail.ImageField(
        upload_to=get_upload_path, blank=True,
        validators=[validate_image_file_extension]
    )

    is_active = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    last_online = models.DateTimeField(blank=True, null=True)
    is_audit_user = models.BooleanField(default=False)

    # `token_refreshed_on` will be used for validating the token. Tokens
    # created before this field will be rejected.
    token_refresh_date = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'middle_name', 'last_name']

    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.token_refresh_date = now()

    def _holiday_queryset(self, date):
        from irhrs.organization.models.holiday import Holiday
        if isinstance(date, datetime):
            date = date.date()
        user_age = relativedelta(
            dt1=date,  # how old the user was at that day?
            dt2=self.detail.date_of_birth
        ).years
        return Holiday.objects.filter(
            organization=self.detail.organization,
            rule__gender__in=['All', self.detail.gender],
            date=date
        ).filter(
            Q(rule__religion=self.detail.religion) |
            Q(rule__religion__isnull=True)
        ).filter(
            Q(rule__ethnicity=self.detail.ethnicity) |
            Q(rule__ethnicity__isnull=True)
        ).filter(
            Q(rule__division=self.detail.division) |
            Q(rule__division__isnull=True)
        ).filter(
            Q(rule__branch=self.detail.branch) |
            Q(rule__branch__isnull=True)
        ).filter(
            Q(rule__lower_age__lte=user_age) |
            Q(rule__lower_age__isnull=True)
        ).filter(
            Q(rule__upper_age__gte=user_age) |
            Q(rule__upper_age__isnull=True)
        )

    def is_holiday(self, date):
        return self._holiday_queryset(date).exists()

    def holiday_for_date(self, date):
        return self._holiday_queryset(date)

    def is_offday(self, date):
        workday = self.attendance_setting.work_day_for(date)
        return not workday

    @property
    def full_name(self):
        appends = [self.first_name]
        if self.middle_name:
            appends.append(self.middle_name)
        if self.last_name:
            appends.append(self.last_name)
        return " ".join(appends)

    @property
    def is_online(self):
        from irhrs.websocket.consumers.global_consumer import UserOnline

        return UserOnline.is_user_online(self.id) if self.id else False

    def get_short_name(self):
        return self.first_name

    def natural_key(self):
        return self.email

    @property
    def is_staff(self):
        return self.is_superuser

    def clean(self):
        self.email = self.email.lower()

    def save(self, *args, **kwargs):
        if verify_login_change(self):
            send_logged_out_signal(self)
        self.__set_username()
        self.full_clean()
        return super().save(*args, **kwargs)

    def block(self):
        """Block the user"""
        self.is_blocked = True
        self.is_active = False

    def __set_username(self):
        """set username equal to email if username is not set"""
        if not self.username:
            self.username = self.email
        else:
            self.username = self.username.lower()

    def __str__(self):
        return f"{self.full_name}"

    @property
    def account_status(self):
        if not self.is_active:
            if self.is_blocked:
                return BLOCKED
            else:
                return NOT_ACTIVATED
        return ACTIVE_USER

    @cached_property
    def user_supervisors(self):
        return self.supervisors.select_related(
            'supervisor', 'supervisor__detail',
            'supervisor__detail__organization',
            'supervisor__detail__job_title', 'supervisor__detail__division',
            'supervisor__detail__employment_level').order_by('authority_order')

    @cached_property
    def has_supervisor(self):
        return self.supervisors.exists()

    @cached_property
    def has_subordinate(self):
        return self.as_supervisor.exists()

    @cached_property
    def first_level_supervisor_including_bot(self):
        """First level supervisor including bot"""
        if self.user_supervisors:
            return self.user_supervisors[0].supervisor
        return None

    @cached_property
    def first_level_supervisor(self):
        """This will return first level supervisor, None for not set or if bot"""
        if self.user_supervisors:
            if not self.user_supervisors[0].supervisor == get_system_admin():
                return self.user_supervisors[0].supervisor
        return None

    @cached_property
    def profile_completeness(self):
        return get_profile_completeness(self)

    @cached_property
    def profile_picture_thumb_raw(self):
        # if self.email == settings.SYSTEM_BOT_EMAIL:
        #     return get_complete_url(url='logos/real-hr-leaf.png', att_type='static')
        gender = self.detail.gender if hasattr(self, 'detail') else MALE
        img = {
            MALE: 'images/default/male.png',
            FEMALE: 'images/default/female.png',
            OTHER: 'images/default/other.png'
        }
        if self.profile_picture:
            return thumbnail.get_thumbnail(
                self.profile_picture, '84x84',
                crop='center', quality=0
            )

        return os.path.join(STATIC_ROOT, img.get(gender))

    @cached_property
    def profile_picture_thumb(self):
        return self.custom_profile_pic_thumb()

    def custom_profile_pic_thumb(self, size='84x84', quality=0, crop='center'):
        gender = self.detail.gender if hasattr(self, 'detail') else MALE
        img = {
            MALE: 'images/default/male.png',
            FEMALE: 'images/default/female.png',
            OTHER: 'images/default/other.png'
        }
        if self.profile_picture:
            return get_complete_url(
                thumbnail.get_thumbnail(
                    self.profile_picture, size,
                    crop=crop, quality=quality
                ).url
            )
        return get_complete_url(url=img.get(gender), att_type='static')

    @property
    def cover_picture(self):
        return self._cover_picture

    @cover_picture.setter
    def cover_picture(self, value):
        self._cover_picture = value

    @cover_picture.getter
    def cover_picture(self):
        return self._cover_picture or f'{settings.STATIC_URL}images/default/cover.png'

    @cached_property
    def cover_picture_thumb(self):
        if self._cover_picture:
            return get_complete_url(
                thumbnail.get_thumbnail(self._cover_picture,
                                        '250x100',
                                        crop='center',
                                        padding=True, quality=0).url
            )
        return get_complete_url(self.cover_picture)

    @cached_property
    def signature_url(self):
        return get_complete_url(self.signature, att_type='media') if self.signature else None

    @cached_property
    def division(self):
        return self.current_experience.division if \
            self.current_experience else None

    @cached_property
    def oldest_experience(self):
        try:
            return self.user_experiences.all().order_by('created_at')[0]
        except IndexError:
            return None

    @cached_property
    def latest_experience(self):
        try:
            return self.user_experiences.all().order_by('-created_at')[0]
        except IndexError:
            return None

    @cached_property
    def current_experience(self):
        try:
            return self._current_experiences[0]
        except IndexError:
            return None

    @cached_property
    def _current_experiences(self):
        # prefetch to _current_experiences
        return self.user_experiences.filter(is_current=True).filter(
            Q(end_date__isnull=True) |
            Q(end_date__gte=get_today())
        )

    @cached_property
    def self_contacts(self):
        return self.contacts.filter(
            contact_of=SELF
        ) if hasattr(self, 'contacts') else None

    def get_hrs_permissions(self, organization=None):
        from irhrs.organization.models import Organization
        result = set()

        # get cache value, if not set cache
        codes = cache.get(f'permission_cache_{str(self.id)}') or ...
        if codes is ...:
            codes = set_user_organization_permission_cache(self)

        # When checking a permission of this user for `no organization` or `commons`
        if not organization:
            result = codes.get(None, set())

        # When checking for permissions against an specific organization
        elif isinstance(organization, Organization):
            result = codes.get(organization.id, set())

        elif isinstance(organization, int):
            result = codes.get(organization, set())

        # When checking for permission against a group of organization
        elif isinstance(organization, (list, set, tuple)):
            for org in organization:
                result = result.union(
                    codes.get(org.id if isinstance(org, Organization) else org) or set()
                )
        return result

    @cached_property
    def switchable_organizations_pks(self) -> set:
        return set(self.organization.filter(
            can_switch=True).values_list("organization__pk", flat=True))

    @cached_property
    def subordinates_pks(self) -> set:
        from irhrs.core.utils.subordinates import find_all_subordinates
        return find_all_subordinates(self.id)

    @cached_property
    def appoint_date(self) -> date:
        first_user_experience = self.user_experiences.order_by(
            'start_date').first()
        return first_user_experience.start_date if first_user_experience else None

    @cached_property
    def dismiss_date(self) -> Union[date, None]:
        last_user_experience = self.user_experiences.order_by(
            '-start_date').first()
        return last_user_experience.end_date if last_user_experience else None

    @cached_property
    def marital_status(self) -> str:
        return self.detail.marital_status

    def first_date_range_user_experiences(self, from_date, to_date):
        return self.date_range_user_experiences(from_date, to_date).first()

    def date_range_user_experiences(self, from_date, to_date):
        return self.user_experiences.filter(
            Q(
                Q(start_date__gte=from_date) &
                Q(start_date__lte=to_date)
            ) |
            Q(
                Q(end_date__gte=from_date) &
                Q(end_date__lte=to_date)
            ) |
            Q(  # When engulfed totally
                ~Q(end_date=None) &
                Q(
                    start_date__lte=from_date,
                    end_date__gte=to_date
                )
            ) |
            Q(
                Q(end_date=None) &
                Q(
                    start_date__lte=from_date
                )
            )
        ).order_by('start_date').distinct('start_date')

    @property
    def current_address(self):
        return self.addresses.order_by(
            # temporary if exists, else permanent
            '-address_type'
        ).values_list('address', flat=True).first() or ''


USER = get_user_model()


class UserDetail(BaseModel):
    """
    Personal / profile Details of the user.
    """
    user = models.OneToOneField(
        to=USER, related_name='detail', on_delete=models.CASCADE
    )
    code = models.CharField(max_length=15, unique=True, null=True, blank=False)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(validators=[validate_user_birth_date])
    religion = models.ForeignKey(
        to=ReligionAndEthnicity, validators=[validate_religion],
        related_name='religion_userdetails', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    ethnicity = models.ForeignKey(
        to=ReligionAndEthnicity, validators=[validate_ethnicity],
        related_name='ethnicity_userdetails', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    nationality = models.CharField(
        max_length=50, choices=NATIONALITY_CHOICES,
        default="Nepali"
    )
    marital_status = models.CharField(
        max_length=20, choices=MARITAL_STATUS_CHOICES, default=SINGLE, db_index=True
    )
    marriage_anniversary = models.DateField(
        null=True, blank=True, validators=[validate_past_date]
    )
    extension_number = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[validate_extension_number]
    )

    # this value should be same as current experience organization
    # in case of resignation current experience is None so refer to
    # this as organization
    organization = models.ForeignKey(
        to='organization.Organization', on_delete=models.CASCADE,
        related_name='userdetails', null=True, blank=True
    )
    branch = models.ForeignKey(
        to='organization.OrganizationBranch',
        on_delete=models.SET_NULL,
        related_name='userdetails',
        null=True, blank=True
    )
    division = models.ForeignKey(
        to='organization.OrganizationDivision',
        on_delete=models.SET_NULL,
        related_name='userdetails',
        null=True, blank=True
    )
    job_title = models.ForeignKey(
        to='organization.EmploymentJobTitle',
        on_delete=models.SET_NULL,
        related_name='userdetails',
        null=True, blank=True
    )
    employment_level = models.ForeignKey(
        to='organization.EmploymentLevel',
        on_delete=models.SET_NULL,
        related_name='userdetails',
        null=True, blank=True
    )
    employment_status = models.ForeignKey(
        to='organization.EmploymentStatus',
        on_delete=models.SET_NULL,
        related_name='userdetails',
        null=True, blank=True
    )

    joined_date = models.DateField(default=get_today)
    # resigned date is when resignation letter was submitted
    resigned_date = models.DateField(null=True, blank=True)
    # last working date is last day of employee in the organization
    last_working_date = models.DateField(null=True, blank=True)
    parting_reason = models.CharField(
        blank=True,
        choices=PARTING_REASON_CHOICES,
        max_length=20
    )
    completeness_percent = models.PositiveIntegerField(
        validators=[MinMaxValueValidator(0, 100)],
        default=0
    )
    objects = UserDetailManager()

    def __str__(self):
        return f"{self.user} - {self.code or 'N/A'}"

    def get_hrs_permissions(self, organization=None):
        return self.user.get_hrs_permissions(organization)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.get_new_employee_code()

        return super().save(*args, **kwargs)

    @classmethod
    def get_new_employee_code(cls):
        """
        Checks for the maximum employee code.
        Adds 1 to the max employee number to get newer one.
        """
        # https://stackoverflow.com/questions/59198776/how-do-i-make-and-access-regex-capture-groups-in-django-without-rawsql

        class EndNumeric(Func):
            function = 'REGEXP_MATCHES'
            template = r"(%(function)s(%(expressions)s, '^(.*\D)([0-9]*)$'))[2]::text"

        get_code_qs = cls.objects.filter(
            code__regex=r'({})\d'.format(INITIAL_EMPLOYEE_CODE)
        ).annotate(
            _code_number=EndNumeric('code')
        ).annotate(
            code_number=Cast('_code_number', models.IntegerField())
        )
        code = get_code_qs.order_by('code_number').values_list('code_number', flat=True).last() or 0
        return f"{INITIAL_EMPLOYEE_CODE}{code+1}"


class UserPhone(BaseModel):
    user = models.OneToOneField(
        to=USER, on_delete=models.CASCADE,
        related_name='uphone'
    )
    country_code = models.CharField(
        default=NEPAL, choices=COUNTRY_CHOICE, max_length=5
    )
    phone = models.CharField(max_length=12, unique=True)
    is_verified = models.BooleanField(default=False)
    verification_sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.country_code}-{self.phone} " + self.phone + '||' + 'is' if self.is_verified \
            else 'isn\'t' + 'verified'


# User that are no associated with RealHr and doesnot has user instance
class ExternalUser(TimeStampedModel):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False
    )
    full_name = models.CharField(
        _('Full Name'),
        max_length=150,
        validators=[validate_text_only]
    )
    profile_picture = thumbnail.ImageField(
        upload_to=get_upload_path,
        blank=True
    )
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=30
    )
    email = models.EmailField(max_length=50)

    # User Detail
    gender = models.CharField(
        max_length=6,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )
    marital_status = models.CharField(
        choices=MARITAL_STATUS_CHOICES,
        null=True, blank=True,
        max_length=50, db_index=True
    )
    dob = models.DateField(
        _("Date of Birth"),
        blank=True,
        null=True,
        validators=[validate_user_birth_date]
    )

    user_type = models.CharField(
        max_length=30,
        choices=EXTERNAL_USER_TYPE,
        default=APPLICANT
    )
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name

    @property
    def is_applicant(self):
        return hasattr(self, 'applicant')

    @property
    def is_interviewer(self):
        return hasattr(self, 'interviewer')

    @property
    def is_reference_checker(self):
        return hasattr(self, 'reference_checker')

    @staticmethod
    def calculate_age(dob):
        if not dob:
            return 'N/A'

        today = get_today()
        total_year_difference = today.year - dob.year
        return total_year_difference - (
            (today.month, today.day) < (dob.month, dob.day))

    @property
    def age(self):
        return self.calculate_age(self.dob)

    @cached_property
    def profile_picture_thumb(self):
        gender = self.gender or MALE
        img = {
            MALE: 'images/default/male.png',
            FEMALE: 'images/default/female.png',
            OTHER: 'images/default/other.png'
        }
        if self.profile_picture:
            return get_complete_url(
                thumbnail.get_thumbnail(
                    self.profile_picture, '84x84',
                    crop='center', quality=0
                ).url
            )
        return get_complete_url(url=img.get(gender), att_type='static')
