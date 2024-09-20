from calendar import monthrange
from datetime import date
from datetime import timedelta

from irhrs.payroll.utils.datework.bsdate import BSDate, BsDelta
from irhrs.core.utils.nepdate import bs, ad2bs, bs2ad


class DateWork(object):
    calendar_name = 'AD'
    date_class = date
    timedelta_class = timedelta
    # fiscal_year_start_month_date = (4, 1)

    def __init__(self, **kwargs):
        self.fiscal_year_start_month_date = kwargs.get(
            'fiscal_year_start_month_date'
            )

    def get_month_days(self, year, month):
        """
        Returns total days in particular year month of date class
        :param year:
        :param month:
        :return:
        """
        return monthrange(year, month)[1]

    def ad_to_date_class(self, date):
        """
        Converts ad date to date class type
        :param date: date object
        :return: date_class object:
        """
        return date

    def date_class_to_ad(self, date):
        """
        Converts date class object to python ad type
        :param date: date_class object
        :return: date object
        """
        return date

    def get_same_year_month_range_detail(self, employee_appoint_date, from_date, to_date):
        return {
            'start': from_date,
            'end': to_date,
            'worked_years': int((from_date - employee_appoint_date).days / 365),  # todo
            'year': from_date.year,
            'month': from_date.month,
            'month_days': self.get_month_days(from_date.year, from_date.month),
            'days_count': (to_date - from_date).days + 1
        }

    def validate(self, from_date, to_date, employee_appoint_date=None):
        if employee_appoint_date:
            if employee_appoint_date <= from_date and from_date <= to_date:
                return True
        else:
            if from_date <= to_date:
                return True
        return False

    def get_months_data_from_date_range(self, employee_appoint_date, from_date, to_date):

        if not self.validate(from_date, to_date, employee_appoint_date):
            raise ValueError('Invalid arguments. Appoint Date <= from_date <= to_date')

        data = []

        start = from_date
        while True:
            if to_date.month == start.month and to_date.year == start.year:
                end = to_date
            else:
                end = self.date_class(start.year, start.month, self.get_month_days(start.year, start.month))

            data.append(self.get_same_year_month_range_detail(employee_appoint_date, start, end))
            if end == to_date:
                break

            if start.month < 12:
                start = self.date_class(start.year, start.month + 1, 1)
            else:
                start = self.date_class(start.year + 1, 1, 1)
        return data

    def get_fiscal_year_data_from_date_range(self, from_date, to_date):
        if not self.validate(from_date, to_date):
            raise ValueError('Invalid arguments.from_date <= to_date')
        slots = []

        try:
            possible_fy_starts = [
                self.date_class(
                    from_date.year - 1,
                    self.fiscal_year_start_month_date[0],
                    self.fiscal_year_start_month_date[1]
                ),
                self.date_class(
                    from_date.year,
                    self.fiscal_year_start_month_date[0],
                    self.fiscal_year_start_month_date[1]
                ),
                self.date_class(
                    from_date.year + 1,
                    self.fiscal_year_start_month_date[0],
                    self.fiscal_year_start_month_date[1]
                ),
            ]

            if possible_fy_starts[0] <= from_date < possible_fy_starts[1]:
                fy_start_year = possible_fy_starts[0].year
            elif possible_fy_starts[1] <= from_date < possible_fy_starts[2]:
                fy_start_year = possible_fy_starts[0].year + 1

            fy_start_date = self.date_class(fy_start_year, self.fiscal_year_start_month_date[0],
                                            self.fiscal_year_start_month_date[1])
        except Exception as e:
            print(e)
            raise ValueError('Invalid fiscal_year_start_month_date')

        start = from_date
        while True:
            fy_end_date = self.date_class(fy_start_date.year + 1, fy_start_date.month,
                                          fy_start_date.day) - self.timedelta_class(1)
            data = {
                'fy_slot': (fy_start_date, fy_end_date)
            }
            if fy_end_date > to_date:
                end = to_date
            else:
                end = fy_end_date

            data['date_range'] = (start, end)

            slots.append(data)

            if end == to_date:
                break

            fy_start_date = fy_end_date + self.timedelta_class(1)
            start = fy_start_date
        return slots

        # fy_start = self.date_class(from_date, self.fiscal_year_start_month_date[0],
        #                            self.fiscal_year_start_month_date[1])
        # fy_end = self.date_class(from_date + 1, self.fiscal_year_start_month_date[0],
        #                          self.fiscal_year_start_month_date[1]) - self.timedelta_class(
        #     1) - self.timedelta_class(1)

    # def divide_unit_slot_with_holdings_range(self, unit_slot, holdings_list):
    #     for holdings in holdings_list:
    #         pass

    def divide_unit_slot_with_holdings_range(self, unit_slots, holdings_list):
        """
        UF - UT (Unit slot from to unit slot to)
        divide  unit slot with holdings date range
        Holding date range can be:
         F to infinite
         F < SF and


        :param month_slot:
        :return:
        """
        for holdings in holdings_list:
            for unit_slot in unit_slots:
                pass
            pass

    def xxx(self, unit_slot, holdings):
        if not 'holdings' in unit_slot.keys():
            unit_slot['holdings'] = list()
        divided_unit_slots = list()

        uf = unit_slot.get('start')
        ut = unit_slot.get('end')
        for holding in holdings:
            hf = holding.from_date
            ht = holding.to_date

            if not ht:
                if hf <= ht < uf or ut < hf <= ht:
                    continue
                elif hf <= uf and ut <= ht:
                    divided_unit_slots.append(unit_slot['holdings'].append(holding))
                    # unit_slot[]
                # else hf < uf and hf < ut and ht >=uf and
                #     pass
            else:
                pass


class ADDateWork(DateWork):
    calendar_name = 'AD'
    date_class = date
    timedelta_class = timedelta
    fiscal_year_start_month_date = (4, 1)

    def get_month_days(self, year, month):
        return monthrange(year, month)[1]

    def ad_to_date_class(self, date):
        return date


class BSDateWork(DateWork):
    calendar_name = 'BS'
    date_class = BSDate
    timedelta_class = BsDelta
    fiscal_year_start_month_date = (4, 1)

    def get_month_days(self, year, month):
        return bs[year][month - 1]

    def ad_to_date_class(self, ad_date):
        return self.date_class(*ad2bs(ad_date))

    def date_class_to_ad(self, date_class_date):
        return date(*bs2ad(date_class_date.date_tuple()))



addatework = ADDateWork(
    fiscal_year_start_month_date = (4, 1)
)
bsdatework = BSDateWork(
    fiscal_year_start_month_date = (4, 1)
)

dateworks = {
    'AD': addatework,
    'BS': bsdatework
}

available_datework_classes = {
    'AD': ADDateWork,
    'BS': BSDateWork
}

CALENDAR_CHOICES = tuple([(item, item) for item in available_datework_classes.keys()])
