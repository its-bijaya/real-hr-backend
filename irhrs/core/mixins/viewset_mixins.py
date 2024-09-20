"""@irhrs_docs"""
import operator
import re
from datetime import date, timedelta
from functools import reduce

import dateutil.parser as dateparser
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import (
    ValidationError as DjValidationError,
    ObjectDoesNotExist)
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import (
    GenericViewSet, ModelViewSet, ViewSet,
    ReadOnlyModelViewSet)

from irhrs.core.constants.organization import WORKLOG, GLOBAL
from irhrs.core.constants.payroll import SUPERVISOR, EMPLOYEE, APPROVED, DENIED
from irhrs.core.utils.common import (get_today, validate_permissions, validate_used_data)
from irhrs.event.models import Event
from irhrs.leave.models import MasterSetting
from irhrs.organization.models import Organization, FiscalYear, ApplicationSettings
from irhrs.permission.constants.permissions import (
    USER_PROFILE_PERMISSION,
    HAS_PERMISSION_FROM_METHOD, HRIS_PERMISSION)
from irhrs.permission.permission_classes import permission_factory
from irhrs.permission.utils.views import PermissionWithFilterMixin
from irhrs.training.models import Training
from irhrs.users.models import UserDetail, UserSupervisor

USER = get_user_model()
TEN_YEARS = relativedelta(years=10)
_HR, _USER, _SUPERVISOR = 'hr', 'user', 'supervisor'


# with permission and filter standard views
class HRSGenericAPIView(PermissionWithFilterMixin, GenericAPIView):
    pass


class HRSModelViewSet(PermissionWithFilterMixin, ModelViewSet):
    pass


class HRSViewSet(PermissionWithFilterMixin, ViewSet):
    pass


class HRSReadOnlyModelViewSet(PermissionWithFilterMixin, ReadOnlyModelViewSet):
    pass


class DisallowPatchMixin:
    """
    # TODO: accept method to disallow
    ViewSet mixin for disallowing patch methods
    """
    http_method_names = [
        'get', 'post', 'put', 'delete', 'head', 'options', 'trace'
    ]


class CreateViewSetMixin(PermissionWithFilterMixin,
                         mixins.CreateModelMixin,
                         GenericViewSet):
    """
    A viewset that provides  `create` action.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class DestroyViewSetMixin(PermissionWithFilterMixin,
                          mixins.DestroyModelMixin,
                          GenericViewSet):
    """
    A viewset that provides  `destory` action.
    """
    pass


class CreateDestroyViewsetMixin(PermissionWithFilterMixin,
                                mixins.CreateModelMixin,
                                mixins.DestroyModelMixin,
                                GenericViewSet):
    """
    A viewset that provides `create`, `destroy` action
    """
    pass



class CreateRetrieveUpdateDestroyViewSetMixin(PermissionWithFilterMixin,
                                              mixins.CreateModelMixin,
                                              mixins.RetrieveModelMixin,
                                              mixins.UpdateModelMixin,
                                              mixins.DestroyModelMixin,
                                              GenericViewSet):
    """
    A viewset that provides `retrieve`, `create`, `update` and
    `destroy` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class CreateRetrieveUpdateViewSetMixin(PermissionWithFilterMixin,
                                       mixins.CreateModelMixin,
                                       mixins.RetrieveModelMixin,
                                       mixins.UpdateModelMixin,
                                       GenericViewSet):
    """
    A viewset that provides `retrieve`, `create`, `update` and
    `destroy` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListCreateUpdateViewSetMixin(PermissionWithFilterMixin,
                                   mixins.ListModelMixin,
                                   mixins.CreateModelMixin,
                                   mixins.UpdateModelMixin,
                                   GenericViewSet):
    """
    A viewset that provides `list`, `create`, and `update` actions
    """
    pass


class ListCreateUpdateDestroyViewSetMixin(PermissionWithFilterMixin,
                                          mixins.ListModelMixin,
                                          mixins.CreateModelMixin,
                                          mixins.UpdateModelMixin,
                                          mixins.DestroyModelMixin,
                                          GenericViewSet):
    pass


class ListRetrieveUpdateDestroyViewSetMixin(PermissionWithFilterMixin,
                                            mixins.ListModelMixin,
                                            mixins.RetrieveModelMixin,
                                            mixins.UpdateModelMixin,
                                            mixins.DestroyModelMixin,
                                            GenericViewSet):
    """
    A viewset that provides `list`, `retrieve`, `update` and
    `destroy` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass

class ListRetrieveCreateDestroyViewSetMixin(PermissionWithFilterMixin,
                                            mixins.ListModelMixin,
                                            mixins.RetrieveModelMixin,
                                            mixins.CreateModelMixin,
                                            mixins.DestroyModelMixin,
                                            GenericViewSet):
    """
    A viewset that provides `list`, `retrieve`, `create` and
    `destroy` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """


class RetrieveUpdateViewSetMixin(PermissionWithFilterMixin,
                                 mixins.RetrieveModelMixin,
                                 mixins.UpdateModelMixin,
                                 GenericViewSet):
    """
    A viewset that provides `retrieve` and `update` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListCreateViewSetMixin(PermissionWithFilterMixin,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin,
                             GenericViewSet):
    """
    A viewset that provides `list` and `create` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListCreateDestroyViewSetMixin(PermissionWithFilterMixin,
                                    mixins.ListModelMixin,
                                    mixins.CreateModelMixin,
                                    mixins.DestroyModelMixin,
                                    GenericViewSet):
    """
    A viewset that provides `list` , `create` and `Destroy` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListRetrieveUpdateViewSetMixin(PermissionWithFilterMixin,
                                     mixins.ListModelMixin,
                                     mixins.RetrieveModelMixin,
                                     mixins.UpdateModelMixin,
                                     GenericViewSet):
    """
    A viewset that provides `list`, `retrieve` and `update` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class UpdateViewSetMixin(PermissionWithFilterMixin,
                         mixins.ListModelMixin,
                         mixins.UpdateModelMixin,
                         GenericViewSet):
    """
    A viewset that provides `list`, and `update` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListRetrieveDestroyViewSetMixin(PermissionWithFilterMixin,
                                      mixins.ListModelMixin,
                                      mixins.RetrieveModelMixin,
                                      mixins.DestroyModelMixin,
                                      GenericViewSet):
    """
    A viewset that provides `list`, `retrieve` and `destroy` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListCreateRetrieveViewSetMixin(PermissionWithFilterMixin,
                                     mixins.ListModelMixin,
                                     mixins.CreateModelMixin,
                                     mixins.RetrieveModelMixin,
                                     GenericViewSet):
    """
       A viewset that provides `list`, `create` and `retrieve` actions.

       To use it, override the class and set the `.queryset` and
       `.serializer_class` attributes.
       """
    pass


class ListCreateRetrieveUpdateViewSetMixin(PermissionWithFilterMixin,
                                           mixins.ListModelMixin,
                                           mixins.CreateModelMixin,
                                           mixins.RetrieveModelMixin,
                                           mixins.UpdateModelMixin,
                                           GenericViewSet):
    """
       A viewset that provides `list`, `create`, `retrieve` and `update` actions

       To use it, override the class and set the `.queryset` and
       `.serializer_class` attributes.
    """


class ListCreateRetrieveDestroyViewSetMixin(PermissionWithFilterMixin,
                                            mixins.ListModelMixin,
                                            mixins.CreateModelMixin,
                                            mixins.RetrieveModelMixin,
                                            mixins.DestroyModelMixin,
                                            GenericViewSet):
    """
       A viewset that provides `list`, `create`, `retrieve` and `delete` actions

       To use it, override the class and set the `.queryset` and
       `.serializer_class` attributes.
    """


class ListRetrieveViewSetMixin(PermissionWithFilterMixin,
                               mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               GenericViewSet):
    """
    A viewset that provides `list` and `retrieve` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListUpdateViewSetMixin(PermissionWithFilterMixin,
                             mixins.ListModelMixin,
                             mixins.UpdateModelMixin,
                             GenericViewSet):
    """
    A viewset that provides `list` and `update` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class RetrieveViewSetMixin(PermissionWithFilterMixin,
                           mixins.RetrieveModelMixin,
                           GenericViewSet):
    """
    A viewset that provides `retrieve` action.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class ListViewSetMixin(PermissionWithFilterMixin,
                       mixins.ListModelMixin,
                       GenericViewSet):
    """
           A viewset that provides `list` action

           To use it, override the class and set the `.queryset` and
           `.serializer_class` attributes.
        """
    pass


class CreateUpdateViewSetMixin(PermissionWithFilterMixin,
                               mixins.CreateModelMixin,
                               mixins.UpdateModelMixin,
                               GenericViewSet):
    pass


class CreateUpdateDeleteViewSetMixin(PermissionWithFilterMixin,
                                     mixins.CreateModelMixin,
                                     mixins.UpdateModelMixin,
                                     mixins.DestroyModelMixin,
                                     GenericViewSet):
    pass


class CreateDeleteViewSetMixin(PermissionWithFilterMixin,
                               mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               GenericViewSet):
    pass


class PastUserParamMixin:
    @cached_property
    def user_type(self):
        request = getattr(self, 'request', None)
        if request:
            is_hr = validate_permissions(
                request.user.get_hrs_permissions(
                    getattr(self, 'organization', None)
                ),
                HRIS_PERMISSION
            )
            user_status = request.query_params.get('user_status')
            if is_hr and user_status in ['past', 'all']:
                return user_status
        return 'current'


class PastUserFilterMixin(PastUserParamMixin):
    def get_queryset(self):
        qs = super().get_queryset()
        user_pks = list(USER.objects.all().current().values_list('pk', flat=True))
        if self.user_type == 'current':
            return USER.objects.filter(id__in=user_pks)
        elif self.user_type == 'past':
            return USER.objects.exclude(id__in=user_pks)

        return qs


class PastUserGenericFilterMixin(PastUserParamMixin):
    user_definition = None

    def get_queryset(self):
        qs = super().get_queryset()

        if self.user_type == 'current':
            user_pks = list(USER.objects.all().current().values_list('pk', flat=True))
            if self.user_definition:
                qs = qs.filter(**{
                    f"{self.user_definition if self.user_definition else ''}_id__in": user_pks})
            else:
                qs = qs.filter(**{"id__in": user_pks})

        elif self.user_type == 'past':
            user_pks = list(USER.objects.all().past().values_list('pk', flat=True))
            if self.user_definition:
                qs = qs.filter(**{
                    f"{self.user_definition if self.user_definition else ''}_id__in": user_pks})
            else:
                qs = qs.filter(**{"id__in": user_pks})

        return qs.filter()


class PastUserTimeSheetFilterMixin(PastUserGenericFilterMixin):
    user_definition = 'timesheet_user'


class MeetingMixin:
    _meeting = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.get_meeting()

    def get_meeting(self):
        if not self._meeting:
            event = self.kwargs.get('event_id')
            if event is not None:
                event = get_object_or_404(
                    Event.objects.only('id'), id=event
                )
                try:
                    self._meeting = event.eventdetail
                except:
                    return self._meeting
        return self._meeting

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['meeting'] = self.meeting
        return context

    def get_queryset(self):
        return super().get_queryset().filter(meeting=self.meeting)

    @cached_property
    def meeting(self):
        return self.get_meeting()


class OrganizationMixin:
    _organization = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.get_organization()

    def get_organization(self):
        if not self._organization:
            slug = self.kwargs.get('organization_slug')
            if slug is not None:
                self._organization = get_object_or_404(
                    self.organization_qs(), slug=slug
                )
        return self._organization

    @property
    def organization(self):
        return self.get_organization()

    @staticmethod
    def organization_qs():
        return Organization.objects.all()


class OrganizationCommonsMixin:
    organization_field = 'organization'

    def get_queryset(self):
        return super().get_queryset().filter(
            **{self.organization_field: self.get_organization()}
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context


class TrainingMixin:
    _training = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.get_training()

    def get_training(self):
        if not self._training:
            slug = self.kwargs.get('training_slug')
            if slug is not None:
                self._training = get_object_or_404(
                    Training, slug=slug
                )
        return self._training

    @property
    def training(self):
        return self.get_training()


class UserDetailMixin:
    # TODO @Ravi: Remove this mixin. No usage.
    """
    Returns user whenever kwargs has user_id to get user
    TO BE REMOVED
    """
    _userdetail = None

    def get_userdetail(self):
        # TODO: make this cached property
        if not self._userdetail:
            user_id = self.kwargs.get('user_id')
            if user_id is not None:
                self._userdetail = get_object_or_404(
                    UserDetail,
                    user_id=user_id
                )
        return self._userdetail


class UserDetailCommonsMixin:
    """
    TO BE REMOVED
    """

    def get_queryset(self):
        return self.queryset.filter(userdetail=self.get_userdetail())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['userdetail'] = self.get_userdetail()
        return context


class UserMixin:
    """Returns user when kwargs has user_id to get user"""
    _organization = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        _ = self.user

    def get_user_queryset(self):
        return USER.objects.all()

    @cached_property
    def user(self):
        user_id = self.kwargs.get('user_id')
        if user_id is not None:
            return get_object_or_404(
                self.get_user_queryset(),
                id=user_id
            )

    def get_organization(self):
        if not self._organization:
            if self.user:
                self._organization = self.user.detail.organization
        return self._organization

    @property
    def is_supervisor(self):
        if self.request.method.lower() == 'get' and \
            self.request.query_params.get('as') == 'supervisor':
            return self.user and self.user.id in self.request.user.subordinates_pks
        return False


class UserPermissionMixin(UserMixin):
    """

    """
    permission_classes = [permission_factory.build_permission(
        "ContactDetailPermission",
        allowed_to=[USER_PROFILE_PERMISSION, HAS_PERMISSION_FROM_METHOD]
    )]

    @property
    def mode(self):
        _mode = self.request.query_params.get('as')
        if _mode in (_HR, _USER, _SUPERVISOR):
            return _mode
        return USER

    def has_user_permission(self):
        if self.mode == _HR:
            return validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                USER_PROFILE_PERMISSION
            )
        return self.mode == _SUPERVISOR or self.is_current_user()

    def is_current_user(self):
        return self.request.user == self.user


class UserCommonsMixin(UserPermissionMixin):
    def get_queryset(self):
        as_hr = self.request.query_params.get('as') == 'hr'
        if not as_hr and self.request.user != self.user and not self.is_supervisor:
            self.permission_denied(self.request)
        return self.queryset.filter(user=self.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.user
        return context


class ParentFilterMixin:
    def filter_queryset(self, queryset):
        is_parent = self.request.query_params.get('is_parent')
        if is_parent in ["true", "false"]:
            is_parent = True if is_parent == "true" else False
            queryset = queryset.filter(parent__isnull=is_parent)
        return super().filter_queryset(queryset)


class DateRangeParserMixin:
    start_date_parsed = None
    end_date_parsed = None
    start_date_param = "start_date"
    end_date_param = "end_date"

    raise_on_invalid_dates = False

    # TODO@Ravi: Currently, +-10 years is taken for all date.
    # Remove this implementation, and return None,None. If none, do not build
    # filter query.

    @staticmethod
    def get_default_end_date():
        return get_today() + TEN_YEARS

    @staticmethod
    def get_default_start_date():
        return get_today() - TEN_YEARS

    def get_parsed_dates(self):
        if not (self.start_date_parsed and self.end_date_parsed):
            start_date = self.request.query_params.get(self.start_date_param)
            end_date = self.request.query_params.get(self.end_date_param)

            start_date_parsed = None
            end_date_parsed = None

            try:
                start_date_parsed = dateparser.parse(start_date)
                if isinstance(start_date_parsed, timezone.datetime):
                    start_date_parsed = start_date_parsed.date()
            except (TypeError, ValueError, OverflowError):
                if self.raise_on_invalid_dates and start_date is not None:
                    raise ValidationError({'detail': 'Invalid start date'})
            try:
                end_date_parsed = dateparser.parse(end_date)
                if isinstance(end_date_parsed, timezone.datetime):
                    end_date_parsed = end_date_parsed.date()
            except (TypeError, ValueError, OverflowError):
                if self.raise_on_invalid_dates and end_date is not None:
                    raise ValidationError({'detail': 'Invalid end date'})

            self.start_date_parsed = start_date_parsed or self.get_default_start_date()
            self.end_date_parsed = end_date_parsed or self.get_default_end_date()
        return self.start_date_parsed, self.end_date_parsed

    @cached_property
    def fiscal_year(self):
        organization = getattr(
            self,
            'organization',
            None
        )
        query_params = self.request.query_params
        if organization:
            fiscal_id = query_params.get('fiscal', '')
            if fiscal_id and fiscal_id.isdigit():
                fiscal = FiscalYear.objects.filter(
                    organization=organization,
                    id=fiscal_id
                ).first()
            else:
                fiscal = FiscalYear.objects.current(
                    organization=organization
                )
            return fiscal
        return

    @cached_property
    def fiscal_range(self):
        query_params = self.request.query_params
        fiscal_type = query_params.get('fiscal_type')
        if fiscal_type == 'fiscal':
            # return selected fiscal, or return current fiscal
            fiscal = self.fiscal_year
            if fiscal:
                return fiscal.applicable_from, fiscal.applicable_to
        elif fiscal_type == 'gregorian':
            year = query_params.get('year')
            if year and re.fullmatch('\d{4}', year):
                this_year = date(int(year), 1, 1)
                next_year = date(int(year) + 1, 1, 1) - timedelta(days=1)
                return this_year, next_year
        return self.get_parsed_dates()

    @cached_property
    def fiscal_name(self):
        query_params = self.request.query_params
        fiscal_type = query_params.get('fiscal_type')
        if fiscal_type == 'fiscal':
            fiscal = self.fiscal_year
            return fiscal.name if fiscal else None
        elif fiscal_type == 'gregorian':
            year = query_params.get('year')
            return year if year and year.isdigit() else 'no=year'
        return 'Undefined'


class HRSOrderingFilter:
    ordering_fields_map = {}

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        ascending = self.ordering_fields_map

        descending = dict()
        for order, value in ascending.items():
            if isinstance(value, str):
                descending.update({f"-{order}": f"-{value}"})
            elif isinstance(value, (list, tuple)):
                descending.update({
                    f"-{order}": [f"-{v}" for v in value]
                })

        ordering_map = {
            **ascending,
            **descending
        }
        query_order = self.request.query_params.get('ordering', '')
        order_by = [
            v for k, v in ordering_map.items() if k in query_order.split(',')
        ]

        ord_by = []
        for order in order_by:
            if isinstance(order, str):
                ord_by.append(order)
            elif isinstance(order, (list, tuple)):
                order_by.extend(order)
        if ord_by:
            qs = qs.order_by(*ord_by)
        return qs


class IStartsWithIContainsSearchFilter(SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get('search', '')

        search_fields = getattr(
            view, 'get_search_fields',
            lambda *x, **y: None
        )()
        if not search_fields:
            search_fields = getattr(
                view, 'search_fields', None
            )
        if not search_fields:
            return queryset

        # Because, unpacking dictionary directly into a query -> results in AND query,
        # following reduce is used to create an OR query.
        fil_s = reduce(
            operator.or_, [
                Q(**{f'{field}__istartswith': search}) for field in view.search_fields
            ]
        )
        fil_c = reduce(
            operator.or_,
            [
                Q(**{f'{field}__icontains': search}) for field in view.search_fields
            ]
        )
        queryset = queryset.filter(fil_c).annotate(
            order_value=Case(
                When(
                    fil_s,
                    then=Value(1),
                ), default=Value(0),
                output_field=IntegerField()
            )
        ).order_by(
            '-order_value',
            *search_fields
        )
        return queryset


class ActiveMasterSettingMixin:
    @cached_property
    def active_master_setting(self):
        qs = MasterSetting.objects.all()
        if hasattr(self, 'get_organization'):
            qs = qs.filter(
                organization=self.get_organization()
            )
        return qs.active().first()


class SupervisorQuerysetMixin:
    """
    Supervisor Queryset Mixin

    gives util method `get_supervisor_filtered_queryset`

    :cvar user_field --> String representing user_field
        Default is None and assumes queryset is of User Model.
    """
    user_field = None
    allow_non_supervisor_user = False
    immediate_only = False

    @property
    def user_expression(self):
        return f"{self.user_field}__" if self.user_field else ''

    def get_supervisor_filtered_queryset(self, queryset):
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict()
        fil.update(
            {
                f'{self.user_expression}detail__organization': self.get_organization()
            }
        )
        if supervisor_id:
            supervisor = self.get_supervisor()
            if supervisor:
                if self.immediate_only:
                    subordinates = UserSupervisor.objects.filter(
                        authority_order=1,
                        supervisor=supervisor
                    ).values_list(
                        'user', flat=True
                    )
                else:
                    subordinates = supervisor.subordinates_pks
                fil.update({
                    f'{self.user_expression}id__in': subordinates
                })
            else:
                # if supervisor does not match return none
                return queryset.none()

        queryset = self.select_essentials(queryset)

        return queryset.filter(
            **fil
        )

    @staticmethod
    def select_essentials(queryset):
        if hasattr(queryset, 'select_essentials'):
            return queryset.select_essentials()
        return queryset

    def get_supervisor(self):
        supervisor_id = self.request.query_params.get('supervisor')

        # If supervisor is user --> allow
        if supervisor_id == str(self.request.user.id):
            return self.request.user

        # if not allowed to non supervisor user return None
        if not self.allow_non_supervisor_user:
            return None

        # else allowed to non supervisor users
        try:
            return USER.objects.get(id=supervisor_id)
        except (TypeError, ValueError, DjValidationError, ObjectDoesNotExist):
            return None


class SupervisorQuerysetViewSetMixin(SupervisorQuerysetMixin,
                                     PastUserFilterMixin):
    """
    Use as SupervisorQueryset but it overrides get_queryset
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.get_supervisor_filtered_queryset(queryset)


class ModeFilterQuerysetMixin:
    allow_supervisor_filter = False
    permission_to_check = {
        'code': '0.00'
    }
    user_definition = ''

    def get_user_field(self, field):
        return self.user_definition + '__' + field if \
            self.user_definition else field

    def get_queryset(self):
        organization = getattr(self, 'organization', None)

        c_user = self.request.user
        mode = self.request.query_params.get('as')
        immediate = self.request.query_params.get('immediate') == 'true'

        if immediate:
            subordinates = set(
                UserSupervisor.objects.filter(
                    authority_order=1,
                    supervisor=c_user
                ).values_list('user', flat=True)
            )
        else:
            subordinates = c_user.subordinates_pks

        supervisor_as = str(self.request.query_params.get('supervisor'))
        # force to 'None' to directly check `isdigit()`

        supervisor_as = int(supervisor_as) if supervisor_as.isdigit() else None
        # back to number, to check 10 in {1,2,3..}

        supervisor_as = supervisor_as if self.allow_supervisor_filter else None
        # flag to allow or not such filters.

        if mode == 'supervisor':
            my_subs = self.request.user.subordinates_pks
            supervisor_as = supervisor_as if supervisor_as in my_subs else None
        elif mode != 'hr':
            supervisor_as = None

        supervisor_query = UserSupervisor.objects.filter(
            authority_order=1,
            supervisor=supervisor_as
        ).values_list('user', flat=True)

        permissions = [self.permission_to_check] if isinstance(
            self.permission_to_check,
            dict
        ) else self.permission_to_check
        fil = {
            self.get_user_field('detail__organization'): organization
        } if organization else {}

        if mode == 'hr':
            if validate_permissions(
                c_user.get_hrs_permissions(organization),
                *permissions
            ):
                if supervisor_as:
                    fil.update({
                        self.get_user_field(
                            'id__in'
                        ): supervisor_query
                    })
            else:
                # if not c_user.is_audit_user:
                raise PermissionDenied
        elif mode == 'supervisor':
            fil = {
                self.get_user_field('id__in'): subordinates,
                self.get_user_field('detail__organization'): organization
            } if not supervisor_as else {
                self.get_user_field('id__in'): supervisor_query,
                self.get_user_field('detail__organization'): organization
            }
        else:
            fil.update({
                self.get_user_field('id'): c_user.id
            })
        return super().get_queryset().filter(
            **fil
        )


class GetStatisticsMixin:
    """
    Automatically get the statistics based on the model field choices.
    """
    statistics_field = ''

    @property
    def statistics(self):

        filter_map = getattr(
            self, 'filter_map', None
        )
        if self.statistics_field in filter_map:
            res = filter_map.pop(self.statistics_field)
        else:
            res = None
        filter_queryset = getattr(self, 'filter_queryset')
        get_queryset = getattr(self, 'get_queryset')

        choices = get_queryset().model._meta.get_field(
            self.statistics_field
        ).choices
        ret = dict(filter_queryset(
            get_queryset()
        ).aggregate(
            **{
                k: Count(
                    'id',
                    filter=Q(
                        **{
                            self.statistics_field: k
                        }
                    )
                ) for k, v in choices
            }
        ))
        ret.update({
            'All': filter_queryset(
                get_queryset()
            ).aggregate(
                all_count=Count('id')
            ).get('all_count')
        })
        if res:
            filter_map[self.statistics_field] = res
            setattr(
                self, 'filter_map', filter_map
            )
        return ret


class WorkLogPermissionMixin:
    def check_permissions(self, request):
        super().check_permissions(request)
        organization = request.query_params.get(
            'organization'
        )

        if not organization:
            if not hasattr(request.user, 'detail'):
                self.permission_denied(
                    request,
                    message=f"Accessing worklog is forbidden."
                )
            else:
                organization = request.user.detail.organization.slug
        status = ApplicationSettings.objects.filter(
            organization__slug=organization,
            application=WORKLOG,
            enabled=False
        ).exists()
        if status:
            self.permission_denied(
                request,
                message=f"Accessing worklog is forbidden."
            )


class CreateListModelMixin:
    """
    reference from given link
    https://stackoverflow.com/questions/14666199/how-do-i-create-multiple-model-instances-with-django-rest-framework
    """

    def get_serializer(self, *args, **kwargs):
        """ if an array is passed, set serializer to many """
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        if isinstance(serializer.data, list):
            response_data = serializer.data[:]

        response_data = serializer.data
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ValidateUsedData:
    """
    Must have related_names else empty list will be returned from get_related_names method
    """
    related_names = []
    related_methods = ['put', 'patch', 'delete']

    def get_related_names(self):
        return self.related_names

    def get_related_methods(self):
        return self.related_methods

    def _validate_request(self, instance, request_type):
        if self.request.method.lower() in self.get_related_methods() and \
            validate_used_data(
                instance,
                related_names=self.get_related_names()
            ):
            raise ValidationError(
                {
                    "non_field_errors": [
                        _(
                            f'Unable to {request_type} this data. '
                            f'Some data are associated with this {instance._meta.verbose_name}.'
                        )
                    ]
                }
            )

    def perform_update(self, serializer):
        self._validate_request(serializer.instance, request_type='update')
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        self._validate_request(instance, request_type='delete')
        super().perform_destroy(instance)


class ApprovalSettingViewSetMixin:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval_setting = serializer.data
        if not isinstance(approval_setting, list):
            approval_setting = [approval_setting]

        is_valid, message = self._valid_approval_hierarchy(approval_setting)
        if not is_valid:
            return Response({'non_field_error': message}, status=status.HTTP_400_BAD_REQUEST)

        if len(serializer.data) < 1 or len(serializer.data) > 5:
            return Response(
                {
                    "non_field_error": "Approval Hierarchy can't be less than 1 or more than 5."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        self.delete_settings()
        return super().create(request, *args, **kwargs)

    def delete_settings(self):
        pass

    @staticmethod
    def _valid_approval_hierarchy(approval_settings):
        supervisor_list = [
            approve_by.get('supervisor_level') for approve_by in approval_settings
            if approve_by.get('approve_by') == SUPERVISOR
        ]
        employee_list = [
            approve_by.get('employee') for approve_by in approval_settings
            if approve_by.get('approve_by') == EMPLOYEE
        ]

        if supervisor_list and len(supervisor_list) != len(set(supervisor_list)):
            return False, "Approval Setting got similar supervisor level."

        if employee_list and len(employee_list) != len(set(employee_list)):
            return False, "Approval Setting got similar employee."
        return True, "Approval Setting got valid data."


class AdvanceExpenseRequestMixin:
    _expense = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.get_expense_request()

    def get_queryset(self):
        return super().get_queryset().filter(expense=self.expense_request)

    def get_expense_request(self):
        if not self._expense:
            id = self.kwargs.get('expense_id')
            if id is not None:
                self._expense = get_object_or_404(
                    self.expense_qs(), id=id
                )
        return self._expense

    @property
    def expense_request(self):
        return self.get_expense_request()

    def expense_qs(self):
        from irhrs.reimbursement.models import AdvanceExpenseRequest
        return AdvanceExpenseRequest.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['expense'] = self.expense_request
        return context


class CommonApproverViewSetMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.organization
        return context

    @property
    def mode(self):
        mode = self.request.query_params.get('as', 'user')
        if mode not in ['user', 'hr', 'approver']:
            return 'user'
        return mode

    def has_user_permission(self):
        if self.request.user.is_anonymous:
            return False

        if self.mode == 'hr':
            return validate_permissions(
                self.request.user.get_hrs_permissions(self.organization),
                *self.get_permission_for_org_notification()
            )
        elif self.mode == 'user':
            return self.request.user.detail.organization == self.organization

        return True

    def get_queryset(self):
        base_qs = self.queryset.filter(employee__detail__organization=self.organization)
        if self.mode == 'hr':
            queryset = base_qs
        elif self.mode == 'approver':
            # filters request for current approver only
            queryset = self.queryset.filter(
                Q(recipient=self.request.user) |
                Q(approvals__user=self.request.user,
                  approvals__status__in=[APPROVED, DENIED])
            )
        else:
            queryset = base_qs.filter(employee=self.request.user)
        return queryset.select_related(
            'employee', 'employee__detail', 'employee__detail__organization',
            'employee__detail__job_title', 'recipient', 'recipient__detail',
            'recipient__detail__organization', 'recipient__detail__job_title'
        ).distinct()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['stats'] = self.statistics
        return response
