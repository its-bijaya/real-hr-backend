"""@irhrs_docs"""
from ipaddress import ip_address, ip_network

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import (
    DAILY_OVERTIME_LIMIT_IN_HOURS, OFF_DAY_OVERTIME_LIMIT, OVERTIME_DELTA_MAX,
    WEEKLY_OVERTIME_LIMIT_IN_HOURS, MONTHLY_OVERTIME_LIMIT_IN_HOURS)
from irhrs.attendance.validation_error_messages import INVALID_CIDR


def validate_daily_overtime_limit(value):
    if 0 < value < (DAILY_OVERTIME_LIMIT_IN_HOURS * 60):
        return value
    raise ValidationError(_("The daily limit must be between 0 "
                            "and 24 hours (exclusive)"))


def validate_weekly_overtime_limit(value):
    if 0 < value < (WEEKLY_OVERTIME_LIMIT_IN_HOURS * 60):
        return value
    raise ValidationError(_("The weekly limit must be between 0 "
                            f"and {WEEKLY_OVERTIME_LIMIT_IN_HOURS} hours (exclusive)"))


def validate_monthly_overtime_limit(value):
    if 0 < value < (MONTHLY_OVERTIME_LIMIT_IN_HOURS * 60):
        return value
    raise ValidationError(_("The monthly limit must be between 0 "
                            f"and {MONTHLY_OVERTIME_LIMIT_IN_HOURS} hours (exclusive)"))


def validate_off_day_overtime_limit(value):
    if value > OFF_DAY_OVERTIME_LIMIT:
        raise ValidationError(_(
            f"The maximum value must be less than "
            f"{OFF_DAY_OVERTIME_LIMIT} minutes"
        ))
    return value


def validate_overtime_delta(value):
    if value > OVERTIME_DELTA_MAX:
        raise ValidationError(_(
            f"The maximum value for overtime begin/end must be less than "
            f"{OVERTIME_DELTA_MAX} minutes"
            ))
    return value


def validate_CIDR(value):
    """
    Validate CIDR
    :param value: CIDR String
    :return:
    """
    try:
        ip_network(value)
    except ValueError:
        raise ValidationError(INVALID_CIDR)
    return value


def validate_shift_exists(user, for_date):
    if not user.attendance_setting.work_shift_for(for_date):
        raise ValidationError(
            "User does not have a shift for the selected date."
        )
