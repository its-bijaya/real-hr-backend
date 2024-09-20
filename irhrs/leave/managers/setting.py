import datetime

from django.db.models import Manager, Exists, OuterRef, Q, QuerySet

from irhrs.core.utils import common
from irhrs.leave.constants.model_constants import IDLE, ACTIVE, EXPIRED
from irhrs.leave.models.rule import LeaveRule


class MasterSettingQuerySet(QuerySet):
    @staticmethod
    def get_has_rule():
        return Exists(
            LeaveRule.objects.filter(
                leave_type__master_setting=OuterRef('id'),
            )
        )

    def idle(self):
        today = common.get_today()
        return self.exclude(
            # exclude expired
            effective_till__isnull=False,
            effective_till__lt=today
        ).annotate(
            has_rules=self.get_has_rule()
        ).filter(
            Q(effective_from__isnull=True) |
            Q(effective_from__gt=today) |
            Q(has_rules=False)
        )

    def active(self):
        today = common.get_today()
        return self.exclude(
            Q(
                # exclude expired
                effective_till__isnull=False,
                effective_till__lt=today
            ) | Q(
                # or not effective yet
                effective_from__gt=today,
            ) | Q(
                effective_from__isnull=True,
            )
        ).annotate(
            has_rules=self.get_has_rule()
        ).filter(
            has_rules=True
        )

    def expired(self):
        today = common.get_today()
        return self.filter(
            # exclude expired
            effective_till__isnull=False,
            effective_till__lt=today
        )

    def active_for_date(self, active_date):
        return self.exclude(
            Q(
                # exclude expired
                effective_till__isnull=False,
                effective_till__lt=active_date
            ) | Q(
                # or not effective yet
                effective_from__gt=active_date,
            )
        ).annotate(
            has_rules=self.get_has_rule()
        ).filter(
            has_rules=True
        )

    def get_between(self, start: datetime.date, end: datetime.date):
        # 1. ms was active, before FY started, and ms is still active.
        case1 = Q(
            effective_from__lte=start, effective_till__isnull=True
        )
        # 2. ms was active, before FY started; but, ms ended before FY did.
        case2 = Q(
            effective_from__lte=start, effective_till__lte=end,
            # dont want the dead and decayed to be listed
            effective_till__gte=start
        )
        # 3. FY was active, ms started, ms running; FY running
        case3 = Q(
            effective_from__gte=start, effective_till__isnull=True,
            # dont want futures ones to be listed
            effective_from__lte=end,
        )
        # 4. FY was active, ms started, FY ended, ms is still running
        case4 = Q(
            effective_from__gte=start, effective_till__gte=end
        )

        # 5. FY was active, ms started, ms ended, FY is still running
        case5 = Q(
            effective_from__gte=start, effective_till__lte=end
        )

        return self.filter(
            case1 | case2 | case3 | case4 | case5
        ).annotate(
            has_rules=self.get_has_rule()
        ).filter(
            has_rules=True
        )

    def active_between(self, start: datetime.date, end: datetime.date):
        # |----MS1--------------|---MS2--|-----MS3-------------------------|--MS4------>
        # <---------FY1-----------|--------------FY2------------------|------FY4------->

        # 1. ms was active, before FY started, and ms is still active.
        case1 = Q(
            effective_from__lte=start, effective_till__isnull=True
        )
        # 2. ms was active, before FY started; but, ms ended before FY did.
        case2 = Q(
            effective_from__lte=start, effective_till__lte=end,
            # dont want the dead and decayed to be listed
            effective_till__gte=start
        )
        # 3. FY was active, ms started, ms running; FY running
        case3 = Q(
            effective_from__gte=start, effective_till__isnull=True,
            # dont want futures ones to be listed
            effective_from__lte=end,
        )
        # 4. FY was active, ms started, FY ended, ms is still running
        case4 = Q(
            effective_from__gte=start, effective_till__gte=end
        )

        return self.filter(
            case1 | case2 | case3 | case4
        ).annotate(
            has_rules=self.get_has_rule()
        ).filter(
            has_rules=True
        )

    def status_filter(self, status):
        filter_map = {IDLE: 'idle', ACTIVE: 'active', EXPIRED: 'expired'}
        attr = filter_map.get(status)
        return getattr(self, attr)() if attr else self.none()


class MasterSettingManager(Manager):
    def get_queryset(self):
        return MasterSettingQuerySet(self.model, using=self._db)


class LeaveRequestManager(Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(
            is_deleted=True
        )

    def include_deleted(self):
        return super().get_queryset()
