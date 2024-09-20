from irhrs.hris.utils.utils import update_user_profile_completeness
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

with transaction.atomic():
    for user in User.objects.all():
        update_user_profile_completeness(user)
