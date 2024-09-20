"""@irhrs_docs"""
import logging
from datetime import time

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
from django.db import transaction
from django.db.models import Subquery
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.timezone import now
from django_q.models import Schedule
from django_q.tasks import async_task

from irhrs.core.constants.organization import GLOBAL
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_today, combine_aware
from irhrs.hris.constants import EXPIRED, POST_TASK_COMPLETED
from irhrs.websocket.helpers import send_for_group as websocket_group

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
logger = logging.getLogger(__name__)


def send_activation_mail(request, user):
    """
    Send user activation mail.
    :param request: request instance
    :param user: user instance
    :return: None
    """
    if not (user.is_active or user.is_blocked):
        token_generator = PasswordResetTokenGenerator()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        uidb64 = uidb64 if type(uidb64) == str else uidb64.decode()
        token = token_generator.make_token(user)
        url = FRONTEND_URL + '/account/activate/' + uidb64 + '/' + token + '/'
        context = {
            "full_name": user.full_name,
            "email": user.email,
            "activation_link": url
        }

        message = render_to_string('users/activation_email.txt',
                                   context=context,
                                   request=request)

        html_message = render_to_string(
            'users/activation_email.html',
            context=context,
            request=request)
        subject = "RealHRSoft Account Activation"
        from irhrs.core.utils.custom_mail import custom_mail as send_mail
        async_task(send_mail, subject, message, "admin@realhrsoft.com",
                   [user.email],
                   html_message=html_message)


def get_default_date_of_birth():
    """
    return date 18 years from now.
    Used for setting initial birth date
    """
    return timezone.now().date() - timezone.timedelta(days=365 * 18)


def profile_completeness(user):
    total = 0
    # general info
    if hasattr(user, 'detail'):
        total += 10

    else:
        return total

    if user.profile_picture:
        total += 10

    if user.detail.religion:
        total += 10

    if user.detail.ethnicity:
        total += 10

    if user.contacts.exists():
        total += 10

    if user.addresses.exists():
        total += 10

    if hasattr(user, 'medical_info'):
        total += 10

    if hasattr(user, 'legal_info'):
        total += 10

    if user.languages.exists():
        total += 10

    if user.user_education.exists():
        total += 10

    return total


def terminate_user_for_date(experience_id):
    """
    The users, who have been terminated for future date will be active until
    the terminated date. Therefore, this task will ensure the user will
    become inactive and blocked after the given date.
    :param experience: The terminated user experience.
    :param end_date: The last working date for the user
    :return: Success
    """
    from irhrs.users.models import UserExperience
    experience = UserExperience.objects.get(pk=experience_id)
    _BLOCKED_SUCCESSFULLY = True
    _FAILED_TO_BLOCK = False
    today = get_today()
    end_date = experience.end_date
    if not end_date <= today:
        params = {
            'experience_id': experience.id
        }
        Schedule.objects.create(
            func='irhrs.users.utils.terminate_user_for_date',
            kwargs=params,
            next_run=combine_aware(
                end_date + timezone.timedelta(days=1),
                time(0, 5)
            ),
            schedule_type=Schedule.ONCE,
            repeats=-1
        )
        return {
            _FAILED_TO_BLOCK:
                f"The user is to be terminated in {end_date} not on {today}"
        }
    user = experience.user
    experience.is_current = False
    experience.save()
    # A valid user for block is active unblocked user.
    valid_user_for_block = user.is_active and not user.is_blocked
    if not valid_user_for_block:
        logger.info(f"Failed User Termination {user.full_name} with "
                    f"pk {user.pk} as user is already blocked or inactive.")
        return {
            _FAILED_TO_BLOCK: "The user is either inactive or already blocked"
        }
    logger.info(f"Terminating User {user.full_name} with pk {user.pk}")
    actions_performed = []
    if user.is_active:
        user.is_active = False
        actions_performed.append('Deactivated')
    if not user.is_blocked:
        user.is_blocked = True
        actions_performed.append('Blocked')
    user.save(update_fields=['is_active', 'is_blocked'])
    logger.info(f"Terminated user {user.full_name} with pk {user.pk} with "
                f"actions: {', '.join(actions_performed)}")
    return {
        _BLOCKED_SUCCESSFULLY: f"The user was {', '.join(actions_performed)}"
    }


def verify_login_change(instance):
    if instance and instance.pk:
        login_fields = ('username', 'email',)
        old_instance = get_user_model().objects.get(
            pk=instance.pk
        )
        login_changed = any(
            map(
                lambda f: getattr(instance, f) != getattr(old_instance, f),
                login_fields
            )
        )
        if login_changed:
            instance.token_refresh_date = now()
            return True


def auto_expire_offer_letters():
    from irhrs.hris.constants import SENT as EMAIL_SENT
    from irhrs.hris.models.onboarding_offboarding import GeneratedLetter
    offer_letters_to_expire = GeneratedLetter.objects.filter(
        status=EMAIL_SENT,
        preemployment__deadline__lt=timezone.now()
    )
    with transaction.atomic():
        offer_letters_to_expire.update(status=EXPIRED)
        # for expired_letter in offer_letters_to_expire:
        #     add_notification(
        #         recipient=expired_letter.created_by,
        #         action=expired_letter,
        #         text=f"{expired_letter.preemployment.full_name}'s Offer letter "
        #              f"has expired."
        #     )


def get_auto_increment_change_type(organization):
    from irhrs.hris.models import ChangeType
    obj, _ = ChangeType.objects.get_or_create(
        organization=organization,
        title='Step Increment',
        affects_experience=True,
        defaults=dict(
            affects_payroll=True,
            affects_work_shift=False,
            affects_core_tasks=True,
            affects_leave_balance=False,
        )
    )
    return obj


def apply_auto_increment():
    from irhrs.hris.models import ChangeType
    from irhrs.hris.models import EmploymentReview
    from irhrs.core.constants.common import YEARS, DAYS, MONTHS
    from irhrs.users.models import UserExperience
    from django.contrib.auth import get_user_model
    exclude_experiences = EmploymentReview.objects.filter(
        change_type__in=ChangeType.objects.filter(
            title='Step Increment'
        )
    ).values_list(
        'change_type__details__old_experience_id', flat=True
    )
    users_with_upcoming_experience = get_user_model().objects.filter(
        user_experiences__upcoming=True
    ).distinct().values_list('id', flat=True)
    valid_experiences = UserExperience.objects.exclude(
        user_id__in=Subquery(users_with_upcoming_experience)
    ).filter(
        is_current=True,
    ).filter(
        employee_level__auto_increment=True,
        employee_level__auto_add_step__isnull=False,
        employee_level__changes_on_fiscal__isnull=False,
        employee_level__frequency__isnull=False,
        employee_level__duration__isnull=False,
    ).filter(
        old_change_types__isnull=True
    ).exclude(
        id__in=exclude_experiences
    )
    incremented = list()

    fiscal_based_list = valid_experiences.filter(
        employee_level__changes_on_fiscal=True
    )
    duration_based_list = valid_experiences.filter(
        employee_level__changes_on_fiscal=False
    )
    from irhrs.organization.models import Organization, FiscalYear

    for org in Organization.objects.all():
        last_fiscal = FiscalYear.objects.filter(
            organization=org,
            applicable_to__lte=get_today(),
            category=GLOBAL
        ).order_by(
            '-applicable_to'
        ).first()
        # if fiscal and fiscal year completed within one week.
        if last_fiscal and (get_today() - last_fiscal.applicable_to).days in range(7):
            for experience in fiscal_based_list.exclude(
                # exclude experiences created after the end of fiscal year.
                start_date__gte=last_fiscal.applicable_to
            ):
                add_value = experience.employee_level.frequency
                add_duration = experience.employee_level.duration
                relative_delta_value = {
                    DAYS: 'days',
                    MONTHS: 'months',
                    YEARS: 'years'
                }.get(add_duration)
                if experience.user.detail.joined_date <= (
                    last_fiscal.applicable_to - relativedelta(
                    **{relative_delta_value: add_value}
                )
                ):
                    incremented.append(
                        increment_experience(experience)
                    )

    for user_experience in duration_based_list:
        start = user_experience.start_date
        add_value = user_experience.employee_level.frequency
        add_duration = user_experience.employee_level.duration
        relative_delta_value = {
            DAYS: 'days',
            MONTHS: 'months',
            YEARS: 'years'
        }.get(add_duration)
        date_of_increment = start + relativedelta(
            **{relative_delta_value: add_value}
        )
        if date_of_increment <= get_today():
            incremented.append(
                increment_experience(user_experience)
            )
    return incremented


def copy_core_tasks(detail):
    new_experience = detail.new_experience
    old_experience = detail.old_experience
    user_result_areas = old_experience.user_result_areas.all()
    if not user_result_areas:
        return
    for user_result_area in user_result_areas:
        core_tasks = user_result_area.core_tasks.all()
        user_result_area.id = None
        user_result_area.user_experience = new_experience
        user_result_area.save()
        for core_task in core_tasks:
            user_result_area.core_tasks.add(core_task)


def increment_experience(user_experience):
    from irhrs.hris.api.v1.serializers.onboarding_offboarding import EmploymentReviewSerializer
    change_type = get_auto_increment_change_type(
        organization=user_experience.organization
    )
    ser = EmploymentReviewSerializer()
    value_to_add = user_experience.employee_level.auto_add_step
    new_experience = user_experience
    new_experience.id = None
    new_experience.current_step = min(
        new_experience.current_step + value_to_add,
        new_experience.employee_level.scale_max
    )
    new_experience.upcoming = True
    new_experience.is_current = False
    new_experience.start_date = get_today()
    if not new_experience.employment_status.is_contract:
        new_experience.end_date = None
    new_experience.save()
    obj = ser.create({
        'employee': user_experience.user,
        'change_type': change_type,
        'status': POST_TASK_COMPLETED
    })
    detail = obj.detail
    detail.new_experience = new_experience
    package_slots = nested_getattr(
        detail, 'old_experience.user_experience_packages.all'
    )
    if package_slots:
        detail.new_payroll = getattr(package_slots.order_by(
            '-active_from_date'
        ).first(), 'package', None)
    detail.save()
    copy_core_tasks(detail)
    return obj


def set_user_organization_permission_cache(user):
    from irhrs.permission.models.hrs_permisssion import OrganizationGroup
    switchable_organizations_pks = user.switchable_organizations_pks
    groups = set(user.groups.all())
    codes_org_queryset = list(
        OrganizationGroup.objects.filter(
            permissions__organization_specific=True,
            organization__in=switchable_organizations_pks
        ).filter(
            group__in=groups
        ).order_by('organization', 'permissions__code').values_list(
            'organization',
            'permissions__code'
        )
    )
    org_perm_dict = {
        None: set(
            OrganizationGroup.objects.filter(
                organization=None,
                permissions__organization_specific=False
            ).filter(
                group__in=groups
            ).order_by('permissions__code').values_list(
                'permissions__code',
                flat=True
            )
        ) - {None}
    }
    for org in switchable_organizations_pks:
        org_perm_dict[org] = set(
            map(
                lambda x: x[1],
                filter(lambda x: x[0] == org, codes_org_queryset)
            )
        ) - {None}
    cache.set(
        key=f'permission_cache_{str(user.id)}',
        value=org_perm_dict,
    )
    return org_perm_dict


def send_logged_out_signal(user):
    """Send logout through web socket"""
    _success = websocket_group(str(user.id),
                               data={"message": "Your have been logged out."},
                               msg_type='logged_out')


def send_user_update_signal(user):
    """Send user update info through web socket"""
    from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
    user_detail = {
        'user': UserThinSerializer(
            user,
            fields=['id', 'full_name', 'profile_picture', 'job_title', 'email', 'organization', 'is_current',]
        ).data
    }
    websocket_group(
        group_name=str(user.id),
        data=user_detail,
        msg_type='user_update'
    )
