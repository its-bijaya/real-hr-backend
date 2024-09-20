from rest_framework.exceptions import ValidationError

from .user_serializer_common import UserSerializerMixin
from ....models import UserPublishedContent


class UserPublishedContentSerializer(UserSerializerMixin):
    class Meta:
        model = UserPublishedContent
        fields = ('title', 'slug', 'published_date', 'publication_url',
                  'publication', 'content_type', 'summary')
        read_only_fields = ('slug',)

    def validate_title(self, title):
        user = self.context.get('user')
        qs = user.published_contents.filter(title=title)
        if self.instance:
            qs = qs.exclude(title=self.instance.title)
        if qs.exists():
            raise ValidationError("This user already has "
                                  "published content of this title.")
        return title
