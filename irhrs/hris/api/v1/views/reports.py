from django.core.exceptions import ValidationError
from django.db.models import (Case, When, F, DateField,
                              ExpressionWrapper, DurationField, Count, Q)
from django.utils import timezone
from rest_framework.response import Response

from irhrs.core.constants.user import (MALE, FEMALE, OTHER, MARRIED, SINGLE,
                                       DIVORCED, WIDOWED)
from irhrs.core.mixins.viewset_mixins import (ListViewSetMixin, OrganizationMixin)
from irhrs.core.utils.common import apply_filters
from irhrs.hris.api.v1.permissions import HRISReportHROnlyPermission
from irhrs.hris.api.v1.serializers.reports import ReportSerializer
from irhrs.organization.models import EmploymentLevel, get_user_model
from irhrs.users.models import UserDetail

User = get_user_model()


class YearsOfServiceFilterMixin:

    @staticmethod
    def annotate_service_period(queryset):
        qs = queryset.annotate(
            end_date=Case(
                When(last_working_date__isnull=False, then=F(
                    'last_working_date')),
                default=timezone.now().date(),
                output_field=DateField(),
            )
        ).annotate(
            duration=ExpressionWrapper(F('end_date') - F('joined_date'),
                                       output_field=DurationField())
        )
        return qs


class DivisionBranchFilterMixin:
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get(
            'end_date', str(timezone.now().date()))

        if start_date:
            try:
                queryset = queryset.filter(
                    joined_date__gte=start_date,
                    joined_date__lte=end_date)
            except (TypeError, ValidationError):
                # invalid date format
                pass
        queryset = apply_filters(
            self.request.query_params,
            {
                'branch': 'branch__slug',
                'division': 'division__slug'
            },
            queryset
        )

        return queryset


class NoOfEmployeesVsYearsOfServiceView(DivisionBranchFilterMixin,
                                        OrganizationMixin,
                                        YearsOfServiceFilterMixin,
                                        ListViewSetMixin):
    """
    list:
    query params: "start_date", "end_date" filter through date joined
         "division", "branch" accept slugs
    """
    serializer_class = ReportSerializer
    permission_classes = [HRISReportHROnlyPermission]

    def get_queryset(self):
        return self.annotate_service_period(
            UserDetail.objects.filter(
                organization=self.get_organization(),
            ).current()
        )

    def list(self, request, **kwargs):
        queryset = self.annotate_service_period(
            self.filter_queryset(self.get_queryset()))
        years_of_service = [
            (0, 2), (2, 4), (4, 6), (6, 8), (8, 10),
            (10, 12), (12, 14), (14, 100)
        ]
        group_data = {
            f"{start}-{end}": {
                "start": timezone.timedelta(days=365 * start),
                "end": timezone.timedelta(days=365 * end)
            }
            for (start, end) in years_of_service
        }
        result = {}
        for key, value in group_data.items():
            result.update({key: queryset.filter(duration__gte=value["start"],
                                                duration__lt=value["end"]
                                                ).count()})

        return Response(result)


class MarriedVsAgeVsGender(DivisionBranchFilterMixin,
                           OrganizationMixin,
                           ListViewSetMixin):
    """
    list:
    query params: "start_date", "end_date" filter through date joined
         "division", "branch" accept slugs
    """
    permission_classes = [HRISReportHROnlyPermission]

    def get_queryset(self):
        return UserDetail.objects.filter(
            organization=self.get_organization()
        ).current()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        today = timezone.now().date()
        age_groups = [(16, 25), (25, 35), (35, 45), (45, 60), (60, 150)]

        date_rages = {
            f"{start}-{end}": {
                "start": today - timezone.timedelta(days=start * 365),
                "end": today - timezone.timedelta(days=end * 365)
            }
            for start, end in age_groups
        }

        pre_result = {
            key:
                {
                    "Male": queryset.filter(
                        date_of_birth__lte=val["start"],
                        date_of_birth__gt
                        =val["end"],
                        gender=MALE
                    ),
                    "Female": queryset.filter(
                        date_of_birth__lte=val["start"],
                        date_of_birth__gt=val["end"],
                        gender=FEMALE
                    ),
                    "Other": queryset.filter(
                        date_of_birth__lte=val["start"],
                        date_of_birth__gt=val["end"],
                        gender=OTHER
                    )
                }
            for key, val in date_rages.items()
        }

        result = {}

        for key, fil in pre_result.items():
            data = {}
            for gender, qs in fil.items():
                agg = {
                    marital_status: Count('id', filter=Q(
                        marital_status=marital_status))
                    for marital_status in [MARRIED, SINGLE, DIVORCED,
                                           WIDOWED]
                }
                agg.update({
                    'total': Count('id')
                })
                data.update({gender: qs.aggregate(**agg)})
            result.update({key: data})

        return Response(result)


class EmploymentLevelVsAgeGroup(DivisionBranchFilterMixin,
                                OrganizationMixin,
                                ListViewSetMixin):
    """
    list:
    query params: "start_date", "end_date" filter through date joined
         "division", "branch" accept slugs
    """
    permission_classes = [HRISReportHROnlyPermission]

    def get_queryset(self):
        return UserDetail.objects.filter(
            organization=self.get_organization()
        ).current()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        today = timezone.now().date()
        age_groups = [(16, 25), (25, 35), (35, 45), (45, 60), (60, 150)]

        date_rages = {
            f"{start}-{end}": {
                "start": today - timezone.timedelta(days=start * 365),
                "end": today - timezone.timedelta(days=end * 365)
            }
            for start, end in age_groups
        }

        employment_levels = EmploymentLevel.objects.filter(
            organization=self.get_organization(),
            is_archived=False
        )

        results = []

        for level in employment_levels:
            level_users = queryset.filter(
                employment_level=level
            )

            agg = {
                key: Count(
                    'id',
                    filter=Q(
                        employment_level=level,
                        date_of_birth__lte=value["start"],
                        date_of_birth__gt=value["end"]
                    )
                )
                for key, value in date_rages.items()
            }
            data = {
                "title": level.title,
                "slug": level.slug,
                "count": level_users.count()
            }
            data.update(queryset.aggregate(**agg))
            results.append(data)

        return Response({"results": results})
