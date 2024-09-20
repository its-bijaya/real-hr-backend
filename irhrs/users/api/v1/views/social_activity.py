from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.change_request import ChangeRequestMixin
from ..serializers.social_activity import SocialActivitySerializer
from ....models import UserSocialActivity


class UserSocialActivityViewSet(ChangeRequestMixin, ModelViewSet):
    """
    list:
    * Lists the Social Activities of the user.
    ```javascript
    {
      "count": 1,
      "next": null,
      "previous": null,
      "results": [
        {
          "title": "rock climbing",
          "slug": "rock-climbing",
          "description": "on steppe rocks i walk, neither i talk, nor i stop"
        }
      ]
    }
    ```
    create:
    Create New Social Activity for the user.
    # Payload Format
    ```javascript
    {
      "title": "rock climbing",
      "description": "on steppe rocks i walk, neither i talk, nor i stop"
    }
    ```
    retrieve:
    * Provides detail of an instance for a given slug.

    ```javascript
    {
      "title": "rock climbing",
      "slug": "rock-climbing",
      "description": "on steppe rocks i walk, neither i talk, nor i stop"
    }
    ```

    update:
    * Update Social Activity provided the slug.
    * Refer to `.create()` for format

    partial_update:
    * Allows update to be done on one to multiple fields.

    delete:
    * Delete social activity provided the slug.
    """
    queryset = UserSocialActivity.objects.all()
    serializer_class = SocialActivitySerializer
    lookup_field = 'slug'
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filter_fields = ('title',)
    search_fields = ('title',)
