from rest_framework.exceptions import ValidationError

from irhrs.users.api.v1.serializers.user_serializer_common import \
    UserSerializerMixin
from ....models import UserSocialActivity


class SocialActivitySerializer(UserSerializerMixin):
    class Meta:
        model = UserSocialActivity
        fields = ('title', 'slug', 'description')
        read_only_fields = ('slug',)

    def validate(self, data):
        params = {
            'user': self.context.get('user'),
            'title': data.get('title')
        }
        qs = UserSocialActivity.objects.filter(**params)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError({
                'title': 'The title already exists.'
            })
        return data
