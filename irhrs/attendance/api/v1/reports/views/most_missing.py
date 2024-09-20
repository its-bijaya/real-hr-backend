from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import Http404
from rest_framework.fields import ReadOnlyField

from irhrs.attendance.api.v1.reports.views.mixins import AttendanceReportPermissionMixin
from irhrs.attendance.constants import PUNCH_IN, ATT_ADJUSTMENT, WORKDAY, NO_LEAVE, PUNCH_OUT, TIME_OFF, SECOND_HALF, \
    FIRST_HALF
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, \
    ListViewSetMixin, DateRangeParserMixin, PastUserFilterMixin
from irhrs.users.api.v1.serializers.thin_serializers import UserFieldThinSerializer

USER = get_user_model()


class MostMissingPunchViewSet(PastUserFilterMixin,
                              AttendanceReportPermissionMixin,
                              OrganizationMixin,
                              DateRangeParserMixin,
                              ListViewSetMixin):
    """
    Most missing

    punch_in -> Adjusted Punch In + Absent without leave
    punch_out -> Adjusted Punch Out  + Missing Punch Out
    """
    serializer_class = type(
        "UserByAttendanceCategoryFrequencySerializer",
        (UserFieldThinSerializer,),
        {
            "count": ReadOnlyField()
        }
    )
    queryset = USER.objects.all()

    def get_serializer(self, *args, **kwargs):
        kwargs.update({
            "user_fields": ['id', 'full_name', 'profile_picture', "cover_picture", "is_online", "job_title"]
        })
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
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
                return queryset.none()

        return queryset.filter(**fil).select_related('detail', "detail__job_title")

    def get_date_filter(self):
        return {"timesheets__timesheet_for__range": self.get_parsed_dates()}

    def get_punch_in_queryset(self, queryset):
        return queryset.annotate(
            count=Count(
                'timesheets',
                filter=Q(
                    Q(
                        # Adjusted punch ins
                        timesheets__timesheet_entries__entry_type=PUNCH_IN,
                        timesheets__timesheet_entries__entry_method=ATT_ADJUSTMENT,
                        **self.get_date_filter()
                    ) | Q(
                        # Absent timesheets
                        timesheets__coefficient=WORKDAY,
                        timesheets__leave_coefficient__in=[NO_LEAVE, FIRST_HALF, SECOND_HALF, TIME_OFF],
                        timesheets__is_present=False,
                        **self.get_date_filter()
                    )
                ),
                distinct=True
            )
        )

    def get_punch_out_queryset(self, queryset):
        return queryset.annotate(
            count=Count(
                'timesheets',
                filter=Q(
                    Q(
                        # Adjusted punch outs
                        timesheets__timesheet_entries__entry_type=PUNCH_OUT,
                        timesheets__timesheet_entries__entry_method=ATT_ADJUSTMENT,
                        **self.get_date_filter()
                    ) | Q(
                        # Missing punch outs
                        timesheets__is_present=True,
                        timesheets__punch_out__isnull=True,
                        **self.get_date_filter()
                    )
                ),
                distinct=True
            )
        )

    def filter_queryset(self, queryset):

        queryset = super().filter_queryset(queryset)

        category = self.kwargs.get('category')

        if category not in ['punch-in', 'punch-out']:
            raise Http404

        queryset = getattr(self, f"get_{category.replace('-', '_')}_queryset")(queryset)

        return queryset.filter(count__gt=0).order_by('-count')
