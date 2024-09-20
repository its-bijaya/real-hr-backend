import logging
from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import FileExtensionValidator
from django.db import models, IntegrityError
from django.db.models import ForeignKey, ManyToManyField, OneToOneField, \
    FileField
from django.utils.functional import cached_property

from irhrs.common.models import BaseModel
from irhrs.core.constants.user import CHANGE_REQUEST_STATUS_CHOICES, PENDING
from irhrs.core.utils.common import get_upload_path
from irhrs.users.managers import ChangeRequestManager

USER = get_user_model()

logger = logging.getLogger(__name__)


class ChangeRequest(BaseModel, models.Model):
    user = models.ForeignKey(USER, related_name='change_requests',
                             on_delete=models.CASCADE)
    updated_by = models.ForeignKey(
        USER,
        related_name='updated_changerequests',
        null=True,
        on_delete=models.SET_NULL)

    remarks = models.CharField(blank=True, max_length=200)

    # request to recognize the request related step
    # eg. General Information, Education, Training, etc.
    category = models.CharField(blank=True, max_length=100)
    status = models.CharField(choices=CHANGE_REQUEST_STATUS_CHOICES,
                              default=PENDING,
                              max_length=20,
                              db_index=True)

    # object being created or updated is here
    content_type = models.ForeignKey(ContentType, null=True,
                                     on_delete=models.SET_NULL)
    object_id = models.PositiveIntegerField(null=True)
    change_object = GenericForeignKey()

    # if the user has asked the particular object
    # to be deleted, we just need to remove
    is_deleted = models.BooleanField(null=True, )

    objects = ChangeRequestManager()

    def apply_change_request(self):
        """
        This method applies this particular ChangeRequest
        instance to the object
        """
        if self.object_id and self.content_type:
            instance = self.change_object
        else:
            # just create new object from content type
            instance = self.content_type.model_class()()

        if self.is_deleted:
            # find all other change requests related to this objects which
            # are not approved yet and delete
            content_type = ContentType.objects.get_for_model(instance)
            self.__class__.objects.filter(
                content_type=content_type,
                object_id=instance.id,
                status=PENDING
            ).delete()

            # delete the instance right here and return
            instance.delete()
        else:
            if hasattr(instance, 'change_request_handler'):
                # some models might require custom handler to
                # apply change requests
                return getattr(instance, 'change_request_handler')(
                    change_request=self)

            details = self.details.all()

            # many to many fields require current instance to be saved so
            # we save them at last
            many_to_many = dict()

            for detail in details:
                change_field = instance.__class__._meta.get_field(
                    detail.change_field)

                if isinstance(change_field,
                              (ForeignKey, OneToOneField)):
                    setattr(instance, f"{detail.change_field}_id",
                            detail.new_value)

                elif isinstance(change_field, ManyToManyField):
                    # since we stored them in char field we need to parse them
                    new_pks = detail.new_value[1:-1].split(',')
                    # parsing `'[]'` returns the list of `['']`
                    if '' in new_pks:
                        continue
                    new_values = change_field.related_model.objects.filter(
                        id__in=new_pks)
                    many_to_many.update({detail.change_field: new_values})
                elif isinstance(change_field,
                                FileField):
                    setattr(instance, detail.change_field, detail.files)
                else:
                    setattr(instance, detail.change_field, detail.new_value)

            try:
                instance.save()
            except IntegrityError as e:
                logger.error(e, exc_info=True)
                return False

            # Save many-to-many relationships after the instance is created.
            if many_to_many:
                for field_name, value in many_to_many.items():
                    field = getattr(instance, field_name)
                    field.set(value)

        return True

    @cached_property
    def action(self):
        if self.is_deleted:
            return "Delete"
        elif self.change_object:
            return "Update"
        else:
            return "Create"

    def __str__(self):
        return f"{self.user.full_name} " \
               f"- {self.category} - {self.status}"


class ChangeRequestDetails(models.Model):
    request = models.ForeignKey(ChangeRequest, related_name='details',
                                on_delete=models.CASCADE)

    change_field = models.CharField(max_length=100)
    change_field_label = models.CharField(max_length=100)

    # old value and new value can have null=True
    # because we might need distinguish them
    # if the user wishes to give us empty value
    old_value = models.TextField(null=True)
    old_value_display = models.TextField(null=True)
    new_value = models.TextField(null=True)
    new_value_display = models.TextField(null=True)

    files = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )

    def __str__(self):
        return f"{self.request.user.full_name}"

    def _get_value_display(self, value, new=False):
        """
        :param value: value to display
        :param new: boolean whether to display new value or old value
        :return: display value
        """
        if not value:
            return value

        if self.is_filefield:
            if new and self.files:
                # if new file send file url
                return settings.BACKEND_URL + self.files.url
            return settings.BACKEND_URL + settings.MEDIA_URL + value
        elif self.is_datefield:
            from dateutil import parser
            try:
                return parser.parse(value).date()
            except ValueError:
                return None
        return value

    @cached_property
    def is_datefield(self):
        model = self.request.content_type.model_class()
        is_datefield = False
        for f in model._meta.fields:
            if f.name == self.change_field:
                if isinstance(f, models.DateField):
                    is_datefield = True
        return is_datefield

    @cached_property
    def is_filefield(self):
        model = self.request.content_type.model_class()
        return isinstance(model._meta.get_field(self.change_field),
                      models.FileField)

    @cached_property
    def new(self):
        return self._get_value_display(self.new_value, new=True)

    @cached_property
    def old(self):
        return self._get_value_display(self.old_value)
