from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility

USER = get_user_model()


class UserKSAO(BaseModel):
    ksa = models.ForeignKey(
        to=KnowledgeSkillAbility,
        on_delete=models.CASCADE,
        related_name='assigned_ksao'
    )
    user = models.ForeignKey(
        to=USER,
        on_delete=models.CASCADE,
        related_name='assigned_ksao'
    )
    is_key = models.BooleanField(
        default=False
    )

    def __str__(self):
        return 'K::' if self.is_key else 'P::' + self.ksa.name + '->' + self.user.full_name
