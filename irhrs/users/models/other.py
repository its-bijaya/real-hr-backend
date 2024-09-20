from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models

from irhrs.common.models import SlugModel, BaseModel, DocumentCategory
from irhrs.common.models.commons import Bank
from irhrs.core.constants.common import SCORE_CHOICES, EMPLOYEE
from irhrs.core.constants.user import (PUBLISHED_CONTENT_TYPE)
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import (validate_title, validate_past_date,
                                   validate_has_digit, validate_invalid_chars,
                                   DocumentTypeValidator)

USER = get_user_model()


class UserLanguage(BaseModel, SlugModel):
    user = models.ForeignKey(USER,
                             related_name='languages',
                             on_delete=models.CASCADE,
                             editable=False)
    name = models.CharField(max_length=100, validators=[validate_title])
    native = models.BooleanField(default=False)
    speaking = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
    reading = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
    writing = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
    listening = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)

    class Meta:
        ordering = ('name',)
        unique_together = ('name', 'user')

    def __str__(self):
        return "Language - {}".format(self.name)


class UserPublishedContent(BaseModel, SlugModel):
    user = models.ForeignKey(USER,
                             related_name='published_contents',
                             on_delete=models.CASCADE,
                             editable=False)
    title = models.CharField(max_length=150, validators=[validate_title])
    publication = models.CharField(max_length=150,
                                   blank=True,
                                   help_text="Publication",
                                   validators=[validate_title])
    content_type = models.CharField(max_length=30,
                                    choices=PUBLISHED_CONTENT_TYPE)
    published_date = models.DateField(null=True,
                                      validators=[validate_past_date])
    publication_url = models.URLField(blank=True)
    summary = models.TextField(max_length=600)

    class Meta:
        ordering = ['title']
        unique_together = ('title', 'user', 'published_date',)

    def __str__(self):
        return f"{self.content_type} published on - {self.publication}"


class UserSocialActivity(BaseModel, SlugModel):
    """
    This model stores multiple Social Activities of the User.
    Activities that correlates other individuals/ group.
    """
    user = models.ForeignKey(to=USER,
                             related_name='social_activities',
                             on_delete=models.CASCADE,
                             editable=False)

    title = models.CharField(max_length=150, validators=[validate_title])
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('title',)
        unique_together = ('title', 'user')

    def __str__(self):
        return self.title


class UserBank(BaseModel):
    user = models.OneToOneField(to=USER,
                                on_delete=models.CASCADE,
                                editable=False)
    bank = models.ForeignKey(to=Bank,
                             related_name='user_banks',
                             on_delete=models.CASCADE)
    account_number = models.CharField(max_length=150,
                                      validators=[validate_has_digit,
                                                  validate_invalid_chars])
    branch = models.CharField(max_length=150, blank=True, null=True,
                              validators=[validate_title])

    class Meta:
        unique_together = ('bank', 'account_number')

    def __str__(self):
        return f"{self.user} - {self.bank}"


class UserDocument(BaseModel, SlugModel):
    """Model to store user documents"""
    user = models.ForeignKey(USER, on_delete=models.CASCADE, related_name='documents')

    # can not user created_by here because in case of document added by change request
    # created_by is person who accepts it
    uploaded_by = models.ForeignKey(USER, on_delete=models.CASCADE, related_name='uploaded_documents', null=True)

    title = models.CharField(max_length=255, validators=[validate_title])
    document_type = models.ForeignKey(
        to=DocumentCategory, on_delete=models.SET_NULL,
        null=True, related_name="user_documents",
        validators=[DocumentTypeValidator(association_type=EMPLOYEE)]
    )
    file = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )

    def __str__(self):
        return f"Document from {self.user.full_name} - {self.title}"
