from django.db.models import F, Sum

from irhrs.appraisal.api.v1.serializers.KAAR_score import RangeScoreSerializer, \
    GradeAndDefaultScalingSerializer
from irhrs.appraisal.constants import REVIEWER_EVALUATION, SUPERVISOR_APPRAISAL, SELF_APPRAISAL, \
    KSA, RECEIVED, PA_QUESTION_SET, SUBMITTED, COMPLETED, DEFAULT, GRADE, RANGE, KPI, GENERATED
from irhrs.appraisal.models.KAAR_question import KAARQuestionSet, KSAOQuestion, GenericQuestionSet
from irhrs.appraisal.models.KAAR_score import GradeAndDefaultScaling, \
    RangeScore, ScoreAndScalingConfig
from irhrs.appraisal.models.key_achievement_and_rating_pa import KAARAppraiserConfig, \
    KeyAchievementAndRatingAppraisal
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot
from irhrs.appraisal.utils.common import _validate_repeated_data
from irhrs.core.utils import nested_getattr
from irhrs.notification.utils import add_notification
from irhrs.questionnaire.models.helpers import LONG, SHORT
from irhrs.users.models import User


def get_kaar_form_designs(sub_performance_appraisal_slot):
    return getattr(sub_performance_appraisal_slot, 'kaar_form_design', None)


def generate_kaar_answer_type(kaar_form_design, question_type=KSA):
    qs_answer_choice = kaar_form_design.kaar_answer_types.filter(
        question_type=question_type
    )
    rating_scale = qs_answer_choice.exclude(answer_type__in=[LONG, SHORT]).first()
    text = qs_answer_choice.filter(answer_type__in=[LONG, SHORT]).first()
    return {
        'description': rating_scale.description,
        'is_mandatory': rating_scale.is_mandatory,
        'remarks_required': text.is_mandatory
    }


def get_appraiser_weightage(appraiser_config: KAARAppraiserConfig) -> int:
    appraisal_slot_mode = appraiser_config.kaar_appraisal.sub_performance_appraisal_slot.modes.filter(
        appraisal_type=appraiser_config.appraiser_type
    ).first()
    return getattr(appraisal_slot_mode, 'weightage', 0)


class CalculateKaarScore:
    def __init__(self, instance: KeyAchievementAndRatingAppraisal):
        self.instance = instance
        self.sub_performance_appraisal_slot = instance.sub_performance_appraisal_slot

    @property
    def scale_config(self):
        return getattr(self.sub_performance_appraisal_slot, 'kaar_score_setting', None)

    def get_question_set(self, question_type):
        return self.instance.question_set.filter(question_type=question_type).first()

    def get_annual_rating(self, question_type):
        return nested_getattr(
                self.get_question_set(question_type), 'annual_rating.final_score', default=None
            )

    def calculate_kpi_score(self, appraiser_config: KAARAppraiserConfig):
        if not self.scale_config:
            return

        if nested_getattr(self.scale_config, 'kpi.scale_type') != GRADE:
            appraiser_weightage = get_appraiser_weightage(appraiser_config)
            total_score = appraiser_config.kpi_scores.aggregate(
                total_score=Sum(
                    F('score') * 0.01 * F('question__extended_individual_kpi__weightage')
                )).get('total_score') or 0
            return round(total_score * 0.01 * appraiser_weightage, 2)
        else:
            return self.get_annual_rating(KPI)

    def calculate_ksao_score(self, appraiser_config: KAARAppraiserConfig):
        if not self.scale_config:
            return
        if nested_getattr(self.scale_config, 'ksao.scale_type') != GRADE:
            ksao_score = appraiser_config.ksao_scores.aggregate(total_score=Sum('score')).get(
                'total_score', 0) or 0
            appraiser_weightage = get_appraiser_weightage(appraiser_config)
            return round(ksao_score * 0.01 * appraiser_weightage, 2)
        else:
            return self.get_annual_rating(KSA)

    def check_score_type(self, question_type, scale_type):
        return nested_getattr(
            self.scale_config, f'{question_type}.scale_type'
        ) == scale_type

    def calculate_overall_rating(self):
        kpi_has_grade_scale = self.check_score_type(KPI, GRADE)
        ksao_has_grade_scale = self.check_score_type('ksao', GRADE)
        total_kpi_score = self.get_annual_rating(KPI) if kpi_has_grade_scale else 0
        total_ksao_score = self.get_annual_rating(KSA) if ksao_has_grade_scale else 0

        for appraiser_config in self.instance.appraiser_configs.all():
            kpi_score = self.calculate_kpi_score(appraiser_config)
            ksao_score = self.calculate_ksao_score(appraiser_config)
            if not kpi_has_grade_scale:
                total_kpi_score += kpi_score
            if not ksao_has_grade_scale:
                total_ksao_score += ksao_score

        return {
            'kpi_score': round(total_kpi_score, 2) if not kpi_has_grade_scale else total_kpi_score,
            'ksao_score': round(total_ksao_score, 2) if not ksao_has_grade_scale else total_ksao_score
        }

    def save_overall_rating(self):
        self.instance.overall_rating = self.calculate_overall_rating()
        self.instance.save()

    def save_total_score(self):
        self.instance.total_score = self.calculate_overall_rating()
        self.instance.save()


class setDefaultScoreForAppraisal:
    def __init__(self,
                 appraiser_config: KAARAppraiserConfig,
                 sub_performance_appraisal_slot: SubPerformanceAppraisalSlot = None
                 ):
        self.appraiser_config = appraiser_config
        self.kaar_appraisal = appraiser_config.kaar_appraisal
        self.sub_performance_appraisal_slot = sub_performance_appraisal_slot \
                                            or self.kaar_appraisal.sub_performance_appraisal_slot

    def get_default_scores(self):
        return self.sub_performance_appraisal_slot.default_scores.values(
            'question_type', 'score', 'grade_score'
        )

    def get_supervisor_evaluation(self):
        return getattr(self.appraiser_config, 'supervisor_evaluation', None)

    def get_scale_config(self, question_type):
        scale_setting = getattr(self.sub_performance_appraisal_slot, 'kaar_score_setting', None)
        if not scale_setting:
            return
        return getattr(scale_setting, question_type, None)

    def set_default_score(self):
        kaar_default_scores = self.get_default_scores()
        supervisor_evaluation = self.get_supervisor_evaluation()
        if not supervisor_evaluation and supervisor_evaluation.set_default_rating:
            return

        scale_type_to_field_mapper = {
            GRADE: 'grade_score',
            DEFAULT: 'score',
            RANGE: 'score'
        }

        question_type_detail_mapper = {
            KPI: {'field': 'kpi_score', 'scale_type': self.get_scale_config(KPI).scale_type},
            KSA: {'field': 'ksao_score', 'scale_type': self.get_scale_config('ksao').scale_type}
        }
        overall_rating = {}
        for item in kaar_default_scores:
            question_detail = question_type_detail_mapper[item.get('question_type')]
            overall_rating[question_detail['field']] = item.get(
                scale_type_to_field_mapper[question_detail['scale_type']]
            )

        self.kaar_appraisal.overall_rating = overall_rating
        self.kaar_appraisal.save()


class ForwardAppraisalQuestions:
    def __init__(
            self,
            appraiser_config: KAARAppraiserConfig,
            performance_appraisal_slot: SubPerformanceAppraisalSlot,
            authenticated_user: User
    ):
        self.appraiser_config = appraiser_config
        self.authenticated_user = authenticated_user
        self.appraiser_type = appraiser_config.appraiser_type
        self.kaar_appraisal = appraiser_config.kaar_appraisal
        self.appraisee = appraiser_config.kaar_appraisal.appraisee
        self.performance_appraisal_slot = performance_appraisal_slot

    @property
    def next_appraiser_type(self):
        return {
            SELF_APPRAISAL: SUPERVISOR_APPRAISAL,
            SUPERVISOR_APPRAISAL: REVIEWER_EVALUATION,
            REVIEWER_EVALUATION: SELF_APPRAISAL,
        }[self.appraiser_type]

    @property
    def kaar_form_design(self):
        return get_kaar_form_designs(self.performance_appraisal_slot)

    def generate_ksao_questions(self):
        if self.next_appraiser_type != SUPERVISOR_APPRAISAL:
            return
        assigned_ksao = self.appraisee.assigned_ksao.all()
        if not assigned_ksao:
            return
        ksao_question_set, _ = KAARQuestionSet.objects.update_or_create(
            kaar_appraisal=self.appraiser_config.kaar_appraisal,
            name="Competencies",
            question_type=KSA
        )
        answer_choice = generate_kaar_answer_type(
            kaar_form_design=self.kaar_form_design,
            question_type=KSA
        )
        for user_ksao in assigned_ksao:
            KSAOQuestion.objects.update_or_create(
                question_set=ksao_question_set,
                ksao=user_ksao,
                defaults=answer_choice
            )

    @property
    def can_generate_question_set(self):
        return self.kaar_form_design and self.kaar_form_design.add_feedback and \
                self.kaar_form_design.generic_question_set and \
                self.kaar_form_design.generic_question_set.sections.exists()

    def generate_generic_question_set(self):
        if not self.can_generate_question_set:
            return
        generic_question_set = self.kaar_form_design.generic_question_set

        from irhrs.appraisal.utils.generate_question_set import GenerateQuestionSet
        kaar_question_set, _ = KAARQuestionSet.objects.get_or_create(
            kaar_appraisal=self.kaar_appraisal,
            name="PA Question Set",
            question_type=PA_QUESTION_SET
        )
        for section in generic_question_set.sections.all():
            generic_questions = GenerateQuestionSet.get_generic_question_set(
                self.appraisee, section
            )
            for question in generic_questions:
                GenericQuestionSet.objects.update_or_create(
                    question_set=kaar_question_set, generic_question=question
                )
        if not kaar_question_set.generic_questions.exists():
            kaar_question_set.delete()
        return

    @property
    def next_appraiser_qs(self):
        return self.kaar_appraisal.appraiser_configs.filter(appraiser_type=self.next_appraiser_type)

    def complete_kaar_appraisal(self):
        if self.appraiser_config.question_status != SUBMITTED or self.kaar_appraisal.status == COMPLETED:
            return
        if (not self.can_generate_question_set and self.appraiser_type == REVIEWER_EVALUATION) or (
                self.appraiser_type == SELF_APPRAISAL and
                self.kaar_appraisal.question_set.filter(question_type=PA_QUESTION_SET).exists()):
            self.kaar_appraisal.status = COMPLETED
            self.kaar_appraisal.save()

    def display_all_data_to_appraisee(self):
        if self.appraiser_type != REVIEWER_EVALUATION:
            return
        self.kaar_appraisal.display_to_appraisee = True
        self.kaar_appraisal.save()

    def send_question_to_next_appraiser(self):
        if self.appraiser_config.question_status != SUBMITTED or self.kaar_appraisal.status == COMPLETED \
                or self.kaar_appraisal.question_set.filter(question_type=PA_QUESTION_SET).exists():
            return

        if self.next_appraiser_type in [SUPERVISOR_APPRAISAL, REVIEWER_EVALUATION]:
            self.generate_ksao_questions()
            self.next_appraiser_qs.update(question_status=RECEIVED)
            calc = CalculateKaarScore(self.kaar_appraisal)
            calc.save_total_score()
        else:
            self.generate_generic_question_set()
            self.display_all_data_to_appraisee()

    def send_notification_to_appraiser(self):
        if self.kaar_appraisal.status == COMPLETED:
            return
        for appraiser_config in self.next_appraiser_qs:
            add_notification(
                text=f"Performance Appraisal Review Forms has been assigned to you.",
                recipient=appraiser_config.appraiser,
                action=appraiser_config,
                actor=self.authenticated_user,
                url=f'/user/pa/appraisal/{self.performance_appraisal_slot.id}/kaarForms'
            )


class ResendToAppraiser:
    def __init__(
        self,
        kaar_appraisal: KeyAchievementAndRatingAppraisal,
        authenticated_user: User
    ):
        self.kaar_appraisal = kaar_appraisal
        self.authenticated_user = authenticated_user

    def get_appraiser(self, appraiser_type):
        return self.kaar_appraisal.appraiser_configs.filter(appraiser_type=appraiser_type)

    def resend_to_supervisor(self):
        supervisor_appraiser_qs = self.get_appraiser(SUPERVISOR_APPRAISAL)
        self.get_appraiser(SUPERVISOR_APPRAISAL).update(question_status=RECEIVED)
        self.get_appraiser(REVIEWER_EVALUATION).update(question_status=GENERATED)
        sub_performance_appraisal_id = self.kaar_appraisal.sub_performance_appraisal_slot.id
        appraisee = self.kaar_appraisal.appraisee
        for appraiser_config in supervisor_appraiser_qs:
            add_notification(
                text=f"Performance Appraisal Review Forms of "
                     f"{appraisee} has been Re-assigned to you.",
                recipient=appraiser_config.appraiser,
                action=appraiser_config,
                actor=self.authenticated_user,
                url=f'/user/pa/appraisal/{sub_performance_appraisal_id}/kaarForms'
            )


class CreateKAARScore:
    def __init__(self, instance: ScoreAndScalingConfig, data, context):
        self.instance = instance
        self.scale_type = instance.scale_type
        self.data = data
        self.context = context

    @property
    def serializer_mapper(self):
        return {
            DEFAULT: GradeAndDefaultScalingSerializer,
            GRADE: GradeAndDefaultScalingSerializer,
            RANGE: RangeScoreSerializer
        }

    @property
    def model_mapper(self):
        return {
            DEFAULT: GradeAndDefaultScaling,
            GRADE: GradeAndDefaultScaling,
            RANGE: RangeScore
        }

    @property
    def serializer_class(self):
        return self.serializer_mapper.get(self.scale_type)

    @property
    def model_class(self):
        return self.model_mapper.get(self.scale_type)

    def create_range_score(self):
        ser = self.serializer_class(data=self.data, context=self.context)
        ser.is_valid(raise_exception=True)
        return ser.save()

    def create_default_and_grade_score(self):
        _validate_repeated_data(
            data=self.data,
            key='name',
            message='Duplicate name supplied.'
        )
        _validate_repeated_data(
            data=self.data,
            key='score',
            message='Duplicate score supplied.'
        )
        ser = self.serializer_class(data=self.data, context=self.context, many=True)
        ser.is_valid(raise_exception=True)
        self.instance.grade_and_default_scales.all().delete()
        return ser.save()

    def create_scores(self):
        if self.scale_type != RANGE:
            return self.create_default_and_grade_score()
        return self.create_range_score()


class UpdateKAARScores(CreateKAARScore):
    def update_range_scores(self):
        scale_instance = self.model_class.objects.get(id=self.data.pop('id'))
        ser = self.serializer_class(instance=scale_instance, data=self.data, partial=True)
        ser.is_valid(raise_exception=True)
        return ser.save()

    def update_scores(self):
        if self.scale_type == RANGE:
            return self.update_range_scores()
        return self.create_default_and_grade_score()

class CalculateKpiScore():
    def __init__(self, instance: KeyAchievementAndRatingAppraisal):
        self.instance = instance
        self.sub_performance_appraisal_slot = instance.sub_performance_appraisal_slot

    @property
    def scale_config(self):
        return getattr(self.sub_performance_appraisal_slot, 'kaar_score_setting', None)

    def get_annual_rating(self, question_type):
        return nested_getattr(
                self.get_question_set(question_type), 'annual_rating.final_score', default=None
            )

    def get_question_set(self, question_type):
        return self.instance.question_set.filter(question_type=question_type).first()

    def calculate_self_appraiser_score(self, appraiser_config: KAARAppraiserConfig):
        if not self.scale_config:
            return

        if nested_getattr(self.scale_config, 'kpi.scale_type') != GRADE:
            total_score = appraiser_config.kpi_scores.aggregate(
                total_score=Sum(
                    F('score') * 0.01 * F('question__extended_individual_kpi__weightage')
                )).get('total_score') or 0
            return round(total_score, 2)
        else:
            return self.get_annual_rating(KPI)
