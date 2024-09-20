# ===========README============
# ALLOW_PAST_REQUESTS_FOR_PRE_APPROVAL = True
# set in env.py
# ===========/ README============

from django.contrib.auth import get_user_model

from irhrs.attendance.api.v1.serializers.credit_hours import CreditHourRequestSerializer

credit_user = get_user_model().objects.get(id=30)

payload = {
    "credit_hour_duration": "01:00:00",
    "credit_hour_date": "2020-10-01",
    "remarks": "1 hour credit request [From Backend]"
}

dummy_request_post = type(
    'Request',
    (object,),
    {
        'method': 'POST',
        'user': credit_user,
    }
)
serializer = CreditHourRequestSerializer(
    data=payload,
    context=dict(
        sender=credit_user,
        history=False,
        allow_request=True,
        allow_edit=True,
        request=dummy_request_post
    )
)

if serializer.is_valid():
    serializer.save()
else:
    print(serializer.errors)


# Credit Hour Request PATCH [OCT - 01 | 01:00:00]
