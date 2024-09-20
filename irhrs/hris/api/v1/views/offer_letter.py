from cryptography.fernet import Fernet as EncyptFromFernet, InvalidToken
from django.conf import settings
from django.http import Http404
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.viewset_mixins import RetrieveUpdateViewSetMixin
from irhrs.core.utils.common import format_timezone, get_today
from irhrs.hris.api.v1.serializers.onboarding_offboarding import \
    OfferLetterSerializer
from irhrs.hris.constants import EXPIRED, DECLINED, ACCEPTED, SENT, NOT_SENT, \
    FAILED
from irhrs.hris.models.onboarding_offboarding import GeneratedLetter

fernet = EncyptFromFernet(settings.FERNET_KEY)
decrypt_string = lambda token: fernet.decrypt(token.encode()).decode()


class PerformOfferLetter(RetrieveUpdateViewSetMixin):
    authentication_classes = []
    permission_classes = []  # Remove permission to allow non-logged in user.
    serializer_class = OfferLetterSerializer
    queryset = GeneratedLetter.objects.exclude(
        status__in=[FAILED]
    )
    lookup_field = 'uri'

    def get_object(self):
        seid = self.request.query_params.get('seid')
        instance = super().get_object()
        if instance.status == NOT_SENT:
            raise ValidationError(
                'Cannot access url unless offer letter is sent to the candidate.'
            )
        try:
            decryption_key = decrypt_string(seid)
        except (InvalidToken, AttributeError):
            raise Http404
        if decryption_key != format_timezone(
                instance.created_at.replace(microsecond=0)
        ) or not hasattr(instance, 'preemployment'):
            raise Http404
        return instance

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status in [ACCEPTED, DECLINED, EXPIRED]:
            raise ValidationError({
                'message': 'The letter cannot be acted further'
            })
        pre_employment = getattr(instance, 'preemployment', None)
        if not pre_employment:
            raise Http404
        deadline = pre_employment.deadline.astimezone()
        now = get_today(with_time=True)
        if deadline < now:
            raise ValidationError(
                "The offer expired on {}".format(
                    format_timezone(deadline)
                )
            )
        return super().update(request, *args, **kwargs)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'remove_link': True
        })
        return ctx
