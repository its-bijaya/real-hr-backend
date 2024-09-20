from rest_framework.exceptions import ValidationError

from irhrs.core.validators import validate_start_end_date
from .user_serializer_common import UserSerializerMixin
from ....models import UserPastExperience


class UserPastExperienceSerializer(UserSerializerMixin):
    class Meta:
        model = UserPastExperience
        fields = ('title', 'slug', 'organization',
                  'responsibility', 'department', 'employment_level',
                  'employment_status', 'job_location', 'start_date',
                  'end_date')
        read_only_fields = ('slug',)

    def validate_title(self, title):
        user = self.context.get('user')
        qs = user.past_experiences.filter(title=title)
        if self.instance:
            qs = qs.exclude(title=self.instance.title)
        if qs.exists():
            raise ValidationError("This user already has "
                                  "past experience of this title.")
        return title

    def validate(self, data):
        validate_start_end_date(data.get('start_date'),
                                data.get('end_date'),
                                self)
        return data
