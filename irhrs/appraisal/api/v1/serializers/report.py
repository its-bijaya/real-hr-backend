from django.contrib.auth import get_user_model
from rest_framework import serializers

from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalYearWeight
from irhrs.appraisal.utils.common import (
    get_user_appraisal_score_for_year,
    get_user_appraisal_score_for_slot
)
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class SummaryReportSerializer(UserThinSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'profile_picture',
            'cover_picture',
            'job_title',
            'is_current',
            'organization',
            'score',
        ]

    def get_score(self, user):
        slot_id = self.context.get('slot_id')
        return get_user_appraisal_score_for_slot(user, slot_id)


class SummaryReportDetailSerializer(UserThinSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'profile_picture',
            'cover_picture',
            'job_title',
            'is_current',
            'organization',
            'score',
        ]

    @staticmethod
    def get_score(obj):
        score = 0
        # To resolve Zero Division Error
        if obj.total_score:
            score = float(format(obj.score / obj.total_score * 100, '.2f'))
        return score


class YearlyReportSerializer(UserThinSerializer):
    score = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'full_name',
            'job_title',
            'profile_picture',
            'cover_picture',
            'is_current',
            'organization',
            'score'
        ]

    def get_score(self, user):
        year_id = self.context.get('year_id')
        data = get_user_appraisal_score_for_year(user, year_id)
        # replace total_average_score calculated by database value
        yearly_weight = SubPerformanceAppraisalYearWeight.objects.filter(
            appraiser=user, performance_appraisal_year=year_id
        ).first()
        data["total_average_score"] = yearly_weight.percentage if yearly_weight else 0
        return data
