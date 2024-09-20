from irhrs.common.api.permission import CommonSMTPServerPermission
from irhrs.common.api.serializers.smtp_server import SMTPServerSerializer
from irhrs.common.models.smtp_server import SMTPServer
from irhrs.core.mixins.viewset_mixins import ListCreateDestroyViewSetMixin


class SMTPServerViewSet(ListCreateDestroyViewSetMixin):
    serializer_class = SMTPServerSerializer
    queryset = SMTPServer.objects.all()
    permission_classes = [CommonSMTPServerPermission]
