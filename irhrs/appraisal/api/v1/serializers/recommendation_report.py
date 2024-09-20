from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlotWeight
from irhrs.appraisal.models.performance_appraisal_setting import StepUpDownRecommendation
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.hris.models import EmploymentReview, ChangeType
from irhrs.hris.api.v1.serializers.onboarding_offboarding import EmploymentReviewSerializer


class RecommendationReportSerializer(serializers.ModelSerializer):
    step_up_down = serializers.SerializerMethodField()
    user = UserThinSerializer(
        source='appraiser',
        read_only=True,
        fields=(
            'id', 'full_name',
            'profile_picture',
            'is_online', 'is_current', 'organization',
        )
    )
    class Meta:
        model = SubPerformanceAppraisalSlotWeight
        fields = (
            'sub_performance_appraisal_slot','percentage', 'step_up_down','user'
        )

    @staticmethod
    def get_step_up_down(obj):
        return obj.step_up_down


class AppraisalEmploymentReviewSerializer(EmploymentReviewSerializer):
    class Meta:
        model = EmploymentReview
        fields = (
            'employee', 'change_type'
        )

    def get_created_at(self, obj):
        return None


    def get_modified_at(self, obj):
        return None

    def get_task_status(self, instance):
        return None

    def create(self, validated_data):
        user_score = self.context.get("queryset").filter(appraiser=validated_data.get("employee")).order_by('appraiser').first()
        if user_score.step_up_down >= 0:
            remarks = f"Step Up/Down by {user_score.step_up_down} recommended from performance appraisal."
        else:
            remarks = f"Step Up/Down by {user_score.step_up_down} recommended from performance appraisal."
        validated_data["remarks"] = remarks
        super().create(validated_data)

class AppraisalEmploymentReviewListSerializer(serializers.Serializer):
    employee_review_list = AppraisalEmploymentReviewSerializer(many=True)
