from django_filters.rest_framework import DjangoFilterBackend

from irhrs.core.mixins.change_request import ChangeRequestMixin
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from irhrs.users.api.v1.serializers.education import UserEducationSerializer
from irhrs.users.models.education_and_training import UserEducation


class UserEducationView(
    ChangeRequestMixin,
    ModelViewSet
):
    """
    list:
    Lists all the available education details for the user.

    ```javascript
    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "userdetail": 1,
                "degree": "phd",
                "field": "BSC CSIT",
                "institution": "TU",
                "university": "TU",
                "marks_type": "cgpa",
                "marks": 3.6,
                "from_year": "2001-01-01",
                "to_year": "2010-01-01",
                "is_current": false,
                "id": 1
            }
        ]
    }
    ```

    create:
    Creates a new education detail for the user.
    ```javascript
    {
        "degree": "Bachelors",
        "field": "CSIT",
        "institution": "TU-Affl",
        "university": "TU",
        "marks_type": "cgpa"
    }
    ```

    retrieve:
    Provides details regarding the selected education for the user.
    ```javascript
    {
        "userdetail": 1,
        "degree": "phd",
        "field": "BSC CSIT",
        "institution": "DWK",
        "university": "TU",
        "marks_type": "cgpa",
        "marks": 3.6,
        "from_year": "2001-01-01",
        "to_year": "2010-01-01",
        "is_current": false,
        "id": 1
    }
    ```
    update:

    * Updates the education details provided the education detail id. The

    * format is similar to `.create()` method.

    partial_update:

    * Partially updates the user education instance. Accepts partial data.

    * Format similar to the `.update()` method.

    delete:

    * Deletes a user education instance provided an id.

   """
    serializer_class = UserEducationSerializer
    filter_fields = ('degree', 'field', 'institution',
                     'university', 'marks_type', 'from_year', 'to_year',
                     'is_current')
    search_fields = ('degree',)
    ordering_fields = ('degree', 'university', 'marks_type',
                       'to_year')
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,
                       DjangoFilterBackend)
    queryset = UserEducation.objects.all()
