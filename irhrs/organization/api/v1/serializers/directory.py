from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from irhrs.users.models import UserDetail


