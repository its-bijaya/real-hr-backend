from rest_framework.exceptions import ValidationError

from ....models import UserLanguage
from .user_serializer_common import UserSerializerMixin


class UserLanguageSerializer(UserSerializerMixin):
    class Meta:
        model = UserLanguage
        fields = ('slug', 'name', 'native',
                  'speaking', 'reading', 'writing', 'listening')
        read_only_fields = ('slug',)

    def validate_native(self, native):
        if native:
            try:
                user = self.context.get('user')
                if self.instance:
                    language = UserLanguage.objects.exclude(
                        id=self.instance.id).get(
                        native=native,
                        user=user)
                else:
                    language = UserLanguage.objects.get(
                        native=native,
                        user=user)
                if language:
                    raise ValidationError("User already has a native language")
            except UserLanguage.DoesNotExist:
                return native
        return native

    def validate_name(self, name):
        user = self.context.get('user')
        qs = user.languages.filter(name=name)
        if self.instance:
            qs = qs.exclude(name=self.instance.name)
        if qs.exists():
            raise ValidationError("This user already has "
                                  "language of this name.")
        return name
