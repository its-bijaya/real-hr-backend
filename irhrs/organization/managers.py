from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import Manager
from django.utils import timezone

from irhrs.core.constants.organization import GLOBAL
from irhrs.core.utils.common import get_today


class FiscalYearManager(Manager):
    def _base(self, organization, date=None, category=GLOBAL):
        if not date:
            date = get_today()
        try:
            return self.get_queryset().get(
                organization=organization,
                applicable_from__lte=date,
                applicable_to__gte=date,
                category=category
            )
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            return None

    def current(self, organization, category=GLOBAL):
        return self._base(
            organization=organization,
            category=category
        )

    def active_for_date(self, organization, date_=None, category=GLOBAL):
        return self._base(
            organization=organization,
            date=date_,
            category=category
        )

    def all_fiscals(self, organization, category=GLOBAL):
        return self.get_queryset().filter(
            organization=organization,
            category=category
        ).order_by('applicable_from')

    def for_category_exists(self, organization, date=None, category=GLOBAL):
        if not date:
            date = get_today()
        return self.get_queryset().filter(
            organization=organization,
            category=category,
            applicable_from__lte=date,
            applicable_to__gte=date,
        ).exists()


class NotificationTemplateMapManager(Manager):
    def active(self):
        return self.get_queryset().filter(
            is_active=True
        )
