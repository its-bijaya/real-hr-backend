from irhrs.core.mixins.change_request import NoCreateChangeRequestMixin
from irhrs.core.mixins.viewset_mixins import RetrieveUpdateViewSetMixin
from ..serializers.medical_info import UserMedicalInfoSerializer
from ....models import UserMedicalInfo


class UserMedicalInfoView(
    NoCreateChangeRequestMixin, RetrieveUpdateViewSetMixin
):
    """
    create:
    ## Create User Medical Info

    Data
    ```javascript
    {
        "blood_group": "a+",
        "height": 120,
        "height_unit": cms,
        "weight": 60,
        "weight_unit": kgs,
        "smoker": false,
        "drinker": false,
        "on_medication": true,
        "chronic_disease": [
            {
                "title": "Asthma",
                "description": "RTI"
            },
            {
                "title": "Rheumatoid Arthritis",
                "description": "Back Pain"
            }
        ]
    }
    ```

    retrieve:

    Retrieve a User Medical detail given the id.

    ```javascript
    {
        "userdetail": 4,
        "blood_group": "b+",
        "height": 121.0,
        "height_unit": "cms",
        "weight": 120.0,
        "weight_unit": "lbs",
        "smoker": true,
        "drinker": true,
        "on_medication": true,
        "media_link": [],
        "id": 4,
        "chronic_disease": [
            {
                "title": "AIDS",
                "description": "",
                "userdetail": 4,
                "slug": "aids"
            },
            {
                "title": "diabities",
                "description": "",
                "userdetail": 4,
                "slug": "diabities"
            },
            {
                "title": "cholestrol",
                "description": "",
                "userdetail": 4,
                "slug": "cholestrol"
            },
            {
                "title": "asthma",
                "description": "",
                "userdetail": 4,
                "slug": "asthma"
            }
        ]
    }
    ```
    update:

    Update User Medical Info:
    ## During the update, the fields chronic_disease and media_link behave as:
    * Add new chronic disease et. al
    ```javascript
        [
            {
                "title": "Rheumatoid"
            }
        ]
    ```
    * Update existing chronic disease:
    ```javascript
        [
            {
                "title": "Rheumatoid Arthritis",
                "slug": "rheumatoid",
                "description": "Pain in the joints."
            }
        ]
    ```
    * Example:
    Data
    ```javascript
    {
        "blood_group": "a-",
        "height": 6.11,
        "height_unit": "ft.in",
        "weight": 60.0,
        "weight_unit": "kgs",
        "smokes": false,
        "drinks": false,
        "medicates": true,
        "chronic_disease": {
            "title": "Necronemesis",
            "slug": "necronemesis",
            "description": "Love non living Bodies."
        }
    }
    ```

    partial_update:

    Updates User Medical Info Details partially.

    Accepts the same parameters as ```.update()``` but not all fields required.

    """
    queryset = UserMedicalInfo.objects.all()
    serializer_class = UserMedicalInfoSerializer

    def get_object(self):
        return self.get_queryset().first()
