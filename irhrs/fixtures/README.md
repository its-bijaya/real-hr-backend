### Fixtures regarding Permissions
* Permission can be seeded by `setup_hrs_permissions`
* Later, dump the permissions onto a file, and place it under `fixtures`

```python
import json
from django.db.models.functions import Cast
from django.db.models import FloatField

from irhrs.permission.models import HRSPermission
from irhrs.permission.api.v1.serializers.hrs_permission import HRSPermissionSerializer

queryset = HRSPermission.objects.annotate(
    numeric_code=Cast(
        'code',
        FloatField()
    )
).order_by(
    'numeric_code'
)
model_name = 'permission.hrspermission'
fixtures_dump_file = open('permissions.json', 'w')
headers = ('model', 'fields')
permission_data = HRSPermissionSerializer(
    instance=queryset,
    many=True,
    exclude_fields=['id']
).data

json_object = [
    dict(
        zip(('model', 'fields'), (model_name, data))
    )  for data in permission_data
]

json.dump(
    obj=json_object,
    fp=fixtures_dump_file
)

fixtures_dump_file.close()
```
