from django.db import models

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.constants.common import KSA_TYPE, KNOWLEDGE
from irhrs.core.validators import validate_title
from irhrs.organization.models import Organization


class KnowledgeSkillAbility(SlugModel, BaseModel):
    name = models.CharField(max_length=255, validators=[validate_title])
    description = models.TextField(max_length=600, blank=True)
    ksa_type = models.CharField(max_length=22, choices=KSA_TYPE, default=KNOWLEDGE, db_index=True)
    organization = models.ForeignKey(Organization, related_name='ksa', on_delete=models.CASCADE)

    def __str__(self):
        return self.ksa_type + '-' + self.name

    def _get_slug_text(self):
        return str(self).lower()

    class Meta:
        unique_together = ['name', 'organization', 'ksa_type']
        verbose_name_plural = 'Knowledge skill abilities'
