from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet

from .serializers import HRPolicyHeadingSerializer, HRPolicyBodySerializer
from irhrs.organization.models import Organization

from ...models import HRPolicyHeading, HRPolicyBody


class HRPolicyHeadingViewSet(ModelViewSet):
    """
    list:
    Lists the policy heading for the selected organization.
        ```javascript

        {
          "count": 1,
          "next": null,
          "previous": null,
          "results": [
            {
              "title": "string",
              "description": "Description",
              "organization": {
                "name": "Google",
                "abbreviation": "GOOG",
                "email": "",
                "slug": "google"
              },
              "status": "Published",
              "order_field": 1,
              "slug": "string"
            }
          ]
        }
        ```
    create:
    Create new policy heading for the given organization.
        ```javascript

        {
          "title": "title_string",
          "description": "description_string",
          "status": "choice", Choices are ("Published", "Unpublished", )
          "order_field": 1
        }
        ```

    retrieve:
    Get the policy heading detail for the organization.
        ```javascript
        {
          "title": "string",
          "description": "Description",
          "organization": {
            "name": "Google",
            "abbreviation": "GOOG",
            "email": "",
            "slug": "google"
            },
          "status": "Published", Choices are ("Published", "Unpublished", )
          "order_field": 1,
          "slug": "string"
        }
        ```
    delete:
    Deletes the policy heading for an organization.

    update:
    Updates the selected policy heading details for the given organization.
        ```javascript
        {
          "title": "change_string",
          "description": "change_description_string",
          "status": "change_choice", Choices are ("Published", "Unpublished", )
          "order_field": 1
        }
        ```
    """
    queryset = HRPolicyHeading.objects.all()
    serializer_class = HRPolicyHeadingSerializer
    lookup_field = 'slug'
    search_fields = ('title',)
    ordering_fields = ('order_field', 'title')
    filter_backends = (SearchFilter, OrderingFilter)

    def get_queryset(self):
        organization_slug = self.kwargs.get('organization_slug')
        get_object_or_404(Organization, slug=organization_slug)
        return self.queryset.filter(
            organization__slug=organization_slug)


class HRPolicyBodyViewSet(ModelViewSet):
    """
    list:
    Lists the policy body for the selected organization.
    ```javascript
        {
          "count": 1,
          "next": null,
          "previous": null,
          "results": [
            {
              "heading": {
                "title": "string",
                "description": "Description",
                "organization_slug": "google",
                "status": "Published"
              },
              "title": "Body title",
              "body": "This is description field",
              "attachment": null,
              "parent": {       // parent of the policy body
                "parent": null
              },
              "order_field": 1,
              "slug": "new",
              "child": [] // list of children of the policy body
            }
          ]
        }

    ```

    create:
    Create new policy body for the given organization.
    ```javascript
    {
      "heading": "heading_slug",
      "title": "Body Title",
      "body": "This is description field",
      "attachment": null, //Attach a file here
      "parent": null, //slug of the parent body
      "order_field": 1 // Order field number
    }
    ```

    retrieve:
    Get the policy body detail for the organization.
    ```javascript
        {
      "heading": {
        "title": "string",
        "description": "Description",
        "organization_slug": "google",
        "status": "Published"
      },
      "title": "New",
      "body": "This is description field",
      "attachment": null,
      "parent": {
        "parent": null
      },
      "order_field": 1,
      "slug": "new",
      "child": []
    }
    ```

    delete:
    Deletes the selected policy body for an organization.

    update:
    Updates the selected policy body details for the given organization.
    ```javascipt
    {
      "heading": "heading_slug",
      "title": "Body Title",
      "body": "This is description field",
      "attachment": null, //Attach a file here
      "parent": null, //slug of the parent body
      "order_field": 1 // Order field number
    }
    ```
    """
    queryset = HRPolicyBody.objects.all()
    serializer_class = HRPolicyBodySerializer
    lookup_field = 'slug'
    search_fields = ('title',)
    ordering_fields = ('order_field', 'title')
    filter_backends = (SearchFilter, OrderingFilter)

    def get_queryset(self):
        organization_slug = self.kwargs.get('organization_slug')
        header_slug = self.kwargs.get('header_slug')
        get_object_or_404(Organization, slug=organization_slug)
        get_object_or_404(HRPolicyHeading, slug=header_slug)
        return self.queryset.filter(
            heading__slug=header_slug
        )
