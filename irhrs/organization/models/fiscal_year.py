import functools

from datetime import datetime
from datetime import timedelta

from django.db import models
from django.utils.functional import cached_property
from django.core.validators import MinValueValidator

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.constants.organization import FISCAL_YEAR_CATEGORY, GLOBAL
from irhrs.core.utils.common import get_today
from irhrs.core.utils.datework import AbstractDatework
from irhrs.organization.managers import FiscalYearManager


class DummyFiscalYear:
    name = 'Dummy'
    applicable_from = None
    applicable_to = None

    def __init__(self, **kwargs) -> None:
        super().__init__()
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def next(self):
        return self.__class__()

    @property
    def previous(self):
        return self.__class__()


class FiscalYear(BaseModel, SlugModel):
    organization = models.ForeignKey(
        to='organization.Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=100,
                            help_text='Name for the Fiscal Year')

    start_at = models.DateField(help_text='Start Date')
    end_at = models.DateField(help_text='End Date')
    description = models.TextField(
        help_text='Description about the Fiscal year')

    applicable_from = models.DateField(
        help_text='Fiscal Year settings to be applicable from')
    applicable_to = models.DateField(
        help_text='Fiscal Year settings to be applicable Upto')
    category = models.CharField(
        max_length=32,
        choices=FISCAL_YEAR_CATEGORY,
        default=GLOBAL
    )

    objects = FiscalYearManager()

    def __str__(self):
        return f"{self.name} starts at {self.start_at} and ends at {self.end_at} "

    @property
    def days_since_start(self):
        td = get_today() - self.start_at
        return td.days if td > timedelta(0) else 0

    def get_fiscal_date(self, english_date):
        mm = self.fiscal_months.filter(
            start_at__lte=english_date,
            end_at__gte=english_date
        ).order_by(
            'start_at'
        ).first()
        if not mm:
            return english_date
        dd = (english_date - mm.start_at).days + 1
        return f'{self.name}-{mm.display_name}-{dd}'

    @cached_property
    def previous(self):
        prev = self._meta.model.objects.exclude(
            pk=self.pk
        ).filter(
            organization=self.organization,
            start_at__lte=self.start_at,
            category=self.category

        ).order_by(
            '-start_at'
        ).first()
        return prev if prev else DummyFiscalYear()

    @cached_property
    def next(self):
        next_ = self._meta.model.objects.exclude(
            pk=self.pk
        ).filter(
            organization=self.organization,
            end_at__gte=self.applicable_to
        ).order_by(
            'applicable_to'
        ).first()
        return next_ if next_ else DummyFiscalYear()

    @property
    def can_update_or_delete(self):
        return get_today() < self.applicable_from < self.applicable_to


class FiscalYearMonth(BaseModel):
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE,
                                    related_name='fiscal_months')
    month_index = models.IntegerField(
        help_text="Order of the month in fiscal year",
        validators=[MinValueValidator(1)]
    )
    display_name = models.CharField(max_length=20,
                                    help_text='Display name of the Month')
    start_at = models.DateField(help_text='start date of month')
    end_at = models.DateField(help_text='end date of month')

    class Meta:
        ordering = ('month_index',)

    def __str__(self):
        return f"{self.fiscal_year.name} > {self.month_index} > {self.display_name}"

    @property
    def all_dates(self):
        return []
        # _delta = self.end_at - self.start_at
        # return [self.start_at + timedelta(i) for i in range(_delta.days + 1)]

    @property
    def next(self):
        return self.fiscal_year.fiscal_months.filter(
            start_at__gte=self.end_at
        ).order_by('start_at').first()

    @property
    def prev(self):
        return self.fiscal_year.fiscal_months.filter(
            start_at__lte=self.start_at
        ).order_by('-start_at').first()


class FY(AbstractDatework):
    _organization = None

    def __init__(self, organization):
        self._organization = organization
        self.fiscal_obj = functools.lru_cache(self.fiscal_obj)
        self.get_fiscal_year_data_from_date_range = functools.lru_cache(
            self.get_fiscal_year_data_from_date_range)
        self.get_months_data_from_date_range = functools.lru_cache(
            self.get_months_data_from_date_range)

    def fiscal_obj(self, date=None):
        return FiscalYear.objects.active_for_date(
            organization=self._organization,
            date_=date
        )

    def fiscal_values(self, date=None):
        fy = self.fiscal_obj(date=date)
        if fy:
            from irhrs.organization.api.v1.serializers.fiscal_year import \
                FiscalYearSerializer
            _context = {'read_only_mode': True}
            return FiscalYearSerializer(instance=fy, context=_context).data
        return None

    def fiscal_objs(self):
        return FiscalYear.objects.all_fiscals(
            organization=self._organization
        )

    def get_months_data_from_date_range(self,
                                        employee_appoint_date,
                                        from_date,
                                        to_date):
        """
        Returns months slots from given date range.
        If employee_appoint_date is greater than from_date then
        from_date is is employee_appoint_date

        Args:
            employee_appoint_date (date): Employee appoint date
            from_date (date): From date
            to_date (date): To date

        Returns:
            list: [
                {
                    'start': <date: Slot start date>,
                    'end': <date: Slot end date>,
                    'month_days': <int: Total days in the month of slot>,
                    'days_count': <int: Total days in slot>
                },
                ...
            ]

        """
        if isinstance(employee_appoint_date, datetime):
            employee_appoint_date = employee_appoint_date.date()

        if isinstance(from_date, datetime):
            from_date = from_date.date()

        if isinstance(to_date, datetime):
            to_date = to_date.date()

        data = []
        if employee_appoint_date > from_date:
            from_date = employee_appoint_date
        # from irhrs.organization.models.fiscal_year import FY
        # org = Organization.objects.get(slug='aayulogic-pvt-ltd')
        # from datetime import datetime
        # from_date = datetime(year=2012, month=2, day=14).date()
        # to_date = datetime(year=2012, month=12, day=30).date()
        # f = FY(organization=org)
        f_data = self.get_fiscal_year_data_from_date_range(from_date, to_date)

        if not f_data:
            return data
        # main_start = f_data[0]['date_range'][0]
        # main_end = f_data[::-1][0]['date_range'][1]

        # fy_ids = [f['fy_obj_id'] for f in f_data]

        for individual_fiscal in f_data:
            _start_date, _end_date = individual_fiscal['date_range']
            _fy_object_id = individual_fiscal['fy_obj_id']

            _start_month_obj = FiscalYearMonth.objects.get(
                fiscal_year_id=_fy_object_id,
                start_at__lte=_start_date,
                end_at__gte=_start_date
            )

            _end_month_obj = FiscalYearMonth.objects.get(
                fiscal_year_id=_fy_object_id,
                start_at__lte=_end_date,
                end_at__gte=_end_date
            )

            _month_objects = FiscalYearMonth.objects.filter(
                fiscal_year_id=_fy_object_id,
                start_at__gte=_start_month_obj.start_at
            ).intersection(
                FiscalYearMonth.objects.filter(
                    fiscal_year_id=_fy_object_id,
                    end_at__lte=_end_month_obj.end_at
                )
            ).order_by('start_at')

            fy_obj = FiscalYear.objects.get(id=_fy_object_id)
            for individual_month in _month_objects:
                if individual_month.start_at >= fy_obj.applicable_from:
                    _month_start = individual_month.start_at
                else:
                    _month_start = fy_obj.applicable_from

                if individual_month.end_at <= fy_obj.applicable_to:
                    _month_end = individual_month.end_at
                else:
                    _month_end = fy_obj.applicable_to
                if from_date > _month_start:
                    _start = from_date
                else:
                    _start = _month_start

                if to_date < _month_end:
                    _end = to_date
                else:
                    _end = _month_end

                data.append(
                    {
                        'start': _start,
                        'end': _end,
                        'actual_start': _month_start,
                        'actual_end': _month_end,
                        'month_days': (_month_end - _month_start).days + 1,
                        'days_count': (_end - _start).days + 1,

                    },
                )

        return data

    def get_fiscal_year_data_from_date_range(self, from_date, to_date):
        """
        Returns list of fiscal year slots contained in from_date and to_date
        along  with date range included in particular fiscal year

        Args:
            from_date (date): From date
            to_date (date): To date

        Returns:
            list: [
                {
                    'fy_slot': <tuple: (<date: FY start date>, <date: FY end date>)>,
                    'date_range': <tuple: Tuple of date range containing is FY>,
                },
                ...
            ]

        """
        # from datetime import datetime
        # from_date = datetime(year=2012, month=2, day=14).date()
        # to_date = datetime(year=2012, month=12, day=30).date()

        # for start
        data = []
        if isinstance(from_date, datetime):
            from_date = from_date.date()

        if isinstance(to_date, datetime):
            to_date = to_date.date()
        start_year = FiscalYear.objects.active_for_date(
            organization=self._organization,
            date_=from_date
        )
        if not start_year:
            main_start = FiscalYear.objects.filter(
                organization=self._organization,
                category=GLOBAL
            ).order_by(
                'applicable_from').first()
            if from_date < main_start.applicable_from:
                start_year = main_start
                # also change the from_date
                from_date = start_year.applicable_from

        # end year
        end_year = FiscalYear.objects.active_for_date(
            organization=self._organization,
            date_=to_date
        )
        if not end_year:
            main_end = FiscalYear.objects.filter(
                organization=self._organization,
                category=GLOBAL
            ).order_by(
                'applicable_to').last()
            if to_date > main_end.applicable_to:
                end_year = main_end
                # also change the to_date
                to_date = main_end.applicable_to

        if not (start_year and end_year):
            return data
        fy_year_objs = FiscalYear.objects.filter(
            organization=self._organization,
            applicable_from__gte=start_year.applicable_from,
            category=GLOBAL
        ).intersection(
            FiscalYear.objects.filter(
                organization=self._organization,
                applicable_to__lte=end_year.applicable_to,
                category=GLOBAL
            )
        ).order_by('applicable_from')

        for fy in fy_year_objs:
            if from_date > fy.applicable_from:
                _start = from_date
            else:
                _start = fy.applicable_from

            if to_date < fy.applicable_to:
                _end = to_date
            else:
                _end = fy.applicable_to
            data.append(
                {
                    'fy_slot': (fy.applicable_from, fy.applicable_to,),
                    'date_range': (_start, _end,),
                    'fy_obj_id': fy.id
                },
            )
        return data
