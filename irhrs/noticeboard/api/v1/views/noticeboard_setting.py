from irhrs.noticeboard.api.v1.serializers.noticeboard_setting import NoticeBoardSettingSerializer
from irhrs.noticeboard.models.noticeboard_setting import NoticeBoardSetting
from irhrs.core.mixins.viewset_mixins import ListCreateRetrieveViewSetMixin
from irhrs.common.api.permission import CommonNoticeBoardSettingPermission

class NoticeBoardSettingViewSet(ListCreateRetrieveViewSetMixin):
    """
    list:
    list NoticeBoardSetting
    ```javascript
        {
            "allow_to_post": "true",
            "need_approval": "true",
        },,
    ```
    ```
    create:
    Create new NoticeBoardSetting.
    ```javascript
        {
            "allow_to_post": "true",
            "need_approval": "true",
        },,
    retrieve:
    Get the detail for a NoticeBoardSetting.
    ```javascript
        {
            "allow_to_post": "true",
            "need_approval": "true",
        },,

    update:
    Updates the selected religion/ ethnicity details for the given organization.
    ```javascript
        {
            "allow_to_post": "true",
            "need_approval": "true",
        },,

    partial_update:
    Update only selected fields of a NoticeBoardSetting.

    Accepts the same parameters as ```.update()```.
    However, not all fields are required.

    """
    serializer_class = NoticeBoardSettingSerializer
    queryset = NoticeBoardSetting.objects.all()
    permission_classes = [CommonNoticeBoardSettingPermission]
