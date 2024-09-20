from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.validators import validate_start_end_date, validate_title
from .user_serializer_common import UserSerializerMixin
from ....models import UserTraining


class UserTrainingSerializer(UserSerializerMixin):
    name = serializers.CharField(required=True, max_length=100,
                                 validators=[validate_title])

    class Meta:
        model = UserTraining
        fields = ('name', 'institution', 'is_current', 'start_date',
                  'end_date', 'slug', 'user')
        read_only_fields = ('slug',)

    def validate(self, data):
        validate_start_end_date(data.get('start_date'), data.get('end_date'),
                                self, data.get('is_current')
                                )
        return data

    def validate_name(self, name):
        user = self.context.get('user')
        qs = user.trainings.filter(name=name)
        if self.instance:
            qs = qs.exclude(name=self.instance.name)
        if qs.exists():
            raise ValidationError("This user already has "
                                  "training of this name.")
        return name
