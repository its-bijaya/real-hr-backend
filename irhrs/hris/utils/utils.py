"""@irhrs_docs"""
import re

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import transaction
from django.db.models import (
    Case, When, IntegerField, Value, BooleanField,
    DateField, F, Subquery, OuterRef, Sum, Q, FilteredRelation, QuerySet,
    ExpressionWrapper, DurationField)
from django.db.models.functions import (
    ExtractMonth, ExtractDay, Cast, Concat,
    Coalesce, Extract, Greatest)
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.common import (
    get_today, get_tomorrow,
    timeout_for_midnight, format_timezone)
from irhrs.core.utils.nepdate import ad2bs, string_from_tuple
from irhrs.users.models import UserDetail
from irhrs.users.utils.common_utils import profile_completeness
from irhrs.hris.constants import (
    OFFER_LETTER, CHANGE_TYPE, ONBOARDING,
    OFFBOARDING, BOTH, EMPLOYEE_DIRECTORY, HOLD, STOPPED, COMPLETED,
    UPCOMING, NEW,
    POST_TASK_COMPLETED)
from irhrs.hris.models.onboarding_offboarding import (
    TaskTemplateMapping,
    EmploymentReview, LeaveChangeType,
    EmployeeSeparation, LeaveEncashmentOnSeparation)
from irhrs.leave.constants.model_constants import ADDED, DEDUCTED, APPROVED, GENERATED, \
    EMPLOYEE_SEPARATION
from irhrs.leave.models import LeaveAccountHistory, LeaveSheet
from irhrs.leave.models.account import LeaveEncashment
from irhrs.leave.tasks import get_active_master_setting
from irhrs.leave.utils.balance import get_fiscal_year_for_leave, HOURLY_LEAVES
from irhrs.organization.models import FiscalYear, UserOrganization
from irhrs.permission.api.v1.serializers.organization import clear_permission_cache
from irhrs.permission.constants.permissions.hrs_permissions import (
    HRIS_EMPLOYMENT_REVIEW_PERMISSION,
    HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION
)
from irhrs.task.models.task import RecurringTaskDate
from irhrs.notification.utils import add_notification
from irhrs.users.models import UserExperience
from irhrs.notification.utils import notify_organization

fernet = Fernet(settings.FERNET_KEY)


def upcoming_birthdays(qs, start_date=None, **kwargs):
    """
    custom method to calculate upcoming birthdays
    and returns the queryset
    """
    today = start_date or timezone.now()
    next_year = today.year + 1

    qs = qs.filter(detail__date_of_birth__lt=today, **kwargs).annotate(
        born_month=ExtractMonth('detail__date_of_birth')
    ).annotate(
        born_day=Case(
            When(born_month=2, detail__date_of_birth__day=29, then=28),
            default=ExtractDay('detail__date_of_birth'),
            output_field=IntegerField())
    ).filter(
        born_day__gte=Case(When(born_month=today.month, then=today.day),
                           default=0)
    ).annotate(
        birth_year=Case(
            When(born_month__lt=today.month, then=next_year),
            When(born_month=today.month, born_day__lt=today.day,
                 then=next_year),
            default=today.year, output_field=IntegerField()),

        is_birthday_today=Case(When(
            born_month=today.month, born_day=today.day, then=Value(True)),

            default=Value(False),
            output_field=BooleanField())
    ).annotate(
        next_birthday=Cast(
            Concat('birth_year', Value('-'), 'born_month', Value('-'),
                   'born_day'),
            DateField()
        )
    ).distinct()
    return qs.order_by('next_birthday')


def upcoming_anniversaries(qs, start_date=None, **kwargs):
    """same as upcoming_birthdays"""

    today = start_date or timezone.now()
    next_year = today.year + 1

    qs = qs.filter(detail__joined_date__lt=today, **kwargs).annotate(
        join_month=ExtractMonth('detail__joined_date')).annotate(
        join_day=Case(When(join_month=2, detail__joined_date__day=29, then=28),
                      default=ExtractDay('detail__joined_date'),
                      output_field=IntegerField())
    ).filter(
        join_day__gte=Case(When(
            join_month=today.month, then=today.day), default=0)
    ).annotate(
        join_year=Case(
            When(join_month__lt=today.month, then=next_year),
            When(join_month=today.month, join_day__lt=today.day,
                 then=next_year),
            default=today.year, output_field=IntegerField()),

        is_anniversary_today=Case(When(
            join_month=today.month, join_day=today.day, then=Value(True)),

            default=Value(False),
            output_field=BooleanField())
    ).annotate(
        next_anniversary=Cast(
            Concat('join_year', Value('-'), 'join_month', Value('-'),
                   'join_day'),
            DateField())
    ).distinct()
    return qs.order_by('next_anniversary')


def validate_experience_conflicts(
    user, start_date, end_date, instance,
    check_start_conflicts=True,
    check_end_conflicts=True,
    check_active_conflicts=True,
    is_current=True
):
    if not user:
        return
    #  TODO @Ravi: doing user.user_experiences.include_upcoming() spits all data, not just
    # current user, find why
    qs = UserExperience.objects.include_upcoming().filter(user=user)
    if instance:
        qs = qs.exclude(
            pk=instance.pk
        )
    start_date_conflicts = qs.filter(
        is_current=False,
        start_date__lte=start_date,
        end_date__gte=start_date,
        end_date__isnull=False
    ).exists()  # Experience is between a past experience.
    end_date_conflicts = False
    conflict_with_active = False
    if end_date:
        end_date_conflicts = qs.filter(
            is_current=False,
            start_date__lte=end_date,
            end_date__gte=end_date,
            end_date__isnull=False
        ).exists()
        if not is_current:
            conflict_with_active = qs.filter(
                start_date__lte=end_date,
                is_current=True
            )
    if check_start_conflicts and start_date_conflicts:
        raise ValidationError({
            'start_date':
                f'This user already has an experience beyond {start_date}'
        })
    if check_end_conflicts and end_date_conflicts:
        raise ValidationError({
            'end_date':
                f'This user\'s has an experience before {end_date}'
        })
    if check_active_conflicts and conflict_with_active:
        raise ValidationError({
            'end_date':
                'The user\'s active experience conflicts with this experience. '
        })


def get_my_change_request_frontend_url():
    return "/user/profile/change-request"


def template_mapper_per_instance(type_):
    mapper = {
        OFFER_LETTER: {
            'full_name': 'full_name',
            'date_of_join_AD': 'date_of_join',
            'date_of_join_BS': ad2bs,
            'employment_level': 'employment_level.title',
            'employment_status': 'employment_status.title',
            'job_title': 'job_title',
            'step': 'step',
            'division': 'division',
            'payroll': 'payroll',
            'company_name': 'organization',
            'company_address': 'organization.abstract_address',
            'branch': 'branch',
            'deadline': 'deadline',
            'address': 'address',
            'gender': 'gender',
            'email': 'email',
            'contract_period': 'contract_period',
        },
        CHANGE_TYPE: {
            'name': 'employee.full_name',
            'nationality': 'employee.detail.nationality',
            'change_type': 'change_type.title',
            'effective_from': 'detail.new_experience.start_date',
            'job_title': 'detail.new_experience.job_title',
            'division': 'detail.new_experience.division',
            'employment_level': 'detail.new_experience.employee_level.title',
            'employment_status':
                'detail.new_experience.employment_status.title',
            'pan_number': 'employee.legal_info.pan_number',
            'cit_number': 'employee.legal_info.cit_number',
            'pf_number': 'employee.legal_info.pf_number',
            'citizenship_number': 'employee.legal_info.citizenship_number',
            'passport_number': 'employee.legal_info.passport_number',
            'branch': 'detail.new_experience.branch',
            'step': 'detail.new_experience.current_step',
            'payroll': 'detail.new_payroll',
            'dob': 'employee.detail.date_of_birth',
            'date_of_join_AD': 'employee.detail.joined_date',
            'date_of_join_BS': ad2bs,
            'company_name': 'employee.detail.organization',
            'company_address': 'employee.detail.organization.abstract_address'
        },
        ONBOARDING: {
            'name': 'employee.full_name',
            'nationality': 'employee.detail.nationality',
            'dob': 'employee.detail.date_of_birth',
            'change_type': 'employee.oldest_experience.change_type',
            'effective_from': 'employee.oldest_experience.start_date',
            'job_title': 'employee.oldest_experience.job_title',
            'division': 'employee.oldest_experience.division',
            'branch': 'employee.oldest_experience.branch',
            'employment_level':
                'employee.oldest_experience.employee_level.title',
            'employment_status':
                'employee.oldest_experience.employment_status.title',
            'step': 'employee.oldest_experience.current_step',
            'pan_number': 'employee.legal_info.pan_number',
            'cit_number': 'employee.legal_info.cit_number',
            'pf_number': 'employee.legal_info.pf_number',
            'citizenship_number': 'employee.legal_info.citizenship_number',
            'passport_number': 'employee.legal_info.passport_number',
            'payroll':
                'detail.new_payroll',
            'date_of_join_AD': 'employee.detail.joined_date',
            'date_of_join_BS': ad2bs,
            'company_name': 'organization',
            'company_address': 'organization.abstract_address'
        },
        OFFBOARDING: {
            'name': 'employee.full_name',
            'nationality': 'employee.detail.nationality',
            'change_type': 'employee.latest_experience.change_type',
            'effective_from': 'employee.latest_experience.start_date',
            'job_title': 'employee.latest_experience.job_title',
            'division': 'employee.latest_experience.division',
            'branch': 'employee.latest_experience.branch',
            'company_name': 'employee.detail.organization',
            'company_address': 'employee.detail.organization.abstract_address',
            'employment_status':
                'employee.latest_experience.employment_status.title',
            'employment_level':
                'employee.latest_experience.employee_level.title',
            'pan_number': 'employee.legal_info.pan_number',
            'cit_number': 'employee.legal_info.cit_number',
            'pf_number': 'employee.legal_info.pf_number',
            'citizenship_number': 'employee.legal_info.citizenship_number',
            'passport_number': 'employee.legal_info.passport_number',
            'approved_date': 'effective_date',
            'separation_type': 'separation_type',
            'resign_date': 'parted_date',
            'last_working_date': 'release_date',
            'dob': 'employee.detail.date_of_birth',
            'step': 'employee.latest_experience.current_step',
            'payroll':
                'detail.old_payroll',
            'date_of_join_AD': 'employee.detail.joined_date',
            'date_of_join_BS': ad2bs
        }
    }
    return mapper.get(type_)


def generate_offer_letter(instance, template_letter, uri=None,
                          generated_instance=None):
    message = template_letter.message
    pattern_map = template_mapper_per_instance(template_letter.type)
    patterns = re.compile('\{\{[\w_ ]+\}\}').findall(message)
    for pattern in patterns:
        attr = pattern[2:-2].strip()

        attribute = pattern_map.get(attr)
        if attr == 'payroll':
            from irhrs.payroll.utils.virtual_user_payroll import (
                generate_payroll_section_for_letter_template
            )
            payroll_breakdown = generate_payroll_section_for_letter_template(
                instance
            )
            message = message.replace(
                pattern,
                payroll_breakdown
            )
        if attribute:
            if attr == 'date_of_join_BS':
                tx = string_from_tuple(
                    attribute(
                        nested_getattr(
                            instance,
                            pattern_map.get('date_of_join_AD')
                        ).strftime('%Y-%m-%d')
                    )  # attribute returns callable function ad2bs(str)
                )
            else:
                tx = nested_getattr(instance, attribute) or ''
            if attr == 'deadline':
                tx = format_timezone(tx)
            message = message.replace(
                pattern,
                str(tx)
            )
    if uri:
        seid = fernet.encrypt(
            format_timezone(
                generated_instance.created_at.replace(microsecond=0)
            ).encode()
        ).decode()
        query = f'/?seid={seid}'
        comp = re.compile('\{\{[ ]*url[ ]*\}\}')
        uri = settings.FRONTEND_URL + '/offer-letter/' + uri + query
        text = (
            '<style>'
            '#notification_url {'
            '    margin: 10px;'
            '    word-break: break-all;'
            '}'
            '</style>'
            '<div id="notification_url">'
            f'Please follow the <a href={uri}> url </a>. '
            f'If the link does not work copy paste this URL: <br> {uri}</div>'
        )
        for pattern in comp.findall(message):
            message = message.replace(pattern, text)
        if uri not in message:
            message = message + r'<br\>' + text
    message = re.sub('\n{2,}', '\n', message)
    return message


def choice_field_display(instance, attribute):
    display = getattr(instance, f'get_{attribute}_display')
    return {
        'value': getattr(instance, attribute),
        'display': display()
    }


def create_task_from_templates(instance):
    task_template = instance.task_template
    template_maps = [
        TaskTemplateMapping(
            template_detail=template_detail
        )
        for template_detail in task_template.templates.all()
    ]
    unassigned_maps = TaskTemplateMapping.objects.bulk_create(template_maps)
    instance.tasks.add(*unassigned_maps)


def create_letter_from_template(letter_template, validated_data):
    pre_employment = validated_data.get('pre_employment')
    employment_review = validated_data.get('employment_review')
    separation = validated_data.get('separation')

    items = [pre_employment, employment_review, separation]
    obj = next(item for item in items if item is not None)
    return generate_offer_letter(obj, letter_template)


def apply_experience_changes(employee, old_experience, new_experience):
    if not new_experience:
        return
    if old_experience:
        old_experience.end_date = new_experience.start_date - timezone.timedelta(
            days=1
        )
        old_experience.is_current = False
        old_experience.save(update_fields=['end_date', 'is_current'])

    new_experience.is_current = True
    new_experience.upcoming = False
    new_experience.save(update_fields=['is_current', 'upcoming'])

    # TODO: @Ravi notify_user is not defined
    # notify_user(
    #     employee,
    #     f"Your experience has been updated by {get_system_admin().full_name} "
    # )


def apply_payroll_changes(change_type_detail):
    from irhrs.payroll.api.v1.serializers import UserExperiencePackageSlotCreateAndUpdateSerializer
    new_experience = change_type_detail.new_experience
    old_experience = change_type_detail.old_experience
    organization = old_experience.organization
    new_payroll = change_type_detail.new_payroll
    data = {
        "user_experience": new_experience.id,
        "package": new_payroll.id if new_payroll else None,
        "active_from_date": new_experience.start_date
    }
    package_slot = UserExperiencePackageSlotCreateAndUpdateSerializer(data=data)
    if package_slot.is_valid():
        package_slot.save()
    else:
        failed_assign_notification_permissions = (
            HRIS_EMPLOYMENT_REVIEW_PERMISSION,
            HRIS_EMPLOYMENT_REVIEW_PROCESS_PERMISSION
        )
        notify_organization(
            text=f"Payroll package assign failed for user {old_experience.user.full_name}"
            f" during employment review.",
            action=new_experience,
            organization=old_experience.organization,
            permissions=failed_assign_notification_permissions,
            url=f'/admin/{organization.slug}/hris/employees/'
            f'employment-review/review-details?id={change_type_detail.id}'
        )


def apply_work_shift_changes(employee, old_work_shift, new_work_shift):
    if old_work_shift == new_work_shift or not new_work_shift:
        return
    today = get_today()
    tomorrow = get_tomorrow()
    att_setting = employee.attendance_setting
    att_setting.individual_setting_shift.filter(
        applicable_to__isnull=True
    ).update(
        applicable_to=today
    )
    att_setting.individual_setting_shift.create(
        shift=new_work_shift,
        applicable_from=tomorrow
    )


def apply_leave_balance_changes(detail):
    leave_changes = LeaveChangeType.objects.filter(
        change_type=detail,
        update_balance__isnull=False
    ).annotate(
        substitute_balance=Coalesce(  # substitute balance is addition or
            # reduction balance
            F('update_balance'), 0
        ) - Coalesce(
            F('balance'), 0
        )
    )
    for leave_change in leave_changes:
        balance_to_add = leave_change.substitute_balance
        if balance_to_add == 0:
            continue  # its pointless
        change_occurred = detail.change_type.title
        leave_account = leave_change.leave_account
        previous_balance = leave_account.balance
        previous_usable_balance = leave_account.usable_balance
        difference = leave_account.balance - leave_account.usable_balance
        leave_account.balance = leave_account.balance + balance_to_add
        max_bal = nested_getattr(leave_account, 'rule.max_balance')

        if max_bal and leave_account.balance > max_bal:
            leave_account.balance = leave_account.rule.max_balance

        leave_account.usable_balance = leave_account.balance - difference

        leave_account.last_accrued = timezone.now()
        action = ADDED if balance_to_add > 0 else DEDUCTED
        leave_account.save(update_fields=['balance', 'usable_balance'])
        LeaveAccountHistory.objects.create(
            account=leave_account,
            user=leave_account.user,
            actor=get_system_admin(),
            action=action,
            previous_balance=previous_balance,
            previous_usable_balance=previous_usable_balance,
            new_balance=leave_account.balance,
            new_usable_balance=leave_account.usable_balance,
            remarks=f'Added by the System under {change_occurred} rule'
        )


@transaction.atomic()
def apply_change_type():
    """
    Applies change type when the date is matched.
    i.e. Promotes user, updates balance, updates payroll and all.
    :return:
    """
    from irhrs.users.api.v1.serializers.experience import \
        UserExperienceSerializer

    completed_reviews = EmploymentReview.objects.exclude(
        status__in=[HOLD, STOPPED]
    ).filter(
        status=COMPLETED,
        detail__new_experience__start_date__lte=get_today()
    ).exclude(
        detail__new_experience__upcoming=False
    )
    reviews = list()
    for completed_review in completed_reviews:
        # the above filter should not include reviews whose status is not
        # completed
        detail = completed_review.detail
        change_type = detail.change_type
        employee = detail.old_experience.user
        if change_type.affects_experience:
            apply_experience_changes(
                employee, detail.old_experience, detail.new_experience
            )
            UserExperienceSerializer.update_experience_is_current(
                instance=detail.new_experience,
                user=employee
            )
        if change_type.affects_payroll:
            change_type_detail = completed_review.detail
            apply_payroll_changes(change_type_detail)
        if change_type.affects_work_shift:
            apply_work_shift_changes(
                employee, detail.old_work_shift, detail.new_work_shift
            )
        if change_type.affects_leave_balance:
            apply_leave_balance_changes(detail)
        completed_review.committed = True
        reviews.append(completed_review)
        add_notification(
            text=f"Your employment experience has been updated.",
            actor=get_system_admin(),
            action=completed_review,
            recipient=employee,
            url=f"/user/profile/{employee.id}/?tab=experience"
        )
    return reviews


def terminate_recurring_task(user, released_date):
    tasks = RecurringTaskDate.objects.filter(
            template__deleted_at__isnull=True,
            template__created_by=user,
            template__recurring_rule__isnull=False,
            recurring_at__gte=released_date
        )
    tasks.delete()


def remove_user_from_admin(user):
    user_in_organization_admin = UserOrganization.objects.filter(user=user)
    user_in_organization_admin.delete()
    user.groups.clear()
    clear_permission_cache()


def annotate_proportionate_carry_forward_used_edited_on_leave_accounts(
    queryset: QuerySet,  # LeaveAccountQueryset
    fiscal: FiscalYear,
    separation: EmployeeSeparation
) -> QuerySet:
    days_in_that_year = (fiscal.end_at - fiscal.start_at).days + 1

    effective_from = max(fiscal.start_at, separation.employee.detail.joined_date)
    effective_till = separation.release_date if separation.release_date else get_today()
    effective_days = (effective_till - effective_from).days + 1
    experience_qs = UserExperience.objects.filter(user=OuterRef('user__id')).values(
        'probation_end_date')[:1]
    return queryset.annotate(
        encashment_edit=FilteredRelation(
            relation_name='encashment_edits_on_separation',
            condition=Q(encashment_edits_on_separation__separation=separation)
        ),
        prob_setting=F('rule__proportionate_on_probation_end_date'),
        prob_end_date=Subquery(experience_qs),
        leave_starts_from=Case(
            When(prob_setting=True, then=Coalesce(F'prob_end_date',
                                                  F'user__detail__joined_date')),
            output_field=DateField()),
        leave_effective_from=Case(When(leave_starts_from__isnull=False,
                                       then=Greatest(F'leave_starts_from', fiscal.start_at)),
                                  output_field=DateField()),
        prob_proportinate_effective_days=ExpressionWrapper(
            ExtractDay(effective_till-F('leave_effective_from')) + 1,
            output_field=IntegerField()
        )
    ).annotate(
        proportionate=Case(
            When(
                rule__renewal_rule__isnull=True,
                then=F('usable_balance')
            ),
            When(
                Q(prob_proportinate_effective_days__isnull=False,
                  leave_effective_from__isnull=False),
                then=F(
                    'rule__renewal_rule__initial_balance'
                ) / days_in_that_year * F('prob_proportinate_effective_days')
            ),
            default=F(
                'rule__renewal_rule__initial_balance'
            ) / days_in_that_year * effective_days
        ),
        carry_forward=Coalesce(Subquery(
            LeaveAccountHistory.objects.filter(
                carry_forward__isnull=False,
                created_at__date__gte=fiscal.start_at,
                account=OuterRef('pk')
            ).values('carry_forward')[:1]
        ), 0.0),
        used_balance=Coalesce(
            Case(
                When(
                    rule__leave_type__category__in=HOURLY_LEAVES,
                    then=Subquery(
                        LeaveSheet.objects.filter(
                            request__leave_account=OuterRef('pk'),
                            request__is_deleted=False,
                            request__status=APPROVED,
                            leave_for__gte=fiscal.start_at
                        ).annotate(minutes=ExpressionWrapper(
                            Extract(
                                ExpressionWrapper(
                                    F('end') - F('start'), output_field=DurationField()
                                ), 'epoch') / 60,
                            output_field=IntegerField()
                        )).order_by().values('request__leave_account').annotate(
                            total_minutes=Sum('minutes')).values('total_minutes')[:1]
                    )

                ),
                default=Sum(
                    'leave_requests__sheets__balance',
                    filter=Q(
                        leave_requests__is_deleted=False,
                        leave_requests__status=APPROVED,
                        leave_requests__sheets__leave_for__gte=fiscal.start_at
                    )
                ), output_field=IntegerField()
            ), 0
        ),
        edited_encashment=F('encashment_edit__encashment_balance')
    )


def encash_leave_on_separation(separation):
    employee = separation.employee
    fiscal = get_fiscal_year_for_leave(employee.detail.organization)
    if not fiscal:
        return

    accounts = annotate_proportionate_carry_forward_used_edited_on_leave_accounts(
        employee.leave_accounts.filter(
            rule__leave_type__master_setting=get_active_master_setting(
                employee.detail.organization
            ),
            is_archived=False,
            rule__is_paid=True
        ),
        fiscal,
        separation
    )

    for account in accounts:
        if account.edited_encashment:
            encash_balance = account.edited_encashment
        else:
            if hasattr(account.rule, 'renewal_rule'):
                encash_balance = account.proportionate + account.carry_forward - \
                                 account.used_balance
            else:
                encash_balance = account.usable_balance
            encash_balance = round(encash_balance, 2)
            encashment_edit = LeaveEncashmentOnSeparation.objects.create(
                separation=separation,
                leave_account=account,
                encashment_balance=encash_balance
            )
            encashment_edit.history.create(
                actor=get_system_admin(),
                previous_balance=encash_balance,
                new_balance=encash_balance,
                remarks="Recorded while applying off-boarding"
            )

        # encash_balance > 0
        if encash_balance:
            encashment = LeaveEncashment.objects.create(
                user=employee,
                account=account,
                status=GENERATED,
                balance=round(encash_balance, 2),
                source=EMPLOYEE_SEPARATION
            )
            encashment.history.create(
                actor=get_system_admin(),
                action=GENERATED,
                new_balance=round(encash_balance, 2),
                remarks="encashed during employee separation"
            )


@transaction.atomic()
def apply_separation():
    """
    Applies Separation when off boarding is completed.
    * Deactivates user -> disabling login & visibility from the system
    * Archives Leave Accounts -> disabling leave accruals.
    """
    completed_reviews = EmployeeSeparation.objects.exclude(
        status__in=[HOLD, STOPPED]
    ).filter(
        employee__is_active=True,
        release_date__lt=get_today()
    )
    terminated_users = list()
    for completed_review in completed_reviews:
        employee = completed_review.employee

        encash_leave_on_separation(completed_review)

        employee.leave_accounts.update(
            is_archived=True
        )
        employee.is_active = False
        employee.is_blocked = True
        employee.save()
        employee.detail.resigned_date = completed_review.parted_date
        employee.detail.last_working_date = completed_review.release_date
        employee.detail.parting_reason = completed_review.separation_type.category
        employee.detail.save()
        employee.user_experiences.update(is_current=False)
        terminated_users.append(employee)
        terminate_recurring_task(employee, completed_review.release_date)
        remove_user_from_admin(employee)
    return terminated_users


def a_month_before():
    return get_today() - timezone.timedelta(days=30)


def recently_joined(experience):
    thirty_days_in_past = a_month_before()
    today = get_today()

    # if the user's experience is before 30 days, not new.
    dt = experience.user.detail.joined_date
    return (
        UPCOMING if dt > today else NEW if dt >= thirty_days_in_past
        else False
    )


def employment_reviewed(experience, source=None):
    review = EmploymentReview.objects.filter(
        detail__new_experience=experience
    ).first()
    if review and experience.start_date > a_month_before(
    ) and review.change_type.badge_visibility in [BOTH, source]:
        return review.change_type.title
    return False


def employee_resigning(experience, source=None):
    separation = EmployeeSeparation.objects.filter(
        employee=experience.user,
        release_date__gte=get_today()
    ).first()
    if (
        separation
        and separation.separation_type.badge_visibility in [BOTH, source]
    ):
        return separation.separation_type.title
    return False


def generate_user_tag(instance, source):
    from django.core.cache import cache
    if source == EMPLOYEE_DIRECTORY:
        experience = instance.current_experience
        if not experience:
            return {
                'onboarding': False,
                'employment_review': False,
                'offboarding': False
            }
    else:
        experience = instance
    cache_key = f'experience_tag__{experience.id}'
    cache_value = cache.get(cache_key, None)
    # if cache_value:
    #     return cache_value
    tag_result = {
        'onboarding': recently_joined(experience),
        'employment_review': employment_reviewed(experience, source),
        'offboarding': employee_resigning(experience, source),
    }
    cache.set(cache_key, tag_result, timeout=timeout_for_midnight())
    return tag_result


def raise_if_hold(instance):
    current_status = instance.status
    if current_status in [HOLD, STOPPED]:
        raise ValidationError(
            f"Cannot perform this action because "
            f"{instance.__class__.__name__} is in "
            f"{instance.get_status_display().lower()} state"
        )


def validate_no_off_boarding_in_progress(employee):
    if EmployeeSeparation.objects.exclude(
        # List innocuous status here.
        status__in=(
            STOPPED, COMPLETED, POST_TASK_COMPLETED,
        )
    ).filter(
        employee=employee
    ).exists():
        raise ValidationError(
            f"Off-boarding process for this user is ongoing."
        )


def validate_no_employment_review_in_progress(employee):
    if EmploymentReview.objects.exclude(
        status__in=(
            STOPPED, COMPLETED, POST_TASK_COMPLETED,
        )
    ).filter(
        employee=employee
    ).exists():
        raise ValidationError(
            f"Employment Review for this user is ongoing."
        )


def get_doj_from_user_bs(user):
    return "-".join(
        map(
            lambda dt: str(dt).rjust(2, '0'),
            ad2bs(user.detail.joined_date)
        )
    )


def generate_custom_letter_message(letter_template, user):
    mapping = {
        'full_name': 'full_name',
        'date_of_join_AD': 'detail.joined_date',
        'date_of_join_BS': get_doj_from_user_bs,
        'employment_level': 'detail.employment_level.title',
        'employment_status': 'detail.employment_status.title',
        'job_title': 'detail.job_title.title',
        'step': 'current_experience.current_step',
        'division': 'detail.division',
        'company_name': 'detail.organization',
        'company_address': 'detail.organization.address.address',
        'branch': 'detail.branch.name',
        'address': 'current_address',
        'gender': 'detail.gender',
        'experience_end_date': 'current_experience.end_date',
        'nationality': 'detail.nationality',
        'change_type': 'current_experience.change_type',
        'pan_number': 'legal_info.pan_number',
        'cit_number': 'legal_info.cit_number',
        'pf_number': 'legal_info.pf_number',
        'citizenship_number': 'legal_info.citizenship_number',
        'passport_number': 'legal_info.passport_number',
        'ssfid': 'legal_info.ssfid',
        'dob': 'detail.date_of_birth',
        'resign_date': 'detail.resigned_date',
        'last_working_date': 'detail.last_working_date',
    }
    message = letter_template.message
    patterns = re.compile('\{\{[\w_ ]+\}\}').findall(message)
    for pattern in patterns:
        attr = pattern[2:-2].strip()
        value = mapping.get(attr)
        if callable(value):
            message = message.replace(
                pattern,
                str(value(user))
            )
        else:
            val = nested_getattr(user, value)
            if not val:
                continue
            message = message.replace(
                pattern,
                str(nested_getattr(user, value))
            )
    return message


def update_user_profile_completeness(user):
    if isinstance(user, UserDetail):
        user_detail = user
    else:
        user_detail = UserDetail.objects.filter(user=user).first()
    total = profile_completeness(user)

    if user_detail:
        user = user_detail.user
        user_detail.completeness_percent = total
        user_detail.save()
    return total

def filter_duty_station_assignment(qs, fiscal_year):
    return qs.filter(
        (
            Q(to_date__isnull=True) &
            Q(
                Q(from_date__lte=fiscal_year.start_at) |
                Q(from_date__range=(fiscal_year.start_at, fiscal_year.end_at))
            )
        )
        |
        (
            Q(to_date__isnull=False) &
            Q(
                Q(
                    Q(from_date__range=(fiscal_year.start_at, fiscal_year.end_at)) |
                    Q(to_date__range=(fiscal_year.start_at, fiscal_year.end_at)),
                )
                |
                Q(from_date__lte=fiscal_year.start_at, to_date__gte=fiscal_year.end_at)
            )
        )
    ).distinct()
