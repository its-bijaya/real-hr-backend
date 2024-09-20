from dateutil.parser import parse as parse_date
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from django.db.models import Q, Count
from django.http import Http404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from irhrs.core.constants.user import MALE, FEMALE, OTHER, RESIGNED, MARRIED, \
    SINGLE
from irhrs.core.mixins.serializers import add_fields_to_serializer_class
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, OrganizationMixin
from irhrs.core.utils.common import get_today
from irhrs.hris.api.v1.permissions import HRISPermission, \
    HRISReportPermissionMixin, HRISUserPermission
from irhrs.organization.api.v1.serializers.employment import \
    EmploymentStatusSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.websocket.consumers.global_consumer import UserOnline

USER = get_user_model()


class UserListMixin:

    categories_map = {}
    extra_data_map = {}

    @action(methods=['GET'], detail=False, url_name='user-list',
            url_path=r'(?P<category>[\w]+)-users')
    def user_list(self, request, category, **kwargs):

        method_name = self.categories_map.get(category, None)
        if not method_name:
            raise Http404

        select_related = ["detail", "detail__job_title", "detail__division"]

        queryset = getattr(self, method_name)().select_related(*select_related).order_by(
            "first_name", "middle_name", "last_name"
        )

        gender = request.query_params.get("gender", None)
        if gender:
            # since gender is stored in title case so convert to title case instead of using iexact
            queryset = queryset.filter(detail__gender=gender.title())

        page = self.paginate_queryset(queryset)

        # get details of field to add from extra_data_map
        extra_field_name, extra_field_source = self.extra_data_map.get(category, ('joined_date', 'detail.joined_date'))

        serializer_class = add_fields_to_serializer_class(UserThinSerializer, {
            extra_field_name: serializers.ReadOnlyField(
                source=extra_field_source, allow_null=True),
            'employment_status': EmploymentStatusSerializer(
                fields=['title', 'slug'],
                source='detail.employment_status'
            )
        })

        serializer_data = serializer_class(
            page,
            many=True,
            fields=["id", "full_name", "profile_picture", "cover_picture",
                    "division", "is_online", "job_title", 'employment_status', 'is_current', 'organization',
                    extra_field_name],
            context=self.get_serializer_context()
        ).data
        return self.get_paginated_response(serializer_data)


class HRISStatisticMixin:
    @staticmethod
    def get_critical_contracts_queryset(org, queryset):
        contract_settings = getattr(org, 'contract_settings', None)
        critical_days = getattr(contract_settings, 'critical_days', 15)

        critical_date = timezone.now().date() + timezone.timedelta(
            days=critical_days)

        return queryset.filter(
            user_experiences__is_current=True,
            user_experiences__employment_status__is_contract=True,
            user_experiences__end_date__lte=critical_date,
            user_experiences__end_date__gte=timezone.now().date()
        )

    @staticmethod
    def get_incomplete_profiles_queryset(queryset):
        return queryset.filter(
            Q(profile_picture__isnull=True) |
            Q(detail__religion__isnull=True) |
            Q(detail__ethnicity__isnull=True) |
            Q(addresses__isnull=True) |
            Q(contacts__isnull=True) |
            Q(languages__isnull=True) |
            Q(medical_info__isnull=True) |
            Q(legal_info__isnull=True)
        ).distinct()

    @staticmethod
    def get_active_employee_queryset(queryset):
        online_employees = UserOnline.all_active_user_ids()
        return queryset.filter(
            id__in=online_employees
        )

    @staticmethod
    def get_inactive_employee_queryset(queryset):
        online_employees = UserOnline.all_active_user_ids()
        return queryset.exclude(
            id__in=online_employees
        ).distinct()


class HRISOverviewSummary(HRISStatisticMixin, HRISReportPermissionMixin, OrganizationMixin,
                          UserListMixin, ListViewSetMixin):
    """
    View for HRIS Overview information bar

    use `/{category}-users/` for users list of numbers

    category can be `total`, `active`, `inactive`, `critical`, `incomplete`
    """
    categories_map = {
        "total": "get_queryset",
        "active": "get_active_employee",
        "inactive": "get_inactive_employee",
        "critical": "get_critical_contracts",
        "incomplete": "get_incomplete_profiles"
    }
    extra_data_map = {
        "critical": ('expiry_date', 'current_experience.end_date'),
    }

    def get_queryset(self):
        select_related = [
            'detail', 'detail__job_title', 'detail__employment_status'
        ]
        queryset = USER.objects.all().current().select_related(*select_related)

        supervisor = self.request.query_params.get('supervisor')

        queryset = queryset.filter(detail__organization=self.get_organization())

        if supervisor:
            if supervisor == str(self.request.user.id):
                queryset = queryset.filter(
                    id__in=self.request.user.subordinates_pks)
            else:
                queryset = queryset.none()

        return queryset

    def list(self, request, *args, **kwargs):
        total_employee = self.get_queryset().count()
        active_employee = self.get_active_employee().count()
        inactive_employee = total_employee - active_employee
        critical_contracts = self.get_critical_contracts().count()

        return Response({
            "Total Employee": total_employee,
            "Active Employee": active_employee,
            "Inactive Employee": inactive_employee,
            "Incomplete Profile": self.get_incomplete_profiles().count(),
            "Critical Contracts": critical_contracts
        })

    def get_critical_contracts(self):
        return self.get_critical_contracts_queryset(org=self.get_organization(),
                                                    queryset=self.get_queryset())

    def get_incomplete_profiles(self):
        return self.get_incomplete_profiles_queryset(queryset=self.get_queryset())

    def get_active_employee(self):
        return self.get_active_employee_queryset(queryset=self.get_queryset())

    def get_inactive_employee(self):
        return self.get_inactive_employee_queryset(queryset=self.get_queryset())


class HRStatisticsView(OrganizationMixin, UserListMixin,
                       HRISReportPermissionMixin,
                       ListViewSetMixin):
    """
    View for Statistics section on HRIS overview

    use `/{category}-users/` for users list of numbers

    category can be `joined`, `resigned`, `turnover`, `married`, `single`
    """
    queryset = USER.objects.all()

    start_date = None
    end_date = None
    days = 365

    categories_map = {
        "joined": "get_joined_queryset",
        "resigned": "get_resigned_users",
        "turnover": "get_parted_users",
        "married": "get_married_users",
        "single": "get_single_users"
    }
    extra_data_map = {
        # type : (key, field)
        "joined": ('joined_date', 'detail.joined_date'),
        "resigned": ('resigned_date', 'detail.resigned_date'),
        "turnover": ('parted_date', 'detail.last_working_date'),
        "married": ('joined_date', 'detail.joined_date'),
        "single": ('joined_date', 'detail.joined_date'),
    }

    def get_queryset(self):
        supervisor_id = self.request.query_params.get('supervisor')
        fil = dict(
            detail__organization=self.organization
        )

        if supervisor_id:
            if supervisor_id == str(self.request.user.id):
                fil.update({
                    'id__in':
                        self.request.user.subordinates_pks
                })
            else:
                # if supervisor does not match return none
                return super().get_queryset().none()

        self.set_start_end_date()

        return super().get_queryset().filter(**fil)

    def set_start_end_date(self):
        start_date = self.request.query_params.get('start_date')

        end_date = self.request.query_params.get(
            'end_date', None)

        if start_date:
            try:
                self.start_date = parse_date(start_date).date()
                self.end_date = parse_date(end_date).date() if \
                    end_date else timezone.now().date()

                self.days = (self.start_date - self.end_date).days + 1
                return
            except (TypeError, ValueError, ValidationError):
                pass
        self.start_date = timezone.now().date() - timezone.timedelta(days=365)
        self.end_date = timezone.now().date()
        self.days = (self.start_date - self.end_date).days + 1

    def list(self, request, *args, **kwargs):
        # filtered_queryset
        queryset = self.filter_queryset(self.get_queryset())

        # start date of a period before asked date range
        last_period_start_date = self.start_date - \
                                 timezone.timedelta(days=self.days)

        # total users
        total_users = queryset.current().count()
        past_users = self.get_queryset().filter(
            Q(detail__joined_date__lte=last_period_start_date) & Q(
                Q(detail__last_working_date__isnull=True) |
                Q(detail__last_working_date__gte=self.end_date)
            )
        )
        past_total_users_count = past_users.count()

        # joined users stats
        current_joined = self.get_joined_queryset().aggregate(
            male=Count('id', filter=Q(detail__gender=MALE)),
            female=Count('id', filter=Q(detail__gender=FEMALE)),
            other=Count('id', filter=Q(detail__gender=OTHER)),
            total=Count('id')
        )
        current_joined_users = current_joined.get('total')
        past_period_joined_users = self.get_queryset().filter(
            detail__joined_date__gte=last_period_start_date,
            detail__joined_date__lt=self.start_date
        ).count()

        if total_users != 0 and past_total_users_count != 0:
            joined_increment = ((current_joined_users / total_users) - (
                    past_period_joined_users / past_total_users_count
            )) * 100
        else:
            joined_increment = "N/A"

        # resigned users calculation
        resigned_users = self.get_resigned_users().aggregate(
            male=Count('id', filter=Q(detail__gender=MALE)),
            female=Count('id', filter=Q(detail__gender=FEMALE)),
            other=Count('id', filter=Q(detail__gender=OTHER)),
            total=Count('id')
        )
        past_resigned_users = self.get_queryset().filter(
            detail__last_working_date__gte=last_period_start_date,
            detail__last_working_date__lt=self.start_date,
            detail__parting_reason=RESIGNED
        ).count()

        resigned_users_count = resigned_users.get('total')

        if total_users != 0 and past_total_users_count != 0:
            resigned_increment = ((resigned_users_count / total_users) -
                                  (past_resigned_users / past_total_users_count)
                                  ) * 100
        else:
            resigned_increment = "N/A"

        parted_users = self.get_parted_users().aggregate(
            male=Count('id', filter=Q(detail__gender=MALE)),
            female=Count('id', filter=Q(detail__gender=FEMALE)),
            other=Count('id', filter=Q(detail__gender=OTHER)),
            total=Count('id')
        )
        past_parted_users = self.get_queryset().filter(
            detail__last_working_date__gte=last_period_start_date,
            detail__last_working_date__lt=self.start_date,
        ).count()
        parted_users_count = parted_users.get('total')

        if total_users != 0 and past_total_users_count != 0:
            turnover_increment = ((parted_users_count / total_users) -
                                  (past_parted_users / past_total_users_count)) * 100
        else:
            turnover_increment = 'N/A'

        # marital_status
        married = self.filter_status_by_marital_status(MARRIED).aggregate(
            male=Count('id', filter=Q(detail__gender=MALE)),
            female=Count('id', filter=Q(detail__gender=FEMALE)),
            other=Count('id', filter=Q(detail__gender=OTHER)),
            total=Count('id')
        )
        single = self.filter_status_by_marital_status(SINGLE).aggregate(
            male=Count('id', filter=Q(detail__gender=MALE)),
            female=Count('id', filter=Q(detail__gender=FEMALE)),
            other=Count('id', filter=Q(detail__gender=OTHER)),
            total=Count('id')
        )

        all_ = self.get_queryset().current().aggregate(
            male=Count('id', filter=Q(detail__gender=MALE)),
            female=Count('id', filter=Q(detail__gender=FEMALE)),
            other=Count('id', filter=Q(detail__gender=OTHER)),
            total=Count('id')
        )

        return Response({
            "joined": {
                "total": current_joined_users,
                "male": current_joined.get("male"),
                "female": current_joined.get("female"),
                "other": current_joined.get("other"),
                "change_percentage": joined_increment,
            },
            "resigned": {
                "total": resigned_users_count,
                "male": resigned_users.get("male"),
                "female": resigned_users.get("female"),
                "other": resigned_users.get("other"),
                "change_percentage": resigned_increment
            },
            "turnover": {
                "total": parted_users_count,
                "male": parted_users.get("male"),
                "female": parted_users.get("female"),
                "other": parted_users.get("other"),
                "change_percentage": turnover_increment
            },
            "married": married,
            "single": single,
            "age": self.get_age_stats(),
            "genders": all_
        })

    def get_age_stats(self):
        queryset = self.get_queryset().current()
        today = get_today()
        age_groups = [(16, 25), (25, 35), (35, 45), (45, 60), (60, 150)]
        date_rages = {
            f"{start}-{end}": {
                "start": today - timezone.timedelta(days=start * 365),
                "end": today - timezone.timedelta(days=end * 365)
            }
            for start, end in age_groups
        }

        agg = {
            key: Count(
                "id",
                filter=Q(
                    detail__date_of_birth__lte=val["start"],
                    detail__date_of_birth__gt=val["end"])
            )
            for key, val in date_rages.items()
        }

        return queryset.aggregate(**agg)

    def get_filtered_queryset(self):
        # filtered_queryset
        # joined users
        return self.filter_queryset(self.get_queryset())

    def get_joined_queryset(self):
        return self.get_filtered_queryset().filter(
            detail__joined_date__gte=self.start_date,
            detail__joined_date__lte=self.end_date
        )

    def get_resigned_users(self):
        return self.get_filtered_queryset().filter(
            detail__last_working_date__gte=self.start_date,
            detail__last_working_date__lte=self.end_date,
            detail__parting_reason=RESIGNED
        )

    def get_parted_users(self):
        return self.get_filtered_queryset().filter(
            detail__last_working_date__gte=self.start_date,
            detail__last_working_date__lte=self.end_date,
        )

    def filter_status_by_marital_status(self, status):
        return self.get_queryset().current().filter(detail__marital_status=status)

    def get_married_users(self):
        return self.filter_status_by_marital_status(MARRIED)

    def get_single_users(self):
        return self.filter_status_by_marital_status(SINGLE)
