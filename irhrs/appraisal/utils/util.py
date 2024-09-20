from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter

from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.constants import THREE_SIXTY_PERFORMANCE_APPRAISAL
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot
from irhrs.core.mixins.viewset_mixins import OrganizationMixin
from irhrs.core.utils import nested_getattr
from irhrs.core.utils.common import get_today
from irhrs.core.utils.filters import OrderingFilterMap

User = get_user_model()


class AppraisalSettingBaseFilterMixin:
    valid_branch = valid_division = valid_employment_type = valid_employment_level = []
    filter_with_list = ['branch', 'division', 'employment_type', 'employment_level']
    appraisal_type = None

    def get_appraisal_type(self):
        assert self.appraisal_type, 'Appraisal Type must be defined.'
        return self.appraisal_type

    def get_queryset(self, union=True):
        queryset = User.objects.all().current().select_related(
            'detail', 'detail__organization', 'detail__job_title', 'detail__division',
            'detail__branch', 'detail__employment_status', 'detail__employment_level'
        )
        return self.base_filter_according_to_setting(queryset, union)

    def get_exceptional_filter(self, sub_pa_slot, action_type='include'):
        exceptional_filter = sub_pa_slot.exceptional_appraisee_filter_seetings.filter(
            appraisal_type=self.get_appraisal_type()
        ).first()

        if exceptional_filter:
            if action_type == 'include':
                users = exceptional_filter.include_users.values_list('id', flat=True)
            else:
                users = exceptional_filter.exclude_users.values_list('id', flat=True)
            if users:
                return Q(id__in=users)
        return Q()

    def base_filter_according_to_setting(self, queryset, union=True):
        appraisal_setting = getattr(self.performance_appraisal_slot, 'appraisal_setting', None)
        fil = Q()
        if appraisal_setting:
            date_range = {
                getattr(
                    appraisal_setting,
                    'duration_of_involvement_type'
                ).lower(): getattr(appraisal_setting, 'duration_of_involvement')
            }
            valid_joined_date = get_today() - relativedelta(**date_range)
            self.get_appraisal_setting_data(appraisal_setting)
            fil = Q(
                Q(detail__joined_date__lte=valid_joined_date),
                *[self.get_valid_filter(filter_with) for filter_with in self.filter_with_list]
            )
        get_user_id = queryset.filter(fil).exclude(
                self.get_exceptional_filter(
                    sub_pa_slot=self.performance_appraisal_slot,
                    action_type='exclude'
                )
            ).values_list(
                'id',
                flat=True
            )
        if union:
            qs = queryset.filter(id__in=get_user_id.union(
                queryset.filter(
                    self.get_exceptional_filter(sub_pa_slot=self.performance_appraisal_slot)
                ).values_list('id', flat=True)
            )
            )
            return qs
        return queryset.filter(id__in=get_user_id)


    def get_valid_filter(self, filter_with):
        filter_data = getattr(self, f'valid_{filter_with}')
        filter_text = filter_with if filter_with != "employment_type" else "employment_status"
        if filter_data:
            return Q(**{f'detail__{filter_text}__slug__in': filter_data})
        return Q()

    def get_appraisal_setting_data(self, appraisal_setting):
        self.valid_branch = appraisal_setting.branches.all().order_by(
            'slug'
        ).values_list('slug', flat=True)
        self.valid_division = appraisal_setting.divisions.all().order_by(
            'slug'
        ).values_list('slug', flat=True)
        self.valid_employment_type = appraisal_setting.employment_types.all().order_by(
            'slug'
        ).values_list('slug', flat=True)
        self.valid_employment_level = appraisal_setting.employment_levels.all().order_by(
            'slug'
        ).values_list('slug', flat=True)


class AppraisalSettingFilterMixin(
    AppraisalSettingBaseFilterMixin,
    OrganizationMixin, SubPerformanceAppraisalMixin
):
    filter_backends = [SearchFilter, OrderingFilterMap]
    search_fields = ('first_name', 'middle_name', 'last_name')
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name'),
    }

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        return qs.filter(*[self.get_filter(filter_with) for filter_with in self.filter_with_list])

    def get_filter(self, filter_with):
        filter_data = self.request.query_params.get(filter_with)
        valid_filter_data = getattr(self, f'valid_{filter_with}')
        if filter_data:
            if valid_filter_data and not {filter_data}.issubset(set(valid_filter_data)):
                raise ValidationError({'detail': f'Invalid {filter_with} filter supplied.'})
            filter_text = filter_with if filter_with != "employment_type" else "employment_status"
            return Q(**{f'detail__{filter_text}__slug': filter_data})
        return Q()

