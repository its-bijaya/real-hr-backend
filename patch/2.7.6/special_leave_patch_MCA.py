"""
TO DO

Leave Apply and approve for nov 13
Apply Credit Leave Request by Suresh Prashad Yadav for 13 November. Request Date and Time should be 13 nov 8 am. Remarks should be "Personal Reason"
Approved above leave by Dhurjati Prasad Sahu on date 13 nov at time 8:12 AM with Remarks "OK"

Leave Apply and approve for nov 18 and 19
Apply Annual Leave Request by Suresh Prashad Yadav for 18 and 19 November. Request Date and Time should be 18 nov 9:00:45 am. Remarks should be "Personal Reason"
Approved above leave by Dhurjati Prasad Sahu on date 18 nov at time 9:05:23 AM with Remarks "OK"

Leave Apply and approve for nov 20
Apply Sick Leave Request by Suresh Prashad Yadav for 20 November. Request Date and Time should be 20 nov 7:14:20 am. Remarks should be "Feeling unwell"
Approved above leave by Dhurjati Prasad Sahu on date 20 nov at time 7:30:12 AM with Remarks "OK"

Leave Rule name and id are
Credit Hour id 14
Sick Leave id 2
Annual Leave id 1
Employee Name and id are
Suresh Prasad Yadav id 58
Dhurjati Prasad Sahu id 15
# Add holiday for November 23 as "Public Holiday"
"""

import json

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from irhrs.core.utils.common import DummyObject
from irhrs.leave.api.v1.serializers.leave_request import LeaveRequestSerializer, LeaveRequestActionSerializer
from irhrs.leave.constants.model_constants import CREDIT_HOUR, REQUESTED, APPROVED
from irhrs.leave.models import LeaveType, MasterSetting, LeaveRequest, LeaveAccount
from irhrs.notification.models import Notification
from irhrs.notification.models.notification import OrganizationNotification

USER = get_user_model()


# 1 Create Leave Request
def create_leave_request(
        user_id, leave_account_id,
        date_from, date_to, time_from, time_to, remarks,
        forced_timestamp
):
    """
    Payload
    --->
        leave_account: 2055
        details: X X X X
        part_of_day:
        start: 2020-08-25
        end: 2020-08-25
        start_time: 11:22
        end_time: 11:22
    <---
    :param user_id:
    :param leave_account_id:
    :param date_from:
    :param date_to:
    :param time_from:
    :param time_to:
    :param remarks:
    :param forced_timestamp:
    :return:
    """
    user = USER.objects.get(pk=user_id)
    leave_account = LeaveAccount.objects.get(pk=leave_account_id)
    part_of_day = '' if leave_account.rule.leave_type.category == CREDIT_HOUR else 'full'
    payload = {
        'leave_account': leave_account_id,
        'details': remarks,
        'part_of_day': part_of_day,
        'start': date_from,
        'end': date_to if date_to else date_from,
        'start_time': time_from if time_from else '',
        'end_time': time_to if time_to else '',
    }
    revised = {k: v for k, v in payload.items() if v}
    post_request = DummyObject(
        method='POST',
        user=user
    )
    context = {
        'request': post_request,
        'leave_type_queryset': LeaveType.objects.filter(
            master_setting__in=MasterSetting.objects.filter(organization=user.detail.organization)
        ),
        'organization': user.detail.organization,
        'view': DummyObject(mode='')
    }
    serializer = LeaveRequestSerializer(
        data=revised,
        context=context
    )
    valid = serializer.is_valid()
    if valid:
        instance = serializer.save()
        # update leave request timestamp
        res = LeaveRequest.objects.filter(id=instance.id).update(
            created_at=forced_timestamp,
            modified_at=forced_timestamp
        )
        print('Update Leave Request Timestamp', res)
        # update leave request history timestamp
        res = instance.history.filter(action=REQUESTED).update(
            created_at=forced_timestamp,
            modified_at=forced_timestamp
        )
        print('Update Leave Request History Timestamp', res)

        return instance
    else:
        print(
            json.dumps(serializer.errors, default=str, indent=4)
        )
        return None


# 2 Approve Leave Request
def approve_leave_request(
        leave_request_id,
        supervisor_id,
        remarks,
        forced_timestamp
):
    """
    [{
        "leave_request": leave_request_id,
        "action": "approve",
        "remark": "Approved"
    },...]
    :param leave_request_id:
    :param supervisor_id:
    :param remarks:
    :param forced_timestamp:
    :return:
    """
    user = USER.objects.get(pk=supervisor_id)
    payload = [
        {
            'leave_request': leave_request_id,
            'action': 'approve',
            'remark': remarks
        }
    ]
    post_request = DummyObject(
        method='POST',
        user=user
    )
    ctx = {
        'request': post_request,
        'leave_requests': LeaveRequest.objects.filter(),
        'view': DummyObject(mode=''),
    }
    serializer = LeaveRequestActionSerializer(
        data=payload,
        context=ctx,
        many=True
    )
    if serializer.is_valid():
        instance = serializer.save()[0]
        # update leave request timestamp
        res = LeaveRequest.objects.filter(id=instance.id).update(
            modified_at=forced_timestamp
        )
        print('Update Leave Approve Timestamp', res)
        # update leave request history timestamp
        res = instance.history.filter(
            action=APPROVED
        ).update(
            created_at=forced_timestamp,
            modified_at=forced_timestamp
        )
        print('Update Leave Approve History Timestamp', res)
        return instance
    else:
        print(
            json.dumps(serializer.errors, indent=4, default=str)
        )
        return None


def update_request_notification_time(instance, text_identifier, forced_timestamp):
    # Update notifications timestamp
    res = Notification.objects.filter(
        action_object_id=instance.id,
        action_content_type=ContentType.objects.get(
            model=instance._meta.model.__name__.lower()
        )
    ).filter(text__icontains=text_identifier).update(
        created_at=forced_timestamp,
        modified_at=forced_timestamp
    )
    print('Update Notification Timestamp', text_identifier, res)
    # Update Organization Notifications timestamp
    res = OrganizationNotification.objects.filter(
        action_object_id=instance.id,
        action_content_type=ContentType.objects.get(
            model=instance._meta.model.__name__.lower()
        )
    ).filter(text__icontains=text_identifier).update(
        created_at=forced_timestamp,
        modified_at=forced_timestamp
    )
    print('Update Organization Notification Timestamp', text_identifier, res)


# -- Control Flow --
def run(create_payload, approve_payload):
    request = create_leave_request(**create_payload)
    if request:
        request.refresh_from_db()
        update_request_notification_time(
            instance=request,
            text_identifier='requested',
            forced_timestamp=create_payload.get('forced_timestamp'),
        )
        instance = approve_leave_request(request.id, **approve_payload)
        import ipdb; ipdb.set_trace()
        appr = instance
        if appr:
            update_request_notification_time(
                instance=appr,
                text_identifier='approved',
                forced_timestamp=approve_payload.get('forced_timestamp'),
            )


# PAYLOAD
DATA = [
    (
        {
            'user_id': '58',
            'leave_account_id': '-',
            'date_from': '2020-11-13',
            'date_to': '2020-11-13',
            'time_from': '',
            'time_to': '',
            'remarks': 'Personal Reason',
            'forced_timestamp': '2020-11-13T07:29:03+05:45',
        },
        {
            'supervisor_id': '15',
            'remarks': 'OK',
            'forced_timestamp': '2020-11-13T08:12:16+05:45',
        }
    ),
    (
        {
            'user_id': '58',
            'leave_account_id': '-',
            'date_from': '2020-11-18',
            'date_to': '2020-11-19',
            'time_from': '',
            'time_to': '',
            'remarks': 'Personal Reason',
            'forced_timestamp': '2020-11-18T08:47:36+05:45',
        },
        {
            'supervisor_id': '15',
            'remarks': 'OK',
            'forced_timestamp': '2020-11-18T09:17:42+05:45',
        }
    ),
    (
        {
            'user_id': '58',
            'leave_account_id': '-',
            'date_from': '2020-11-20',
            'date_to': '2020-11-20',
            'time_from': '',
            'time_to': '',
            'remarks': 'Feeling unwell',
            'forced_timestamp': '2020-11-20T07:14:20+05:45',
        },
        {
            'supervisor_id': '15',
            'remarks': 'OK',
            'forced_timestamp': '2020-11-20T07:30:12+05:45',
        }
    ),

]
with transaction.atomic():
    # BEGIN
    for p1, p2 in DATA:
        run(p1, p2)
    # TERMINATE
