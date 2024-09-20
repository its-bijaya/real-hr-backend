"""@irhrs_docs"""
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.user import PENDING
from irhrs.core.mixins.viewset_mixins import UserCommonsMixin, _HR
from irhrs.core.utils.change_request import send_change_request, \
    ChangeRequestSerializerClass, create_delete_change_request, \
    NoCreateChangeRequestSerializerClass
from irhrs.users.models import ChangeRequest
from irhrs.users.utils.notification import send_change_notification_to_user


class ChangeRequestMixin(UserCommonsMixin):
    def initial(self, *args, **kwargs):
        if (self.request.method.lower() != 'get' and self.request.query_params.get('as') == 'supervisor'):
            self.permission_denied(self.request)
        super().initial(*args, **kwargs)

    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()

        # if request is get or not send change request return default
        if self.request.method.upper() == 'GET' or\
                not self.send_change_request:
            return serializer_class

        cr_serializer = ChangeRequestSerializerClass(
            serializer_class,
            self.user
        )
        return cr_serializer()

    @property
    def send_change_request(self):
        """
        If User is HR, Send Change Request is Always False.
        To always prevent this default behavior, mode is introduced.
        Mode is applicable for HR (users with USER_PROFILE_PERMISSION) only.

        For Normal User, Always send change request.
        For HR User, Send Change request if mode != 'HR'
        :return Always
        """
        if send_change_request(
            request_user=self.request.user, user=self.user
        ):
            return True
        return self.mode != _HR

    def perform_destroy(self, instance):
        # intercept destroy
        if self.send_change_request:
            category = instance.__class__._meta.verbose_name.replace(
                    "user ", "").title()
            ctype = ContentType.objects.get_for_model(instance)

            if ChangeRequest.objects.filter(
                    is_deleted=True,
                    content_type=ctype,
                    object_id=instance.id,
                    status=PENDING
            ).exists():
                raise ValidationError(detail={
                    "non_field_errors": ["A change request to delete this "
                                         "record already exists."]})

            create_delete_change_request(
                user=self.user,
                obj=instance,
                category=category
            )
        else:
            super().perform_destroy(instance)
            send_change_notification_to_user(
                self, instance.user, instance.user,
                self.request.user, 'deleted'
            )


class NoCreateChangeRequestMixin(ChangeRequestMixin):
    def get_serializer_class(self):
        serializer_class = super().get_serializer_class()

        # if request is get or not send change request return default
        if self.request.method.upper() == 'GET' or\
                not self.send_change_request:
            return serializer_class

        cr_serializer = NoCreateChangeRequestSerializerClass(
            serializer_class,
            self.user
        )
        return cr_serializer()
