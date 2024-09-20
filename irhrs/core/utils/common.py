# @irhrs_docs
import os
import re
import uuid
from datetime import datetime, time

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Func
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.utils.urls import replace_query_param

from irhrs.core.constants.user import MALE, FEMALE
from irhrs.core.utils.filters import get_applicable_filters


class DummyObject:
    """A dummy object with attributes passed in __init__"""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_uuid_filename(filename):
    """
    rename the file name to uuid4 and return the
    path
    """
    ext = filename.split('.')[-1]
    return "{}.{}".format(uuid.uuid4().hex, ext)


def get_upload_path(instance, filename):
    return os.path.join(f"uploads/{instance.__class__.__name__.lower()}",
                        get_uuid_filename(filename))


def get_pretty_slug(instance):
    """
    Returns readable title/name and browse able slug.
    :param instance: An instance of slug-based model.
    :return: dictionary of name/title and slug.
    """
    val = dict()
    if not instance:
        return val
    if hasattr(instance, 'name'):
        val.update({'name': instance.name})
    elif hasattr(instance, 'title'):
        val.update({'title': instance.title})
    val.update({'slug': instance.slug})
    return val


def get_complete_url(url='', att_type=None):
    """
    Returns complete uri of the attachment, by prefixing the server url.
    :param url: URL of attachments from PROJECT_ROOT
    :att_type: MEDIA_URL or STATIC_URL
    :return: Complete URL
    """
    attachment_type = {
        'media': settings.MEDIA_URL,
        'static': settings.STATIC_URL,
        None: ''
    }
    if not hasattr(settings, 'BACKEND_URL'):
        import logging
        logging.warning('The server url has not been set.')
    server_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
    return f'{server_url}{attachment_type.get(att_type)}{url}'


def get_today(with_time=False, reset_hours=False):
    """
    Returns today's date.

    Setting `with_time` to True returns a datetime.datetime object.
    Setting `with_time` to False returns a datetime.date object.

    Setting `reset_hours` to True resets the time to the first second of the day but
    `with_time` must be set to True while using `reset_hours`.
    """
    datetime_now = timezone.now().astimezone() if with_time else timezone.now().astimezone().date()
    if reset_hours and with_time:
        datetime_now = datetime_now.replace(hour=0, minute=0, second=1)
    return datetime_now

def get_tomorrow(with_time=False):
    return get_today(with_time) + timezone.timedelta(days=1)


def get_yesterday(with_time=False):
    return get_today(with_time) - timezone.timedelta(days=1)


def validate_unique(serializer_instance, data: dict, constraints: iter):
    unique_together_constraints = constraints
    fil = {
        constraint: data.get(
            constraint
        ) for constraint in unique_together_constraints
    }
    exclude = {'id': serializer_instance.instance.id} if \
        serializer_instance.instance else {}

    if serializer_instance.Meta.model.objects.exclude(**exclude).filter(
        **fil).exists():
        raise ValidationError(
            f"The {serializer_instance.Meta.model._meta.verbose_name.title()} "
            f"already exists for the given data."
        )


def apply_filters(qp, filter_map, qs):
    """
    filter query according query params
    :param qp: query_params
    :param filter_map: {
            "filter_key": "model_filter_map"
        }
    :param qs: queryset
    :return: filtered queryset
    """
    try:
        return qs.filter(**get_applicable_filters(qp, filter_map))
    except (ValueError, TypeError):
        # if any error occurs return blank queryset
        return qs.none()


def get_supervisor(user_object):
    """
    Returns First Level Supervisor for the user.
    :param user_object:
    :return:
    """
    return getattr(
        user_object.supervisors.order_by('authority_order').first(),
        'supervisor'
    )


def relative_delta_gte(relative_delta_1, relative_delta_2):
    """
    Returns the comparison between relative delta
    :param relative_delta_1:
    :param relative_delta_2:
    :return:
    """
    base_date = timezone.now().date()
    return (base_date + relative_delta_1) >= (base_date + relative_delta_2)


def combine_aware(date, time):
    _dt = datetime.combine(date, time)
    _dt = timezone.make_aware(_dt)
    return _dt.astimezone()


def get_possessive_determiner(self_user, relative):
    if self_user == relative:
        return "your"

    if relative.detail.gender == MALE:
        return "his"

    if relative.detail.gender == FEMALE:
        return "her"

    # for other gender
    return "their"


def get_random_class_name():
    import uuid
    return str(uuid.uuid4().hex[:6].upper())


def validate_full_name(full_name):
    pattern = re.compile('[a-zA-Z ]{4,}')
    if pattern.fullmatch(full_name):
        return full_name
    raise ValidationError(
        "The full name can only contain alphabets and spaces and must be 4 "
        "characters long."
    )


def modify_field_attributes(**kwargs):
    def wrap(cls):
        for k, v in kwargs.items():
            for kk, vv in v.items():
                setattr(cls._meta.get_field(k), kk, vv)
        return cls

    return wrap


def timeout_for_midnight():
    """
    Util for expiring cache on midnight.
    Used in calculation of User's Tag, that is updated everyday.
    :return:
    """
    return int((combine_aware(
        timezone.now().date() + timezone.timedelta(days=1),
        time(0, 0)
    ) - timezone.now()).total_seconds())


def format_timezone(dt, format_string="%Y-%m-%d %I:%M %p"):
    """
    Returns a date formatted after its converted to datetime
    :param dt: datetime (in UTC)
    :param format_string: string format to be formatted to
    :return: formatted timestamp
    """
    return dt.astimezone().strftime(format_string)


def stringify_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '{:02d}:{:02d}:{:02d}'.format(h, m, s)


def humanize_interval(interval, absolute=True):
    if not interval:
        return "00:00:00"
    elif isinstance(interval, timezone.timedelta):
        total_seconds = interval.total_seconds()
        value = abs(total_seconds) if absolute else total_seconds
        return stringify_seconds(int(value))
    elif isinstance(interval, float):
        return stringify_seconds(int(interval))
    elif isinstance(interval, int):
        return stringify_seconds(interval)
    return interval


def is_request_read_only():
    from irhrs.core.middlewares.base import CurrentMethodMiddleware
    return CurrentMethodMiddleware.get_method() in SAFE_METHODS


def validate_permissions(
    user_permissions,
    *permission_list
):
    initial_permissions = set(
        map(lambda perm: perm.get('code'), permission_list)
    )
    initial_permissions = {
        f"{code.split('.')[0]}.00" for code in initial_permissions
    }.union(
        initial_permissions
    )
    request_is_read_only = is_request_read_only()
    if request_is_read_only:
        initial_permissions = {
            f"{code.split('.')[0]}.99" for code in initial_permissions
        }.union(
            initial_permissions
        )
    return bool(
        set(user_permissions).intersection(
            initial_permissions
        )
    )


def generate_next_url(request, count):
    max_size = settings.REST_FRAMEWORK.get('PAGE_SIZE')
    if count > max_size:
        url = request.build_absolute_uri()
        url = replace_query_param(url, "limit", max_size)
        url = replace_query_param(url, "offset", max_size)
    else:
        url = None
    return url


def _validate_uniqueness(self, queryset, fil):
    """
    This is used to verify whether any field is unique and also
    checks case sensitivity of that field.

    :param self: object parameter of calling class
    :param queryset: queryset upon which filter must be applied
    :param fil: filter that need to be applied
    :return:
    """
    qs = queryset.filter(
        **fil
    )
    if self.instance:
        qs = qs.exclude(
            pk=self.instance.pk
        )
    return qs.exists()


def extract_documents(initial_data, file_field='attachment', filename_field=None):
    documents = []
    data = dict(initial_data)
    for key in data.copy():
        if key.startswith(file_field):
            document = data.get(key)
            if document:
                if not isinstance(document[0], InMemoryUploadedFile):
                    continue
                try:
                    documents.append({
                        file_field: document[0],
                        **({filename_field: document[0].name[:255]} if filename_field else {})
                    })
                except TypeError:
                    documents.append({
                        file_field: document,
                        **({filename_field: document.name[:255]} if filename_field else {})
                    })
    return documents


def extract_documents_with_caption(initial_data, file_field='attachment',
                                   filename_field='name'):
    documents = []
    captions = []
    data = dict(initial_data)
    for key in data.copy():
        if key.startswith(file_field):
            document = data.get(key)
            if document:
                if not isinstance(document[0], InMemoryUploadedFile):
                    continue
                try:
                    documents.append(document[0])
                except TypeError:
                    documents.append(document)
        elif key.startswith(filename_field):
            caption = data.get(key)
            if caption:
                try:
                    captions.append(caption[0])
                except (TypeError, IndexError):
                    captions.append(caption)

    documents_with_caption = []
    for index, document in enumerate(documents):
        try:
            data = {
                file_field: document,
                filename_field: captions[index]
            }
        except IndexError:
            data = {
                file_field: document,
                filename_field: f'file{index}'
            }
        documents_with_caption.append(data)
    return documents_with_caption


def get_related_names(instance, exclude_related_names=None):
    related_names = []
    if not exclude_related_names:
        exclude_related_names = []

    for x in instance._meta.related_objects:
        # gets related name
        name = x.related_name
        if not name:
            # gets class name if related name is not available
            try:
                name = str(x.field).split('.')[-2].lower() + '_set'
            except IndexError:
                continue
        if name and name not in exclude_related_names:
            related_names.append(name)
    return related_names


def validate_used_data(instance, related_names=None):
    """
    Validates whether instance of model has been used or not

    Below given code generated related_object name.

    ..code-block: python
            for x in instance._meta.related_objects:
                # gets related name
                name = x.related_name
                if not name:
                    # gets class name if related name is not available
                    try:
                        name = str(x.field).split('.')[-2].lower() + '_set'
                    except IndexError:
                        continue
                if name and name not in exclude_related_names:
                    related_names.append(name)

    :param instance: Object of any model
    :param related_names: list of related model name
    :type related_names: list
    :return:
    """
    for related_name in related_names:
        if getattr(instance, related_name).exists():
            return True
    return False


def get_common_queryset(self, queryset, fil=None):
    """
    Implement supervisor filter

    :param self: object of the class (self)
    :param queryset: Queryset
    :param fil: other filters
    :type fil: Dict
    :return: queryset
    """
    supervisor_id = self.request.query_params.get('supervisor')
    if not fil:
        fil = dict()

    if supervisor_id:
        if supervisor_id == str(self.request.user.id):
            fil.update({
                'id__in':
                    self.request.user.subordinates_pks
            })
        else:
            return queryset.none()
    return queryset.filter(**fil)


def is_supervisor_of(user, supervisor):
    from irhrs.core.utils.subordinates import find_immediate_subordinates
    return user.id in find_immediate_subordinates(supervisor)


class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'
