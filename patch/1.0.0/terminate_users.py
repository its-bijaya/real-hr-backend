from django.contrib.auth import get_user_model

from irhrs.core.utils.common import get_today
from irhrs.users.utils import terminate_user_for_date

USER = get_user_model()
active_users = USER.objects.filter(
    is_active=True,
    is_blocked=False
)


def has_expired(dt):
    return dt < get_today()


users = list()

for user in active_users.exclude(
        user_experiences__end_date__isnull=True
):
    last_experience = user.user_experiences.order_by(
        '-end_date'
    ).first()
    if has_expired(last_experience.end_date):
        terminate_user_for_date(last_experience.id)
