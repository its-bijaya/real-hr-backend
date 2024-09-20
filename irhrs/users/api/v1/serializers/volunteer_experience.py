from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.validators import validate_start_end_date
from irhrs.core.validators import validate_title
from .user_serializer_common import UserSerializerMixin
from ....models import UserVolunteerExperience


class UserVolunteerExperienceSerializer(UserSerializerMixin):
    title = serializers.CharField(
        required=True,
        max_length=150,
        validators=[validate_title]
    )

    class Meta:
        model = UserVolunteerExperience
        fields = ('title', 'role', 'currently_volunteering', 'description',
                  'start_date', 'end_date', 'slug',
                  'organization', 'cause')
        read_only_fields = ('slug',)

    def validate_title(self, title):
        user = self.context.get('user')
        qs = user.volunteer_experiences.filter(title=title)
        if self.instance:
            qs = qs.exclude(title=self.instance.title)
        if qs.exists():
            raise ValidationError("This user already has "
                                  "Volunteer Experience of this title.")
        return title

    def validate(self, data):
        validate_start_end_date(
            data.get('start_date'), data.get('end_date'),
            self, data.get('currently_volunteering')
        )
        return data

    def get_role(self, obj):
        if hasattr(obj, 'title'):
            return obj.title
        return None
