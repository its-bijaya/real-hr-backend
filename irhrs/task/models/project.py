from django.contrib.auth import get_user_model
from django.db import models as M

from irhrs.core.utils.common import modify_field_attributes

USER = get_user_model()

from irhrs.common.models import BaseModel


@modify_field_attributes(
    created_by={
        'verbose_name': "Project Creator"
    }
)
class TaskProject(BaseModel):
    name = M.CharField(max_length=200, unique=True)
    description = M.TextField()
    members = M.ManyToManyField(USER, blank=True,
                                verbose_name='Project Members')

    def __str__(self):
        return self.name

    class ReportBuilder:
        valid_direct_field = (
            'id', 'name', 'description'
        )
        valid_related_fields = (
            'created_by',
            'members',
        )
