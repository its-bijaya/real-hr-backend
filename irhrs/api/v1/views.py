from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from config import VERSION
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_today, get_complete_url


class ServerInfoView(APIView):
    """
    Get server info.
    Public information about the server such as server time, api version, etc.

    Available fields-> `server_time`, `timezone`, `api_version`, `system_name`, `system_logo`

    Eg. `?fields=server_time,timezone`
    """
    permission_classes = []

    def parse_params(self):
        fields = self.request.query_params.get('fields')
        if fields:
            return fields.split(',')
        return []

    @staticmethod
    def _get_func_name_from_field(field_name):
        return f"get_{field_name}"

    def get_value_for_param(self, field_name):
        return getattr(self, self._get_func_name_from_field(field_name))()

    def is_valid_field(self, field_name):
        return hasattr(self, self._get_func_name_from_field(field_name))

    def get(self, request):
        asked_fields = self.parse_params()
        response_data = dict()

        for field_name in asked_fields:
            if self.is_valid_field(field_name):
                response_data.update({
                    field_name: self.get_value_for_param(field_name)
                })

        return Response(response_data)

    @staticmethod
    def get_server_time():
        return str(get_today(with_time=True))

    @staticmethod
    def get_timezone():
        return settings.TIME_ZONE

    @staticmethod
    def get_api_version():
        return {
            'version': ".".join(str(i) for i in VERSION[:4]),
            'status': VERSION[4]
        }

    @staticmethod
    def get_system_name():
        return getattr(settings, 'SYSTEM_NAME', 'RealHRSoft')

    @staticmethod
    def get_system_logo():
        admin = get_system_admin()
        if admin.profile_picture:
            return admin.custom_profile_pic_thumb(size='250x250', crop='')
        return get_complete_url(url='logos/real-hr-leaf.png', att_type='static')
