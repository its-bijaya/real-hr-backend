from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.attendance.constants import REQUESTED, APPROVED, GENERATED, CONFIRMED
from irhrs.attendance.models.timesheet_report_request import TimeSheetReportRequest, \
    TimeSheetReportRequestHistory
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, DummySerializer
from irhrs.core.utils import get_system_admin
from irhrs.noticeboard.constants import DENIED
from irhrs.users.api.v1.serializers.thin_serializers import UserThumbnailSerializer, \
    UserThinSerializer, UserSignatureSerializer


class ReadOnlyTimeSheetReportRequestSerializer(DynamicFieldsModelSerializer):
    # note: this is read only serializer
    user = UserThumbnailSerializer()
    recipient = UserThumbnailSerializer()
    authorized_signature = serializers.SerializerMethodField()
    has_supervisor = serializers.SerializerMethodField()

    class Meta:
        model = TimeSheetReportRequest
        fields = (
            'id',
            'user',
            'recipient',
            'status',
            'report_data',
            "month_name",
            "month_from_date",
            "month_to_date",
            "year_name",
            "year_from_date",
            "year_to_date",
            "authorized_signature",
            "has_supervisor"
        )

    def get_has_supervisor(self, obj):
        return not obj.user.first_level_supervisor_including_bot == get_system_admin()

    def get_authorized_signature(self, obj):
        requested, approved, confirmed = None, None, None

        if obj.status not in [GENERATED, DENIED]:
            requested = obj.histories.filter(action=REQUESTED).order_by('created_at').last()

        if obj.status in [APPROVED, CONFIRMED]:
            approved = obj.histories.filter(action=APPROVED).order_by('created_at').last()

        if obj.status == CONFIRMED:
            confirmed = obj.histories.filter(action=CONFIRMED).order_by('created_at').last()

        data = {
            "employee": None,
            "approved_by": None,
            "confirmed_by": None
        }
        if requested and requested.attached_signature:
            data["employee"] = {
                "user": UserSignatureSerializer(
                    requested.created_by,
                    fields=(
                        'id', 'full_name', 'profile_picture', 'cover_picture',
                        'job_title', 'is_online', 'last_online',
                    ),
                    context=self.context
                ).data,
                "signature": self.request.build_absolute_uri(requested.attached_signature.url)
            }
        if approved and approved.attached_signature:
            data["approved_by"] = {
                "user": UserSignatureSerializer(
                    approved.created_by,
                    fields=(
                        'id', 'full_name', 'profile_picture', 'cover_picture',
                        'job_title', 'is_online', 'last_online'
                    ),
                    context=self.context
                ).data,
                "signature": self.request.build_absolute_uri(approved.attached_signature.url)
            }
        if confirmed and confirmed.attached_signature:
            data["confirmed_by"] = {
                "user": UserSignatureSerializer(
                    confirmed.created_by,
                    fields=(
                        'id', 'full_name', 'profile_picture', 'cover_picture',
                        'job_title', 'is_online', 'last_online'
                    ),
                    context=self.context
                ).data,
                "signature": self.request.build_absolute_uri(confirmed.attached_signature.url)
            }
        return data


class RemarksRequiredSerializer(DummySerializer):
    remarks = serializers.CharField(max_length=600)


class RemarksOptionalSerializer(DummySerializer):
    remarks = serializers.CharField(max_length=600, allow_blank=True)


class TimeSheetReportActionSerializer(DummySerializer):
    remarks = serializers.CharField(max_length=600)
    add_signature = serializers.BooleanField(default=False)

    def validate(self, attrs):
        add_signature = attrs.get('add_signature')
        request = self.context.get('request')
        if request and add_signature and not request.user.signature:
            raise ValidationError({
                'detail': 'Add signature on general information within your profile.'
            })
        return super().validate(attrs)


class TimeSheetReportRequestHistorySerializer(DynamicFieldsModelSerializer):
    actor = UserThumbnailSerializer()
    action_performed_to = UserThumbnailSerializer(source='action_to')

    class Meta:
        model = TimeSheetReportRequestHistory
        fields = (
            'created_at',
            'actor',
            'action',
            'action_performed_to',
            'remarks'
        )
