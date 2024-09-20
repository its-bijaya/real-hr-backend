import smtplib

from rest_framework.exceptions import ValidationError

from irhrs.common.models.smtp_server import SMTPServer
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer


class SMTPServerSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = SMTPServer
        fields = '__all__'

    @staticmethod
    def connection_class(attrs):
        return smtplib.SMTP_SSL if attrs.get('use_ssl') else smtplib.SMTP

    def validate(self, attrs):
        if attrs.get('use_ssl') and attrs.get('use_tls'):
            raise ValidationError({
                'non_field_errors': "Use TLS/Use SSL are mutually exclusive, so"
                                    " only set one of those settings to True."
            })

        connection_class = self.connection_class(attrs)
        try:
            with connection_class(
                attrs.get('host'),
                attrs.get('port')
            ) as server:
                if attrs.get('use_tls'):
                    server.starttls()
                server.login(attrs.get('username'), attrs.get('password'))
        except smtplib.SMTPAuthenticationError:
            raise ValidationError(
                {
                    'non_field_error': ['Unable to login. Provide valid credential.']
                }
            )
        except smtplib.SMTPServerDisconnected:
            raise ValidationError(
                {
                    'non_field_error': ['Unable to connect. Provide valid smtp information.']
                }
            )
        except OSError:
            raise ValidationError({
                'non_field_error': ['Network Unreachable. Provide valid smtp information.']
            })
        return super().validate(attrs)

    def create(self, validated_data):
        SMTPServer.objects.all().delete()
        return super().create(validated_data)
