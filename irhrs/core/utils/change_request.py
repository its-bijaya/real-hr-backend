"""@irhrs_docs"""
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.db.models import ForeignKey, ManyToManyField, OneToOneField, \
    FileField
from django.db.models.fields.reverse_related import ForeignObjectRel
from rest_framework.exceptions import ValidationError

from irhrs.core.constants.common import HRIS
from irhrs.core.constants.user import PENDING, APPROVED
from irhrs.core.utils.common import DummyObject, validate_permissions
from irhrs.core.utils.user_activity import create_user_activity
from irhrs.notification.utils import notify_organization
from irhrs.permission.constants.permissions import USER_PROFILE_PERMISSION, HRIS_PERMISSION, \
    HRIS_CHANGE_REQUEST_PERMISSION
from irhrs.users.models.change_request import ChangeRequest, \
    ChangeRequestDetails

EXCLUDE_FIELDS = ['pk', 'id', 'created_by', 'modified_by',
                  'created_at', 'modified_at', 'slug']
# The `change_request_validator` is driven with the following logic:
# If `multiple_requests` is True, User can send multiple change requests for it.
# The `unique_fields` will test for the pending and approved requests.
# If there are no unique fields, user has no restriction on new data.
# If there are unique fields, there has to be an integrity in database.
# Examples include: There can only be 1 temporary and 1 permanent address.
# However, two Change Requests should be available to send.
# For Language there can only be 1 native & all title must be unique.
# For Past Exp/Training/Volunteer Exp/Social Activity -> title must be unique.
CHANGE_REQUEST_VALIDATOR = {
    'usercontactdetail': {
        'multiple_requests': True,
        'unique_fields': ['email', 'number']
    },
    'userdocument': {
        'multiple_requests': True,
        'unique_fields': None
    },
    'useraddress': {
        'multiple_requests': True,
        'unique_fields': ['address_type']
    },
    'usereducation': {
        'multiple_requests': True,
        'unique_fields': None
    },
    'userpastexperience': {
        'multiple_requests': True,
        'unique_fields': ['title']
    },
    'usertraining': {
        'multiple_requests': True,
        'unique_fields': ['name']
    },
    'uservolunteerexperience': {
        'multiple_requests': True,
        'unique_fields': ['title']
    },
    'userlanguage': {
        'multiple_requests': True,
        'unique_fields': ['name', 'native']
    },
    'usersocialactivity': {
        'multiple_requests': True,
        'unique_fields': ['title']
    },
    'userinsurance': {
        'multiple_requests': True,
        'unique_fields': None
    }
}


def get_change_request_frontend_url(organization):
    return f"/admin/{organization.slug}/hris/change-requests"


def get_filename(file_instance):
    return file_instance.name.split("/")[-1] if file_instance else file_instance


def send_change_request(request_user, user):
    """ Determine whether to send change request or not"""
    if validate_permissions(
        request_user.get_hrs_permissions(
            user.detail.organization
        ),
        USER_PROFILE_PERMISSION,
        HRIS_PERMISSION,
        HRIS_CHANGE_REQUEST_PERMISSION,
    ):
        return False
    if request_user == user:
        return True
    return False


def get_deleted_data(instance):
    model_class = instance.__class__()
    valid_fields = []
    old_data = dict()

    for field in model_class._meta.get_fields(include_parents=False):
        if isinstance(field, ForeignObjectRel):
            # ignore reverse relations for now
            continue
        if field.name in EXCLUDE_FIELDS:
            continue
        valid_fields.append(field)

    for field in valid_fields:
        old_value = getattr(instance, field.name)

        if isinstance(field,
                      (ForeignKey, OneToOneField)):
            old_data.update({
                field.name: {
                    "old_value": old_value.pk if old_value else None,
                    "new_value": None,
                    "old_value_display": str(old_value) if old_value
                    else None,
                    "new_value_display": None,
                }
            })
        elif isinstance(field, ManyToManyField):
            old_pks = []
            old_value_displays = []

            if old_value:
                for ov in old_value.all():
                    old_pks.append(ov.pk)
                    old_value_displays.append(str(ov))

            old_data.update({
                field.name: {
                    "old_value": old_pks,
                    "old_value_display": ', '.join(old_value_displays),
                    "new_value": None,
                    "new_value_display": None
                }
            })
        elif isinstance(field, FileField):
            old_data.update({
                field.name: {
                    "old_value": old_value,
                    "new_value": None,
                    "old_value_display": get_filename(old_value),
                    "new_value_display": None,
                    "files": None,
                }
            })
        else:
            old_data.update({
                field.name: {
                    "old_value": old_value,
                    "new_value": None,
                    "old_value_display": str(old_value),
                    "new_value_display": None
                }
            })

    return old_data


def get_changes(new_data, instance, show_all_changes=True):
    """ get changes from new data and old instance"""
    changes = dict()

    model_class = instance.__class__()
    valid_fields = []
    fields = new_data.keys()

    for field in model_class._meta.get_fields(include_parents=False):
        if isinstance(field, ForeignObjectRel):
            # ignore reverse relations for now
            continue
        if field.name in EXCLUDE_FIELDS:
            continue

        valid_fields.append(field)

    for field in valid_fields:
        if field.name in fields:
            # field is in new data

            old_value = getattr(instance, field.name)
            new_value = new_data.get(field.name)

            if not (old_value or new_value):
                continue
            if show_all_changes or old_value != new_value:
                if isinstance(field,
                              (ForeignKey, OneToOneField)):
                    changes.update({
                        field.name: {
                            "old_value": old_value.pk if old_value else None,
                            "new_value": new_value.pk if new_value else None,
                            "old_value_display": str(old_value) if old_value
                            else None,
                            "new_value_display": str(new_value) if new_value
                            else None,
                        }
                    })
                elif isinstance(field, ManyToManyField):
                    old_pks = []
                    old_value_displays = []
                    new_pks = []
                    new_value_displays = []

                    if old_value:
                        for ov in old_value.all():
                            old_pks.append(ov.pk)
                            old_value_displays.append(str(ov))

                    if new_value:
                        for nv in new_value:
                            new_pks.append(nv.pk)
                            new_value_displays.append(str(nv))

                    if set(old_pks) != set(new_pks):
                        changes.update({
                            field.name: {
                                "old_value": old_pks,
                                "old_value_display": ', '.join(
                                    old_value_displays
                                ),
                                "new_value": new_pks,
                                "new_value_display": ', '.join(
                                    new_value_displays
                                ),
                            }
                        })

                elif isinstance(field, FileField):
                    changes.update({
                        field.name: {
                            "old_value": old_value,
                            "new_value": new_value,
                            "old_value_display": get_filename(old_value),
                            "new_value_display": new_value,
                            "files": new_value,
                        }
                    })
                else:
                    changes.update({
                        field.name: {
                            "old_value": old_value,
                            "new_value": new_value,
                            "old_value_display": old_value,
                            "new_value_display": new_value
                        }
                    })

    return changes


def create_add_change_request(user, model_class, data: dict, category="", approved=False):
    """
    change request for creating new record
    """
    content_type = ContentType.objects.get_for_model(model_class)
    cr_data = {
        'user': user,
        'content_type': content_type,
        'category': category
    }
    message_string = "sent a Change Request."
    with transaction.atomic():
        cr = ChangeRequest.objects.create(**cr_data)
        if approved:
            cr.status = APPROVED
            cr.save()
            message_string = "made change on profile."

        details = list()
        for field_name, value in data.items():
            if value:
                details_data = {
                    'request': cr,
                    "old_value": None,
                    "old_value_display": None,
                    "change_field": field_name,
                    "change_field_label": field_name
                }

                try:
                    field = model_class._meta.get_field(field_name)
                except FieldDoesNotExist:
                    continue

                if isinstance(field, (ForeignKey, OneToOneField)):
                    details_data.update({
                        'new_value': value.id,
                        'new_value_display': str(value)
                    })
                elif isinstance(field, ManyToManyField):
                    new_pks = []
                    new_value_displays = []

                    if value:
                        for nv in value:
                            new_pks.append(nv.pk)
                            new_value_displays.append(str(nv))

                    details_data.update({
                        "new_value": new_pks,
                        "new_value_display": ', '.join(new_value_displays),
                    })

                elif isinstance(field, FileField):
                    details_data.update({
                        "new_value": value,
                        "new_value_display": value,
                        "files": value,
                    })
                else:
                    details_data.update({
                        'new_value': value,
                        'new_value_display': value
                    })

                details.append(ChangeRequestDetails(
                    **details_data
                ))
        ChangeRequestDetails.objects.bulk_create(details)

    create_user_activity(
        actor=user,
        message_string=message_string,
        category=HRIS
    )
    organization = user.detail.organization
    notification_text = f"{user.full_name} has sent a change request."
    notify_organization(
        actor=user,
        action=user,
        text=notification_text,
        organization=organization,
        url=get_change_request_frontend_url(organization),
        permissions=[
            HRIS_PERMISSION,
            HRIS_CHANGE_REQUEST_PERMISSION
        ]
    )


def create_update_change_request(user, obj, changes: dict, category="", approved=False):
    """ change request for updating existing request"""
    message_string = f"sent a Change Request."
    request = ChangeRequest.objects.create(
        user=user,
        change_object=obj,
        category=category
    )
    for change_field, change in changes.items():
        change_copy = {
            "change_field": change_field,
            "old_value": change.get("old_value"),
            "new_value": change.get("new_value"),
        }
        if not ChangeRequestDetails.objects.filter(
            request__user=user,
            request__status=PENDING,
            **change_copy
        ).exists():
            assert hasattr(obj, change_field), f"{obj.__class__} has no" \
                                               " attribute" \
                                               f" {change_field}"
            ChangeRequestDetails.objects.create(
                change_field=change_field,
                change_field_label=change_field.title(),
                request=request,
                **change
            )
        else:
            ChangeRequestDetails.objects.create(
                change_field=change_field,
                change_field_label=change_field.title(),
                request=request,
                **change
            )
        if approved:
            request.status = APPROVED
            request.save()
            message_string = "made change on profile."

    create_user_activity(
        actor=user,
        message_string=message_string,
        category=HRIS
    )
    organization = user.detail.organization
    notification_text = f"{user.full_name} has sent a change request."
    notify_organization(
        actor=user,
        action=user,
        text=notification_text,
        organization=organization,
        url=get_change_request_frontend_url(organization),
        permissions=[
            HRIS_PERMISSION,
            HRIS_CHANGE_REQUEST_PERMISSION
        ]
    )


def create_delete_change_request(user, obj, category=""):
    if obj:
        request = ChangeRequest.objects.create(
            user=user,
            change_object=obj,
            is_deleted=True,
            category=category
        )
        deleted_data = get_deleted_data(obj)
        for field_name, value in deleted_data.items():
            ChangeRequestDetails.objects.create(
                change_field=field_name,
                change_field_label=field_name.title(),
                request=request,
                **value
            )

        create_user_activity(
            actor=user,
            message_string=f"sent a Change Request.",
            category=HRIS
        )
        organization = user.detail.organization
        notification_text = f"{user.full_name} has sent a change request."
        notify_organization(
            actor=user,
            action=user,
            text=notification_text,
            organization=organization,
            url=get_change_request_frontend_url(organization),
            permissions=[
                HRIS_PERMISSION,
                HRIS_CHANGE_REQUEST_PERMISSION
            ]
        )


class ChangeRequestSerializerClass:
    """

    """

    def __init__(self, serializer_class, user):
        # change request serializer
        self.__cr_serializer = type(
            f"ChangeRequest{serializer_class.__name__}",
            (serializer_class,),
            {
                "create": self.get_create_method(user),
                "update": self.get_update_method(user),
                "validate": self.get_validate_method(user, serializer_class),
            }
        )

    @staticmethod
    def get_validate_method(user, serializer_class):
        def validate(self, attrs):
            ser = serializer_class(
                instance=self.instance,
                data=self.initial_data,
                context=self.context
            )
            ser.is_valid(raise_exception=True)
            attrs = ser.validated_data
            ctype = ContentType.objects.get_for_model(self.Meta.model)
            category = self.Meta.model._meta.verbose_name.replace(
                "user ", "").title()

            # For create request check content type
            if not self.instance and ChangeRequest.objects.filter(
                user=user, status=PENDING, content_type=ctype
            ):
                key = self.Meta.model.__name__.lower()
                allowed = CHANGE_REQUEST_VALIDATOR.get(key, {}).get(
                    'multiple_requests'
                )
                if allowed:
                    unique_fields = CHANGE_REQUEST_VALIDATOR.get(key).get(
                        'unique_fields'
                    ) or list()
                    if not unique_fields:
                        # No Constraint over data
                        return attrs

                    base_qs = ChangeRequestDetails.objects.filter(
                        change_field__in=unique_fields,
                        request__in=ChangeRequest.objects.filter(
                            user=user,
                            status=PENDING,
                            content_type=ctype
                        )
                    )
                    pending_change_request_values = set(
                        base_qs.values_list(
                            'new_value', flat=True
                        )
                    )

                    def is_unique(unq_field):
                        value = attrs.get(unq_field)
                        return value and str(value) in pending_change_request_values

                    conflicts = {
                        unique_field: is_unique(unique_field)
                        for unique_field in unique_fields
                    }
                    if not any(conflicts.values()):
                        return attrs
                    validation_error = dict()
                    for field, conflict in conflicts.items():
                        if not conflict:
                            continue
                        validation_error.update({
                            field: f"The field `{field}` has a pending Change "
                                   f"Request for value `{attrs.get(field)}`"
                        })
                    raise ValidationError(validation_error)
                raise ValidationError(
                    f"A pending change request for {category} already exists. "
                    "Can not send another request until previous request is "
                    "acted."
                )
            return attrs

        return validate

    @staticmethod
    def get_create_method(user):
        def create(self, validated_data):
            # if serializer has defined its own before create, call it
            if hasattr(self, 'before_create'):
                validated_data = self.before_create(validated_data,
                                                    change_request=True)

            validated_data.update({'user': user})
            create_add_change_request(
                user, self.Meta.model, data=validated_data,
                category=self.Meta.model._meta.verbose_name.replace(
                    "user ", "").title()
            )
            return DummyObject(**validated_data)

        return create

    @staticmethod
    def get_update_method(user):
        def update(self, instance, validated_data):
            # if serializer has defined its own before update, call it
            if hasattr(self, 'before_update'):
                validated_data = self.before_update(instance, validated_data,
                                                    change_request=True)

            changes = get_changes(instance=instance, new_data=validated_data)

            if changes:
                create_update_change_request(
                    user, instance, changes,
                    category=self.Meta.model._meta.verbose_name.replace(
                        "user ", "").title())
            return DummyObject(**validated_data)

        return update

    def __call__(self, *args, **kwargs):
        return self.__cr_serializer


class NoCreateChangeRequestSerializerClass(ChangeRequestSerializerClass):
    """
    Change Request where create is handled through `Update` method.
    Used in cases of `Legal` and `Medical` Info.
    """

    def __init__(self, serializer_class, user):
        # change request serializer
        super().__init__(serializer_class, user)
        self.__cr_serializer = type(
            f"ChangeRequest{serializer_class.__name__}",
            (serializer_class,),
            {
                "create": self.get_update_method(user),
                "update": self.get_update_method(user),
                "validate": self.get_validate_method(user, serializer_class),
            }
        )
