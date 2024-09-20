import abc
import typing
import datetime


class AbstractDatework(abc.ABC):
    """Abstract Class for Datework

    Implement this interface to pass datework argument of payroll

    Methods to override:
        * :func:`~AbstractDatework.get_months_data_from_date_range`
        * :func:`~AbstractDatework.get_fiscal_year_data_from_date_range`
    """

    @abc.abstractmethod
    def get_months_data_from_date_range(
        self,
        employee_appoint_date: datetime.date,
        from_date: datetime.date,
        to_date: datetime.date
    ) -> typing.List[typing.Dict]:
        """
        Should return months slots from given date range.

        :param employee_appoint_date: Employee appoint date
        :param from_date: From date
        :param to_date: To date

        :return: List of months

        .. code-block:: python

            [
                {
                    'start': <date: Slot applicable start date>,
                    'end': <date: Slot applicable end date>,
                    'actual_start': <date: Actual slot start date>,
                    'actual_end': <date: Actual slot end date>
                    'month_days': <int: Total days in the month of slot>,
                    'days_count': <int: Total days in slot>
                },
                ...
            ]


        """

    @abc.abstractmethod
    def get_fiscal_year_data_from_date_range(
        self,
        from_date: datetime.date,
        to_date: datetime.date
    ):
        """
        Should return list of fiscal year slots contained in from_date and to_date
        along  with date range included in particular fiscal year


        :param from_date: From date
        :param to_date: To date

        :return: List of fiscal year slots

        .. code-block:: python

                [
                    {
                        'fy_slot': <tuple: (<date: FY start date>, <date: FY end date>)>,
                        'date_range': <tuple: Tuple of date range containing is FY>,
                    },
                    ...
                ]

        """
