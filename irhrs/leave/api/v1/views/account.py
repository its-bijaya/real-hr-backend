from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Exists, OuterRef
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, OrganizationCommonsMixin,
    ListViewSetMixin, ListCreateViewSetMixin, HRSOrderingFilter, UserMixin,
    ListRetrieveViewSetMixin, CreateViewSetMixin, GetStatisticsMixin)
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.leave.api.v1.permissions import LeavePermission, \
    LeaveAccountPermission, LeaveAccountHistoryPermission, UserLeavePermission, UserLeaveReportPermission, \
    LeaveMasterSettingPermission, LeaveAssignPermission
from irhrs.leave.api.v1.serializers.account import (
    UserLeaveAssignSerializer, LeaveAccountHistorySerializer,
    LeaveAccountSerializer,
    LeaveUserSerializer, LeaveAccountBulkUpdateSerializer,
    LeaveAccountListSerializer,
    BulkMigrateOldAccountSerializer)
from irhrs.leave.api.v1.serializers.leave_request import \
    UserLeaveRequestStatisticsSerializer
from irhrs.leave.constants.model_constants import LEAVE_REQUEST_STATUS, ALL
from irhrs.leave.models import LeaveAccount, LeaveRequest, LeaveRule, \
    LeaveAccountHistory, MasterSetting
from irhrs.leave.tasks import get_active_master_setting
from irhrs.leave.utils.balance import \
    get_applicable_leave_types_for_organization
from irhrs.permission.constants.permissions import LEAVE_PERMISSION, LEAVE_BALANCE_PERMISSION, OFFLINE_LEAVE_PERMISSION
from irhrs.users.models import UserDetail

User = get_user_model()


class UserLeaveAssignViewSet(OrganizationMixin,
                             OrganizationCommonsMixin,
                             HRSOrderingFilter,
                             ListCreateViewSetMixin):
    """
    list:
    ---
    Get list of users and filter them to assign leave rules

    *Note: can_assign explains whether user can be assigned with given leave
    rule*

    filters
    ---

        search=search_name -- Searches by users name
        status=Assigned or Unassigned
        leave_rule=rule -- Leave Rule **REQUIRED**
        ethnicity=[ethnicity_slug1, ethnicity_slug2,..] -- Ethnicity Slugs
        religion=[religion_slug1, religion_slug2,..] -- Religion Slugs
        division=[division_slug1, division_slug2] -- User division slug
        branch=[branch_slug1, branch_slug2] -- User branch slug

    ordering
    ---

        full_name


    create:
    ---

    Assign/Remove Employees with leave rule

    data sample

        {
            "users": ["user_id1", "user_id2", "user_id3", ...],
            "action": "Assign", // options are "Assign"/"Remove"
            "leave_rule": "rule_id",
        }

    """
    serializer_class = LeaveUserSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, FilterMapBackend)
    filter_map = {
        'username': 'user__username',
    }
    search_fields = (
        'user__first_name',
        'user__middle_name',
        'user__last_name',
        'user__username'
    )
    ordering_fields_map = {
        'full_name': (
            'user__first_name', 'user__middle_name', 'user__last_name'
        )
    }
    permission_classes = [LeaveAssignPermission]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserLeaveAssignSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return UserDetail.objects.filter(
            organization=self.get_organization(),
            user__attendance_setting__isnull=False
        ).current()

    def filter_from_leave_type(self, queryset):
        """
        This filter auto-excludes user according to the criteria in leave type.
        Eg: Gender: [Male, Female, Others, All]
            Marital Status: [Married, Unmarried, All]
        :return:
        """
        rule = self.get_rule()
        gender_filter = rule.leave_type.applicable_for_gender
        marital_filter = rule.leave_type.applicable_for_marital_status
        if gender_filter != ALL:
            queryset = queryset.filter(
                gender=gender_filter
            )
        if marital_filter != ALL:
            queryset = queryset.filter(
                marital_status=marital_filter
            )
        return queryset

    def filter_queryset(self, queryset):
        rule = self.get_rule()
        if not rule:
            return queryset.none()
        leave_type_id = rule.leave_type_id
        queryset = super().filter_queryset(queryset)
        queryset = self.filter_from_leave_type(queryset)
        status = self.request.query_params.get('status')
        if status in ['Assigned', 'Unassigned']:
            if status == 'Assigned':
                queryset = queryset.annotate(
                    can_assign=~Exists(
                        LeaveAccount.objects.filter(
                            rule=rule,
                            user_id=OuterRef('user_id'),
                            is_archived=False
                        )
                    )
                ).filter(can_assign=False)
            else:
                queryset = queryset.annotate(
                    can_assign=~Exists(
                        LeaveAccount.objects.filter(
                            rule__leave_type_id=leave_type_id,
                            user_id=OuterRef('user_id'),
                            is_archived=False
                        )
                    )
                ).filter(can_assign=True)
        queryset = queryset.filter(**self.get_filters())
        return queryset

    def get_filters(self):
        fil = {}
        ethnicity = self.request.query_params.getlist('ethnicity')
        if ethnicity and ethnicity != [""]:
            fil.update({'ethnicity__slug__in': ethnicity})

        religion = self.request.query_params.getlist('religion')
        if religion and religion != [""]:
            fil.update({
                'religion__slug__in': religion
            })

        branch = self.request.query_params.getlist('branch')
        if branch and branch != [""]:
            fil.update({
                'branch__slug__in': branch
            })

        division = self.request.query_params.getlist('division')
        if division and division != [""]:
            fil.update({
                'division__slug__in': division
            })

        employment_status = self.request.query_params.getlist(
            'employment_status'
        )
        if employment_status and employment_status != [""]:
            fil.update({
                'employment_status__slug__in': employment_status
            })

        return fil

    def get_rule(self):
        rule_id = self.request.query_params.get('leave_rule')
        try:
            return LeaveRule.objects.get(id=rule_id)
        except (LeaveRule.DoesNotExist, TypeError, ValueError):
            return None


class LeaveAccountViewSet(
    HRSOrderingFilter,
    OrganizationMixin,
    ListRetrieveViewSetMixin
):
    """
    list:

    ## Lists all the instances of LeaveAccount with limited fields.
    ```javascript
    [
        {

        },
        {

        }
    ]
    ```
    retrieve:

    ## Displays an instance of LeaveAccount with all fields.

    ```javascript
    {

    }
    ```
    update:

    # Updates an instance of LeaveAccount.

    ## Sample PUT request
    ```javascript
    {

    }
    ```

    partial_update:

    Updates  details partially.

    Accepts the same parameters as ```.update()``` but not all fields required.

    """
    queryset = User.objects.filter()
    filter_backends = (
        filters.SearchFilter, DjangoFilterBackend, FilterMapBackend
    )
    search_fields = (
        'first_name',
        'middle_name',
        'last_name',
        'username'
    )
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'username': 'username',
    }
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name')
    }
    permission_classes = [LeaveAccountPermission]

    def get_serializer_class(self):
        if self.action.lower() == 'list':
            return LeaveAccountListSerializer
        else:
            return LeaveAccountBulkUpdateSerializer

    def get_queryset(self):
        permission_filters = dict()

        permission_code_matches = validate_permissions(
            self.request.user.get_hrs_permissions(self.organization),
            LEAVE_PERMISSION,
            LEAVE_BALANCE_PERMISSION,
            OFFLINE_LEAVE_PERMISSION
        )
        mode = self.request.query_params.get('as')
        subordinates = self.request.user.subordinates_pks
        if mode == 'supervisor':
            permission_filters.update({
                'id__in': subordinates
            })

        if mode == 'hr' and not permission_code_matches:
            raise PermissionDenied

        elif mode not in ['hr', 'supervisor']:
            permission_filters.update({'id': self.request.user.id})

        return super().get_queryset().filter(
            detail__organization=self.get_organization(),
            **permission_filters
        ).filter(
            # at least include self users id for not raising
            # 404 on user id
            Q(leave_accounts__is_archived=False) | Q(
                id=self.request.user.id)
        ).select_related(
            'detail',
            'detail__organization',
            'detail__division',
            'detail__employment_level',
            'detail__job_title'
        ).distinct()

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'applicable_leaves': get_applicable_leave_types_for_organization(
                self.get_organization()
            )
        })
        return ret

    def retrieve(self, request, *args, **kwargs):
        user_instance = self.get_object()
        active_master_setting = MasterSetting.objects.filter(
            organization=self.get_organization()
        ).active().first()
        expired_master_setting = MasterSetting.objects.filter(
            organization=self.get_organization()
        ).expired().order_by('-effective_till').first()
        status = request.query_params.get('status')
        if status and status == 'expired':
            queryset = LeaveAccount.objects.filter(
                rule__leave_type__master_setting=expired_master_setting
            )
        else:
            queryset = LeaveAccount.objects.filter(
                rule__leave_type__master_setting=active_master_setting
            )
        queryset = queryset.filter(
            is_archived=False,
            user=user_instance
        ).select_related(
            'rule',
            'rule__leave_type'
        )
        visibility_toggle = self.request.query_params.get('visible', '')
        if visibility_toggle in ['true', 'false']:
            filter_switch = {
                'true': {
                    'rule__leave_type__visible_on_default': True
                },
                'false': {
                    'rule__leave_type__visible_on_default': False
                }
            }.get(
                visibility_toggle
            )
            queryset = queryset.filter(
                **filter_switch
            )

        ordering = self.request.query_params.get('ordering', None)
        if ordering in ['-usable_balance', 'usable_balance']:
            queryset = queryset.order_by(ordering)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = LeaveAccountSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = LeaveAccountSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(methods=('post',), detail=True, url_path='edit')
    def update_balance(self, request, *args, **kwargs):
        self.serializer_class = LeaveAccountBulkUpdateSerializer
        serializer = LeaveAccountBulkUpdateSerializer(
            data=self.request.data,
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class UserLeaveAccountHistoryViewSet(
    OrganizationMixin,
    UserMixin,
    ListViewSetMixin
):
    serializer_class = LeaveAccountHistorySerializer
    queryset = LeaveAccountHistory.objects.all()
    permission_classes = [LeaveAccountHistoryPermission]

    def get_queryset(self):
        account = self.get_account()
        return super().get_queryset().filter(
            user=self.user,
            user__detail__organization=self.get_organization(),
            account=account
        ).select_related(
            'user__detail',
            'user__detail__organization',
            'user__detail__division',
            'user__detail__employment_level',
            'user__detail__job_title'
        )

    def get_account(self):
        return get_object_or_404(
            LeaveAccount,
            pk=self.kwargs.get('balance_id')
        )

    def has_user_permission(self):
        return self.request.user == getattr(self.get_account(), "user", None) or self.is_supervisor


class UserLeaveRequestStatistics(
    OrganizationMixin,
    UserMixin,
    ListViewSetMixin,
    GetStatisticsMixin
):
    queryset = LeaveRequest.objects.all()
    serializer_class = UserLeaveRequestStatisticsSerializer
    filter_backends = [FilterMapBackend]
    permission_classes = [UserLeaveReportPermission]
    filter_map = {
        'start_date': 'end__date__gte',
        'end_date': 'start__date__lte',
        'status': 'status'
    }
    statistics_field = 'status'

    def get_queryset(self):
        qs = super().get_queryset(
        ).filter(
            user=self.user,
            user__detail__organization=self.get_organization()
        ).select_related(
            'user__detail',
            'user__detail__organization',
            'user__detail__division',
            'user__detail__employment_level',
            'user__detail__job_title'
        )
        return qs

    def has_user_permission(self):
        return self.request.user == self.user

    def list(self, request, *args, **kwargs):
        ret = super().list(request, *args, **kwargs)
        ret.data.update({
            'counts': self.statistics
        })
        return ret


class MigrateOldLeaveAccountView(
    OrganizationMixin,
    CreateViewSetMixin
):
    serializer_class = BulkMigrateOldAccountSerializer
    lookup_url_kwarg = 'master_setting'
    permission_classes = [LeaveMasterSettingPermission]

    def get_serializer_context(self):
        expired_setting = MasterSetting.objects.filter(
            organization=self.get_organization()
        ).expired().order_by('-effective_till').first()
        ctx = super().get_serializer_context()
        ctx.update({
            'active_setting': get_active_master_setting(
                self.get_organization()
            ),
            'expired_setting': expired_setting
        })
        return ctx
