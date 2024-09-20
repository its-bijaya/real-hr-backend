from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.db.models import Manager, QuerySet, Q, When, F, Case, DateField, FilteredRelation
from django.utils.functional import cached_property

from rest_framework.exceptions import ValidationError

from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_today, get_yesterday, get_tomorrow


class UserQueryset(QuerySet):
    def current(self):
        return self.last_experience_annotate().filter(
            is_active=True,
            is_blocked=False
        ).filter(
            __end_date__gte=get_today()
        ).distinct()

    def past(self):
        return self.last_experience_annotate().filter(
            Q(__end_date__lt=get_today())
        ).distinct()

    def exclude_admin(self):
        return self.exclude(**self._excludes)

    def select_essentials(self):
        return self.select_related(
            'detail',
            'detail__employment_level',
            'detail__job_title',
            'detail__organization',
            'detail__division',
        )

    @cached_property
    def _excludes(self):
        system_admin = get_system_admin()
        if system_admin:
            return {'id': system_admin.pk}
        return {}

    def last_experience_annotate(self):
        return self.annotate(
            current_experiences=FilteredRelation(
                'user_experiences',
                condition=Q(user_experiences__is_current=True)
            )
        ).annotate(
            __end_date=Case(
                When(
                    # DON'T REMOVE THIS LINE,
                    # current_experiences__end_date__isnull is true for current_experiences__isnull
                    current_experiences__is_current=True,
                    current_experiences__end_date__isnull=False,
                    then=F('current_experiences__end_date')
                ),
                When(
                    # DON'T REMOVE THIS LINE,
                    # current_experiences__end_date__isnull is true for current_experiences__isnull
                    current_experiences__is_current=True,
                    current_experiences__end_date__isnull=True,
                    then=get_tomorrow()
                ),
                default=get_yesterday(),
                output_field=DateField(null=True)
            )
        )

    # @cached_property
    # def active_user_list(self):
    #     from irhrs.users.models import UserExperience
    #     return set(
    #         UserExperience.objects.filter(
    #             is_current=True
    #         ).filter(
    #             Q(end_date__gte=get_today()) |
    #             Q(end_date__isnull=True)
    #         ).values_list('user_id', flat=True)
    #     )


class UserManager(BaseUserManager):

    def create_user(self, email, password, **extra_fields):

        realhr_bot_email = getattr(
            settings, 'SYSTEM_BOT_EMAIL', 'irealhrbot@irealhrsoft.com'
        )
        if (
            settings.MAX_USERS_COUNT and
            email != realhr_bot_email and
            self.get_queryset().exclude(
                email=realhr_bot_email
            ).filter(is_active=True).count() >= settings.MAX_USERS_COUNT
        ):
            raise ValidationError(
                f"Active user count cannot exceed {settings.MAX_USERS_COUNT}"
            )

        extra_fields.setdefault('is_superuser', False)
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, first_name, middle_name, last_name):
        user = self.create_user(
            email=email,
            password=password,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
        )
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, _email):
        return self.get(email=_email)

    def get_queryset(self):
        return UserQueryset(self.model, using=self._db)

    def exclude_admin(self):
        return self.exclude(**self._excludes)

    @cached_property
    def _excludes(self):
        system_admin = get_system_admin()
        if system_admin:
            return {'pk': system_admin.pk}
        return {}


class UserDetailQueryset(QuerySet):
    def current(self):
        return self.exclude_admin().filter(user__user_experiences__is_current=True)

    def past(self):
        return self.exclude_admin().filter(~Q(user__user_experiences__is_current=True))

    def exclude_admin(self):
        return self.exclude(**self._excludes)

    @cached_property
    def _excludes(self):
        system_admin = get_system_admin()
        if system_admin:
            return {'user_id': system_admin.pk}
        return {}


class UserDetailManager(Manager):
    def get_queryset(self):
        return UserDetailQueryset(self.model, using=self._db)


class UserExperienceManager(Manager):
    def get_queryset(self):
        return QuerySet(self.model, using=self._db).filter(
            upcoming=False
        )

    def include_upcoming(self):
        return QuerySet(self.model, using=self._db)


class ChangeRequestManager(Manager):
    def get_queryset(self):
        return QuerySet(self.model, using=self._db).filter(
            user__is_active=True
        )
