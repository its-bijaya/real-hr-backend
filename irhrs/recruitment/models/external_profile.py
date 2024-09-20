import uuid as uuid
from django.db import models

from irhrs.common.models import BaseModel, TimeStampedModel
from irhrs.organization.models.knowledge_skill_ability import KnowledgeSkillAbility
from irhrs.recruitment.models import DocumentCategory, ApplicantReference
from irhrs.recruitment.models.common import AbstractDocument
from irhrs.users.models.user import ExternalUser


class External(BaseModel):
    user = models.OneToOneField(
        ExternalUser,
        on_delete=models.CASCADE,
        related_name='interviewer'
    )
    ksao = models.ManyToManyField(KnowledgeSkillAbility)

    def __str__(self):
        return self.user.full_name

    @property
    def is_anonymous(self):
        return True


class ExternalDocument(TimeStampedModel, AbstractDocument):
    title = models.CharField(max_length=150)
    user = models.ForeignKey(
        External,
        related_name='documents',
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True, related_name='interviewer_documents'
    )
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ReferenceChecker(BaseModel):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        ApplicantReference,
        on_delete=models.CASCADE,
        related_name='reference_checker'
    )

    def __str__(self):
        return self.user.name
