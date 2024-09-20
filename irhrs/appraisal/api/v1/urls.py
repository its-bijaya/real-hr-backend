from rest_framework.routers import DefaultRouter

from irhrs.appraisal.api.v1.views.appraiser_setting import (
    SupervisorAppraiserSettingViewSet, PeerToPeerFeedBackSettingViewSet,
    SubordinateAppraiserSettingViewSet, ListOfAppraiserWithRespectToAppraiseeViewSet,
    ListOfAppraiseeWithRespectToAppraiserViewSet, SelfAppraiserSettingViewSet,
    AppraisalStatusChangeViewSet, ReviewerEvaluationSettingViewSet,
    SupervisorAppraiserConfigViewSet
)
from irhrs.appraisal.api.v1.views.form_design import PerformanceAppraisalFormDesignViewSet, \
    AppraiseeQuestionSetCountByTypeViewSet, KAARPerformanceAppraisalFormDesignViewSet, \
    KAARAppraiseeQuestionSetCountByTypeViewSet
from irhrs.appraisal.api.v1.views.kaar_report import KeyAchievementAndRatingAppraisalReportViewSet
from irhrs.appraisal.api.v1.views.kaar_score import ScoreAndScalingConfigViewSet, \
    KAARScaleAndScoreSettingViewSet, DefaultScoreSettingViewSet
from irhrs.appraisal.api.v1.views.key_achievements_and_rating_pa import \
    KeyAchievementAndRatingAppraisalViewSet, KAARAppraiserViewSet, SupervisorEvaluationViewSet, \
    ReviewerEvaluationViewSet
from irhrs.appraisal.api.v1.views.kpi import ExtendedIndividualKPIViewSet, KPIViewSet, \
    IndividualKPIViewSet
from irhrs.appraisal.api.v1.views.performance_appraisal import (
    PerformanceAppraisalYearViewSet,
    SubPerformanceAppraisalSlotModeViewSet
)
from irhrs.appraisal.api.v1.views.question import (
    PerformanceAppraisalQuestionSectionViewSet,
    PerformanceAppraisalQuestionSetViewSet,
    PerformanceAppraisalQuestionViewSet,
)

from irhrs.appraisal.api.v1.views.performance_appraisal_setting import (
    AppraisalSettingViewSet, ScoreAndScalingSettingViewSet, DeadlineExtendConditionViewSet,
    DeadlineExceedScoreDeductionConditionViewSet, StepUpDownRecommendationViewSet,
    FormReviewSettingViewSet, ExceptionalAppraiseeFilterSettingViewSet
)
from irhrs.appraisal.api.v1.views.recommendation_report import (
    RecommendationReportViewSet,
)
from irhrs.appraisal.api.v1.views.question_set import QuestionSetActionViewSet
from irhrs.appraisal.api.v1.views.report import PerformanceAppraisalOverviewViewSet, \
    PerformanceAppraisalYearlyReportViewSet, PerformanceAppraisalSummaryReportViewSet

app_name = 'appraisal'

router = DefaultRouter()

router.register(
    r'(?P<organization_slug>[\w\-]+)/year',
    PerformanceAppraisalYearViewSet,
    basename='performance-appraisal-year'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/mode',
    SubPerformanceAppraisalSlotModeViewSet,
    basename='performance-appraisal-mode'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/appraisal',
    AppraisalSettingViewSet,
    basename='appraisal-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/exceptional-appraisee',
    ExceptionalAppraiseeFilterSettingViewSet,
    basename='exceptional-appraisee'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/score-and-scaling',
    ScoreAndScalingSettingViewSet,
    basename='score-and-scaling-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/kaar-score-and-scaling',
    ScoreAndScalingConfigViewSet,
    basename='kaar-score-and-scaling-config'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/kaar-scaling-setting',
    KAARScaleAndScoreSettingViewSet,
    basename='kaar-score-and-scaling-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/kaar-default-score-setting',
    DefaultScoreSettingViewSet,
    basename='kaar-default-score-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/deadline-extend-condition',
    DeadlineExtendConditionViewSet,
    basename='deadline-extend-condition'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/deduction-criteria',
    DeadlineExceedScoreDeductionConditionViewSet,
    basename='deduction-criteria'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/step-up-down',
    StepUpDownRecommendationViewSet,
    basename='step-up-down-recommendation'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/recommendation',
    RecommendationReportViewSet,
    basename='recommendation-report'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/form-review',
    FormReviewSettingViewSet,
    basename='form-review-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/kaar-pa',
    KeyAchievementAndRatingAppraisalViewSet,
    basename='kaar-pa'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/kaar-report',
    KeyAchievementAndRatingAppraisalReportViewSet,
    basename='kaar-pa'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/kaar-appraiser',
    KAARAppraiserViewSet,
    basename='kaar-appraiser'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/supervisor-evaluation',
    SupervisorEvaluationViewSet,
    basename='supervisor-evaluation'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/reviewer-evaluation',
    ReviewerEvaluationViewSet,
    basename='reviewer-evaluation'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/supervisor-appraiser',
    SupervisorAppraiserSettingViewSet,
    basename='supervisor-appraiser-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/supervisor-appraiser-config',
    SupervisorAppraiserConfigViewSet,
    basename='supervisor-appraiser-config'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/reviewer-evaluation',
    ReviewerEvaluationSettingViewSet,
    basename='reviewer-evaluation-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/self-appraiser',
    SelfAppraiserSettingViewSet,
    basename='supervisor-appraiser-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/peer-to-peer-appraiser',
    PeerToPeerFeedBackSettingViewSet,
    basename='peer-to-peer-appraiser-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/setting/subordinate-appraiser',
    SubordinateAppraiserSettingViewSet,
    basename='subordinate-appraiser-setting'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>\d+)/appraisee/(?P<appraisee_id>\d+)/appraiser',
    ListOfAppraiserWithRespectToAppraiseeViewSet,
    basename='appraiser-with-respect-to-appraisee'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>\d+)/appraiser/(?P<appraiser_id>\d+)/appraisee',
    ListOfAppraiseeWithRespectToAppraiserViewSet,
    basename='appraisee-with-respect-to-appraiser'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>\d+)/appraisal/(?P<action_type>(approve-all|edit-deadline|remove-appraisers))',
    AppraisalStatusChangeViewSet,
    basename='appraisal'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/form-design',
    PerformanceAppraisalFormDesignViewSet,
    basename='performance-appraisal-form-design'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/kaar-form-design',
    KAARPerformanceAppraisalFormDesignViewSet,
    basename='kaar-form-design'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/question-set/(?P<action_type>(statistics|count))',
    AppraiseeQuestionSetCountByTypeViewSet,
    basename='appraisee-question-set-count'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/kaar-question-set/(?P<action_type>(statistics|count))',
    KAARAppraiseeQuestionSetCountByTypeViewSet,
    basename='kaar-appraisee-question-set-count'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>[\d]+)/summary/report',
    PerformanceAppraisalSummaryReportViewSet,
    basename='slot-report'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/(?P<year_id>\d+)/yearly/report',
    PerformanceAppraisalYearlyReportViewSet,
    basename='yearly-report'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/overview',
    PerformanceAppraisalOverviewViewSet,
    basename='overview-report'
)

# url for questions
question_url_string = r'(?P<organization_slug>[\w-]+)/question-set'

router.register(
    question_url_string,
    PerformanceAppraisalQuestionSetViewSet,
    basename='appraisal-question-set'
    # private all
)

router.register(
    question_url_string + r'/(?P<question_set>\d+)/section',
    PerformanceAppraisalQuestionSectionViewSet,
    basename='appraisal-question-section'
    # private all
)

router.register(
    question_url_string +
    r'/(?P<question_set>\d+)/section/(?P<question_section>\d+)/question',
    PerformanceAppraisalQuestionViewSet,
    basename='appraisal-question'
    # private all
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/year/slot/(?P<sub_performance_appraisal_slot_id>\d+'
    r')/question-set',
    QuestionSetActionViewSet,
    basename='performance-appraisal-question-set-action'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/kpi-collection',
    KPIViewSet,
    basename='kpi-collection'
)

router.register(
    r'(?P<organization_slug>[\w\-]+)/individual-kpi',
    IndividualKPIViewSet,
    basename='individual-kpi'
)


router.register(
    r'(?P<organization_slug>[\w\-]+)/extended-individual-kpi',
    ExtendedIndividualKPIViewSet,
    basename='extended-individual-kpi'
)

urlpatterns = router.urls
