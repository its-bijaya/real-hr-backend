from django.core.exceptions import ValidationError
from django.db.models import F, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import serializers
from rest_framework.response import Response

from irhrs.core.constants.user import TERMINATED
from irhrs.core.mixins.viewset_mixins import \
    OrganizationMixin, ListRetrieveViewSetMixin, USER
from irhrs.core.utils.common import get_today, get_applicable_filters, \
    apply_filters
from irhrs.core.utils.filters import OrderingFilterMap
from irhrs.hris.api.v1.permissions import HRISPermission, \
    HRISReportPermissionMixin
from irhrs.hris.api.v1.serializers.contract_status import \
    UserContractStatusSerializer, ContractRenewSerializer
from irhrs.permission.constants.permissions import HRIS_PERMISSION, \
    HAS_PERMISSION_FROM_METHOD, HRIS_REPORTS_PERMISSION
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.models import UserExperience


class UserContractStatusView(OrganizationMixin, ListRetrieveViewSetMixin):
    """
    list

    filters

        search= user name
        division__slug
        employee_level__slug
        supervisors

        date range which will filter range of end date of contract
        params start_date and end_date

        status= Safe or Medium or Critical

    """
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilterMap)
    serializer_class = UserContractStatusSerializer
    permission_classes = [
        permission_factory.build_permission(
            "UserContractStatusPermission",
            limit_write_to=[HRIS_PERMISSION],
            limit_read_to=[
                HRIS_PERMISSION,
                HRIS_REPORTS_PERMISSION,
                HAS_PERMISSION_FROM_METHOD
            ],
        )
    ]

    ordering_fields_map = {
        'start_date': 'start_date',
        'end_date': 'end_date',
        'first_name': 'user__first_name',
        'middle_name': 'user__middle_name',
        'last_name': 'user__last_name',
        'division': 'division__name',
        'deadline': 'deadline'
    }
    search_fields = [
        'user__first_name',
        'user__middle_name',
        'user__last_name',
        'user__username'
    ]
    filter_fields = ['division__slug', 'employee_level__slug',
                     'user__supervisors__supervisor']
    ordering = 'end_date'

    def has_user_permission(self):
        if self.request and self.request.method.lower() == 'get' and str(
            self.request.user.id
        ) == self.request.query_params.get(
            'supervisor'
        ):
            return True
        return False

    def get_serializer_context(self):
        organization = self.get_organization()
        context = super().get_serializer_context()
        pk = self.kwargs.get('pk')
        if pk:
            user_exp = UserExperience.objects.get(id=pk)
            context.update({
                'user': user_exp.user
            })

        if organization:
            safe_days = organization.contract_settings.safe_days
            critical_days = organization.contract_settings.critical_days

            context.update({'safe_days': safe_days,
                            'critical_days': critical_days})
        return context

    def get_serializer_class(self):
        if self.action == 'renew':
            return ContractRenewSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(
            is_current=True,
            employment_status__is_contract=True,
            organization=self.get_organization()
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'user_id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return UserExperience.objects.none()
        return UserExperience.objects.filter(**fil)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        status = self.request.query_params.get('status')

        queryset = apply_filters(
            self.request.query_params,
            {
                'start_date': 'end_date__gte',
                'end_date': 'end_date__lte'
            },
            queryset
        )
        if status and status in ["Safe", "Medium", "Critical", "Expired"]:
            context = self.get_serializer_context()
            safe_days = context.get("safe_days")
            critical_days = context.get("critical_days")
            safe_date = timezone.now().date() + timezone.timedelta(
                days=safe_days)
            critical_date = timezone.now().date() + timezone.timedelta(
                days=critical_days)

            if status == "Expired":
                queryset = queryset.filter(
                    end_date__lt=get_today()
                )
            elif status == "Safe":
                queryset = queryset.filter(
                    end_date__gt=safe_date
                )
            elif status == "Critical":
                queryset = queryset.filter(
                    end_date__lt=critical_date, end_date__gte=get_today()
                )
            else:
                queryset = queryset.filter(
                    end_date__lte=safe_date,
                    end_date__gte=critical_date
                )

        return queryset

    @action(methods=['POST'], detail=True, url_name='renew',
            url_path='renew')
    def renew(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        end_date = serializer.data.get('end_date')

        instance = self.get_object()
        instance.is_current = False
        instance.end_date = timezone.now().date()
        if instance.end_date < instance.start_date:
            raise serializers.ValidationError({
                "error": "Start date cannot be greater than end date."
            })
        instance.save()

        instance.pk = None
        instance.is_current = True
        instance.end_date = end_date
        instance.start_date = timezone.now().date() + timezone.timedelta(days=1)
        instance.save()

        return Response({
            "message": f"Successfully renewed contract up to {end_date}."
        }, 201)

    @action(methods=['POST'], detail=True, url_name='terminate',
            url_path='terminate')
    def terminate(self, request, **kwargs):
        today = get_today()
        user = get_object_or_404(
            USER.objects.filter(
                id__in=self.filter_queryset(self.get_queryset()).values('user'),
            ),
            id=self.kwargs.get('pk')
        )
        experience = user.current_experience
        if not experience:
            return Response(
                {'message': 'User has no current experience'},
                400
            )

        if user == request.user:
            return Response(
                {'message': 'Can not act on own user'},
                403
            )

        experience.is_current = False
        experience.end_date = today
        experience.save()

        # block user if contract is terminated
        user.is_active = False
        user.is_blocked = True
        user.save()

        # add termination date
        detail = user.detail
        detail.last_working_date = today
        detail.parting_reason = TERMINATED
        detail.save()

        return Response({
            "message": f"Terminated contract and"
                       f" blocked the user from using system."
        }, 201)
