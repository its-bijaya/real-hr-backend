"""@irhrs_docs"""
import ipaddress
from . import attendance_logger


def check_ip_in_network(ip_address_, ip_network_):
    try:
        ip_address = ipaddress.ip_address(ip_address_)
        ip_network = ipaddress.ip_network(ip_network_)
    except ValueError:
        return False
    return ip_address in ip_network


def allow_current_ip(request):
    """
    Checks the IP restriction for the user, during the Web Attendance.
    :param request:
    :return:
    """
    if not request:
        return
    user = request.user
    try:
        remote_address = request.META['REMOTE_ADDR']
    except KeyError:
        remote_address = request.META['HTTP_REMOTE_ADDR']
    attendance_setting = user.attendance_setting
    enabled_web_attendance = attendance_setting.web_attendance
    if not enabled_web_attendance:
        return False
    ip_addresses = list(attendance_setting.ip_filters.all())
    blocked_addresses = filter(
        lambda fil: fil.allow is False,
        ip_addresses
    )
    allowed_addresses = filter(
        lambda fil: fil.allow is True,
        ip_addresses
    )
    disallow = any(filter(
        lambda address: check_ip_in_network(remote_address, address.cidr),
        blocked_addresses
    ))
    allow = any(filter(
        lambda address: check_ip_in_network(remote_address, address.cidr),
        allowed_addresses
    ))
    if disallow:
        attendance_logger.debug(
            f"Restricted {remote_address} for web login due to block."
        )
        return False
    elif allow:
        return True
    attendance_logger.debug(
        f"Restricted {remote_address} for web login due to not allowed."
    )
    return False
