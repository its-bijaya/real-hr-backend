from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from irhrs.common.api.serializers.common import ProvinceSerializer, CountrySerializer, \
    DistrictSerializer
from irhrs.common.api.serializers.skill import SkillSerializer
from irhrs.core.mixins.viewset_mixins import HRSModelViewSet, ListViewSetMixin
from irhrs.core.utils.filters import FilterMapBackend
from irhrs.organization.api.v1.serializers.employment import EmploymentStatusSerializer, \
    EmploymentLevelSerializer
from irhrs.recruitment.api.v1.mixins import DynamicFieldViewSetMixin, RecruitmentOrganizationMixin
from irhrs.recruitment.api.v1.permissions import (CityPermission, SkillPermission,
                                                  RecruitmentPermission, CountryPermission)
from irhrs.recruitment.api.v1.serializers.common import (
    CitySerializer,
    JobCategorySerializer,
    JobBenefitSerializer,LocationSerializer)
from irhrs.recruitment.models import (
    Location, City,
    Skill, JobCategory,
    JobBenefit, EmploymentStatus,
    EmploymentLevel, Country, District)


class CommonMixin:

    def get_permissions(self):
        if self.request.user.is_anonymous and (
            self.action and self.action.lower() == 'list'
        ):
            self.permission_classes = []
        return super().get_permissions()


class BaseSearchFilter:
    filter_backends = (SearchFilter, )
    search_fields = ['name', ]


class LocationViewSet(CommonMixin, BaseSearchFilter, ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    search_fields = ['address', ]
    # all apis are public
    # no need of assigning permission class
    permission_classes = []


class CountryViewSet(
    DynamicFieldViewSetMixin, CommonMixin,
    BaseSearchFilter, HRSModelViewSet
):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [CountryPermission]
    serializer_include_fields = ['id', 'name']

    @action(
        detail=True,
        methods=['get'],
        url_path='provinces'
    )
    def provinces(self, *args, **kwargs):
        country = self.get_object()
        ser = ProvinceSerializer(country.province_set.all(), many=True)
        return Response(ser.data, status=200)


class DistrictViewSet(
    DynamicFieldViewSetMixin,
    BaseSearchFilter, ListViewSetMixin
):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [CountryPermission]
    serializer_include_fields = ['id', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        country_id = self.kwargs.get('country_id')
        province_id = self.kwargs.get('province_id')
        return queryset.filter(province__country_id=country_id, province_id=province_id)


class CityViewSet(CommonMixin, BaseSearchFilter, HRSModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [CityPermission]

    filter_backends = (SearchFilter, FilterMapBackend)
    search_fields = ['name', 'district_name', 'province']
    filter_map = {
        'country': 'district__province__country'
    }


class SkillViewSet(RecruitmentOrganizationMixin, CommonMixin,
                   BaseSearchFilter, HRSModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [SkillPermission]


class JobCategoryViewSet(RecruitmentOrganizationMixin, CommonMixin,
                         BaseSearchFilter, HRSModelViewSet):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    permission_classes = [RecruitmentPermission]


class JobBenefitViewSet(CommonMixin, BaseSearchFilter, HRSModelViewSet):
    queryset = JobBenefit.objects.all()
    serializer_class = JobBenefitSerializer
    permission_classes = []


class EmploymentStatusViewSet(DynamicFieldViewSetMixin, BaseSearchFilter, ListViewSetMixin):
    queryset = EmploymentStatus.objects.all()
    serializer_class = EmploymentStatusSerializer
    serializer_include_fields = ['title', 'slug']
    permission_classes = []
    search_fields = ['title', ]


class EmploymentLevelViewSet(DynamicFieldViewSetMixin, BaseSearchFilter, ListViewSetMixin):
    queryset = EmploymentLevel.objects.all()
    serializer_class = EmploymentLevelSerializer
    serializer_include_fields = ['title', 'slug']
    permission_classes = []
    search_fields = ['title', ]
