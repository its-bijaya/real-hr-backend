from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from dateutil import parser

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalSettingPermission
from irhrs.appraisal.api.v1.serializers.performance_appraisal import \
    PerformanceAppraisalYearSerializer, SubPerformanceAppraisalSlotModeSerializer
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.performance_appraisal import PerformanceAppraisalYear, \
    SubPerformanceAppraisalSlotMode, SubPerformanceAppraisalSlot
from irhrs.appraisal.utils.common import _validate_total_weight, _validate_repeated_data
from irhrs.core.mixins.viewset_mixins import ListCreateUpdateViewSetMixin, OrganizationMixin, \
    CreateListModelMixin, ListCreateViewSetMixin, OrganizationCommonsMixin
from irhrs.core.utils.common import validate_permissions
from irhrs.core.utils.filters import OrderingFilterMap
from irhrs.notification.utils import add_notification
from irhrs.permission.constants.permissions import PERFORMANCE_APPRAISAL_PERMISSION, \
    PERFORMANCE_APPRAISAL_SETTING_PERMISSION


class SubPerformanceAppraisalMixin:
    performance_appraisal_slot = None

    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)
        self.get_performance_appraisal_slot()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if hasattr(self, 'organization'):
            context['organization'] = self.organization
        context['sub_performance_appraisal_slot'] = self.get_performance_appraisal_slot()
        return context

    def get_performance_appraisal_slot(self):
        if not self.performance_appraisal_slot:
            _id = self.kwargs.get('sub_performance_appraisal_slot_id')
            if _id is not None:
                self.performance_appraisal_slot = get_object_or_404(
                    SubPerformanceAppraisalSlot.objects.all(),
                    id=_id
                )
        return self.performance_appraisal_slot

    def get_queryset(self):
        return super().get_queryset().filter(
            sub_performance_appraisal_slot=self.performance_appraisal_slot
        )


class PerformanceAppraisalYearViewSet(OrganizationMixin, OrganizationCommonsMixin, ListCreateUpdateViewSetMixin):
    queryset = PerformanceAppraisalYear.objects.all()
    serializer_class = PerformanceAppraisalYearSerializer

    filter_backends = [OrderingFilterMap]
    ordering_fields_map = {
        'name': 'name',
        'year': 'year__name'
    }
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        context['mode'] = "hr" if self.request.query_params.get("as") == "hr" else "user"
        return context

    def check_permissions(self, request):
        super().check_permissions(request)
        if self.request.query_params.get('as') == 'hr' and not validate_permissions(
                self.request.user.get_hrs_permissions(self.get_organization()),
                PERFORMANCE_APPRAISAL_PERMISSION,
                PERFORMANCE_APPRAISAL_SETTING_PERMISSION
        ):
            self.permission_denied(
                request, message="You do not have permission to perform this action"
            )


class SubPerformanceAppraisalSlotModeViewSet(OrganizationMixin, SubPerformanceAppraisalMixin,
                                             CreateListModelMixin, ListCreateViewSetMixin):
    queryset = SubPerformanceAppraisalSlotMode.objects.all()
    serializer_class = SubPerformanceAppraisalSlotModeSerializer
    permission_classes = [PerformanceAppraisalSettingPermission]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['organization'] = self.get_organization()
        return context

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() == 'post':
            kwargs.update({
                'fields': ['appraisal_type', 'weightage']
            })
        if self.action == 'update_date_parameters':
            kwargs.update({
                'fields': ['appraisal_type', 'start_date', 'deadline']
            })
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        sub_performance_appraisal_slot = self.get_performance_appraisal_slot()
        sub_performance_appraisal_slot.modes.all().delete()
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        _validate_total_weight(serializer.data)
        _validate_repeated_data(
            data=serializer.data,
            key='appraisal_type',
            message='Duplicate appraisal type supplied.'
        )
        super().perform_create(serializer)

    @action(
        detail=False,
        methods=['post'],
        url_path='update/date-parameters'
    )
    def update_date_parameters(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data

        if not isinstance(data, list):
            data = [data]

        is_updated = False
        changed_modes = list()

        for datum in data:
            modes = self.performance_appraisal_slot.modes.filter(
                appraisal_type=datum.get('appraisal_type')
            )
            start_date = parser.parse(datum.get('start_date'))
            deadline = parser.parse(datum.get('deadline'))
            mode = modes.first()

            date_should_update = (mode.start_date and mode.deadline) and not (
                mode.start_date == start_date.astimezone() and mode.deadline == deadline
            )
            if not (mode.start_date and mode.deadline) or date_should_update:
                is_updated = True
                changed_modes.append(mode.appraisal_type)
                mode_id = mode.id
                modes.update(
                    start_date=start_date,
                    deadline=deadline
                )

        if is_updated:
            appraisals = Appraisal.objects.filter(sub_performance_appraisal_slot__modes=mode_id)
            recipient_list = list()
            for appraisal in appraisals:
                recipient = appraisal.appraiser
                if recipient not in recipient_list:
                    appraisal_type_str = ', '.join(set(changed_modes))
                    add_notification(
                        text=f"Deadline of the {appraisal_type_str} has been changed.",
                        recipient=recipient,
                        action=appraisal,
                        actor=self.request.user,
                        url=f'/user/pa/appraisal/{self.performance_appraisal_slot.id}/forms'
                    )
                    recipient_list.append(recipient)

        return Response(data[:], status=status.HTTP_200_OK)
