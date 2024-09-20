from irhrs.users.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.common.models import DutyStation


class DutyStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyStation
        fields = '__all__'

    def validate(self, attrs, *args):
        if self.context and self.context["action"] in ["update","partial_update"]:
            if self.instance.assignments.exists():
                raise ValidationError(
                    {
                        'error': f'This duty station cannot be '
                        f'updated because some users '
                        f'are currently assigned to it.'
                    }
                )
        return attrs
