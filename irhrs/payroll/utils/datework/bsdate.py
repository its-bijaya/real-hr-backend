# This module uses njango module for Bikram Sambat Calendar
from irhrs.core.utils.nepdate import bs, bs2ad, ad2bs
from datetime import date, timedelta


class BsDelta(object):
    def __init__(self, days):
        self.days = days


class BSDate(object):
    def __init__(self, year, month, day):
        self._year = year
        self._month = month
        self._day = day

        try:
            bs[self._year]
        except KeyError:
            raise ValueError('No such year in njango nepdate calendar')
        if self._month > 12 or self._month < 1:
            raise ValueError('Incorrect Month')
        if self._day > bs[self._year][self._month - 1] or self._day < 1:
            raise ValueError('Incorrect date')

    def date_tuple(self):
        return (self._year, self._month, self._day)

    def as_string(self):
        return '%s-%s-%s' % (
            str(self._year),
            str(self._month).zfill(2),
            str(self._day).zfill(2)
        )

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def day(self):
        return self._day

    def __sub__(self, other):

        if type(other) == BsDelta:
            return BSDate(*ad2bs(date(*bs2ad(self.date_tuple())) - timedelta(other.days)))
        elif type(other) == BSDate:
            delta = date(*bs2ad(self.date_tuple())) - \
                    date(*bs2ad(other.date_tuple()))
            return BsDelta(delta.days)
        else:
            return ValueError('Invalid operands')

    def __add__(self, other):
        if type(other) == BsDelta:
            return BSDate(*ad2bs(date(*bs2ad(self.date_tuple())) + timedelta(other.days)))
        else:
            raise ValueError('Invalid BsDelta')

    def __eq__(self, other):
        if self.__sub__(other).days == 0:
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.__sub__(other).days < 0:
            return True
        else:
            return False

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        if self.__sub__(other).days > 0:
            return True
        else:
            return False

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __repr__(self):
        return '<BSDate->' + str(self.date_tuple())
