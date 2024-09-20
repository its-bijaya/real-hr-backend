from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.core.utils.common import validate_permissions
from irhrs.organization.api.v1.permissions import OrganizationSettingsWritePermission
from irhrs.organization.api.v1.serializers.message_to_user import \
    MessageToUserSerializer
from irhrs.permission.constants.permissions import ORGANIZATION_PERMISSION, \
    ORGANIZATION_SETTINGS_PERMISSION
from ....models import MessageToUser


class MessageToUserView(ModelViewSet):
    """
    list:
    Lists all the Messages saved by the Manager.

    ```javascript
    {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "title": "Dare to dream big",
            "slug": "dare-to-dream-big",
            "message": "“Don’t be afraid to think outside the box.
             Don’t be afraid to dream big. But remember, that dreams without
             goals are just dreams. And they ultimately fuel disappointments.
             Have goals — life goals, yearly goals, monthly goals.
             Don’t just aspire to make a living; aspire to make a difference.”
             ~ Actor-Director Denzel Washington",
            "created_by": {
                "id": 1,
                "full_name": "fb fb",
                "profile_picture": "http://localhost:8000/static/images/m.png",
                "division": {
                    "name": "indeed - 3238",
                    "slug": "indeed-3238"
                },
                "job_title": "Outsourcing Officer",
                "email": "admin@fb.com",
                "employee_level": "Senior Executive"
            },
            "published": true,
            "message_from": {
                "id": 36,
                "full_name": "John Lopez",
                "profile_picture": "http://localhost:8000/static/images/ot.png",
                "division": {
                    "name": "indeed - 3238",
                    "slug": "indeed-3238"
                },
                "job_title": "Marketing Manager",
                "email": "lisa18@young.com",
                "employee_level": "Senior Executive"
            },
            "created": "2018-12-24T12:37:13.190391+05:45",
            "modified": "2018-12-24T12:37:13.190419+05:45",
            "archived": false
        },
        {
            "title": "Face Your Fear",
            "slug": "face-your-fear",
            "message": "“We’re all destined to have to do the thing we fear the
            most anyway. So, you give your obstacles credit. Find the courage
            to overcome them or see clearly that they are not really worth
            prevailing over. Be brave, have courage. When you do you get
            stronger, more aware, and more respectful of yourself, and that
            which you fear.”
            ~Actor – Matthew McConaughey",
            "created_by": {
                "id": 1,
                "full_name": "fb fb",
                "profile_picture": "http://localhost:8000/static/images/m.png",
                "division": {
                    "name": "indeed - 3238",
                    "slug": "indeed-3238"
                },
                "job_title": "Outsourcing Officer",
                "email": "admin@fb.com",
                "employee_level": "Senior Executive"
            },
            "published": true,
            "message_from": {
                "id": 37,
                "full_name": "Bryan Zuniga",
                "profile_picture": "http://localhost:8000/static/images/m.png",
                "division": {
                    "name": "ability - db88",
                    "slug": "ability-db88"
                },
                "job_title": "CEO",
                "email": "rogersbarbara@gmail.com",
                "employee_level": "Senior Executive"
            },
            "created": "2018-12-24T12:37:48.762525+05:45",
            "modified": "2018-12-24T12:37:48.762552+05:45",
            "archived": false
        }
    ]
}
    ```

    create:

    Create a new Message

    ## Field Knowledge
    ```javascript
        {
        "title": "", /*Title of the Message*/
        "message": "", /*Message Body*/
        "message_from": 1 /*user id whose speech it is.*/
        "published": false, /*visible to the user*/
        "archived": false, /*currently not active*/
    }
    ```

    delete:
    ## Deletes a message given the slug.

    update:
    ## Updates a selected Message
    ### Refer to the `create` action or `POST` method

    partial_update:

    ## Partially update a selected message.
    ### Accepts the same parameters as update. Not all fields are required.

    retrieve:
    Selects details of a selected message.

    ```javascript
       {
        "title": "Dare to dream big",
        "slug": "dare-to-dream-big",
        "message": "“Don’t be afraid to think outside the box.
        Don’t be afraid to dream big. But remember, that dreams without goals
        are just dreams. And they ultimately fuel disappointments.
        Have goals — life goals, yearly goals, monthly goals.
        Don’t just aspire to make a living; aspire to make a difference.”
        ~ Actor-Director Denzel Washington",
        "created_by": {
            "id": 1,
            "full_name": "fb fb",
            "profile_picture": "http://localhost:8000/static/images/male.png",
            "division": {
                "name": "indeed - 3238",
                "slug": "indeed-3238"
            },
            "job_title": "Outsourcing Officer",
            "email": "admin@fb.com",
            "employee_level": "Senior Executive"
        },
        "published": true,
        "message_from": {
            "id": 36,
            "full_name": "John Lopez",
            "profile_picture": "http://localhost:8000/static/images/other.png",
            "division": {
                "name": "indeed - 3238",
                "slug": "indeed-3238"
            },
            "job_title": "Marketing Manager",
            "email": "lisa18@young.com",
            "employee_level": "Senior Executive"
        },
        "created": "2018-12-24T12:37:13.190391+05:45",
        "modified": "2018-12-24T12:37:13.190419+05:45",
        "archived": false
    }
    ```
    """
    queryset = MessageToUser.objects.all()
    serializer_class = MessageToUserSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter)
    filter_fields = (
        'title', 'created_by', 'message_from', 'published', 'archived'
    )
    search_fields = ('title', 'message_from__first_name')
    ordering_fields = (
        'title', 'created_at', 'modified_at', 'published', 'archived',
        'created_by', 'message_from'
    )
    lookup_field = 'slug'
    permission_classes = [OrganizationSettingsWritePermission]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Only show not published messages to Admin
        if validate_permissions(
            self.request.user.get_hrs_permissions(),
            ORGANIZATION_SETTINGS_PERMISSION
        ):
            return queryset
        else:
            return queryset.filter(published=True)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'userdetail': self.request.user
        })
        return ctx

    @staticmethod
    def get_organization():
        # to handle organization specific permission
        return None
