import logging

from django.core.cache import cache as dj_cache
from django.db import transaction
from django.db.models import Q, Max
from django_q.tasks import async_task
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from irhrs.appraisal.api.v1.serializers.question_set import AppraisalQuestionsListSerializer
from irhrs.appraisal.constants import KSA, KRA, SELF_APPRAISAL, SENT, KPI, CONFIRMED, \
    KEY_ACHIEVEMENTS_AND_RATING, GENERATED, NOT_GENERATED, REGENERATED, ACTIVE, RECEIVED, SAVED, \
    SUBMITTED
from irhrs.appraisal.models.KAAR_question import KAARQuestionSet, KPIQuestion
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal, \
    KAARAppraiserConfig
from irhrs.appraisal.models.kpi import ExtendedIndividualKPI
from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlot
from irhrs.appraisal.models.form_design import PerformanceAppraisalFormDesign
from irhrs.appraisal.models.question_set import PerformanceAppraisalQuestion
from irhrs.appraisal.utils.kaar_appraisal import generate_kaar_answer_type
from irhrs.appraisal.utils.util import AppraisalSettingBaseFilterMixin
from irhrs.core.mixins.serializers import DummySerializer
from irhrs.core.utils import nested_getattr
from irhrs.notification.utils import notify_organization
from irhrs.permission.constants.permissions import PERFORMANCE_APPRAISAL_PERMISSION
from irhrs.questionnaire.models.helpers import LONG, SHORT, RATING_SCALE

logger = logging.getLogger(__name__)


class BaseForGenerateQuestionSet:
    @classmethod
    def get_appraisals(cls, sub_performance_appraisal_slot):
        appraisal = Appraisal.objects.filter(
            sub_performance_appraisal_slot=sub_performance_appraisal_slot
        )
        _ = appraisal.update(answer_committed=False, approved=False)
        return appraisal

    @classmethod
    def get_form_designs(cls, sub_performance_appraisal_slot):
        return PerformanceAppraisalFormDesign.objects.filter(
            sub_performance_appraisal_slot=sub_performance_appraisal_slot
        )

    @classmethod
    def get_kaar_form_designs(cls, sub_performance_appraisal_slot):
        return getattr(sub_performance_appraisal_slot, 'kaar_form_design', None)

    @classmethod
    def generate_answer_type(cls, form_design, question_type=KSA):
        qs_answer_choice = form_design.answer_types.filter(
            question_type=question_type
        )
        rating_scale = qs_answer_choice.exclude(answer_type__in=[LONG, SHORT]).first()
        text = qs_answer_choice.filter(answer_type__in=[LONG, SHORT]).first()
        return {
            'answer_choices': rating_scale.answer_type,
            'answers': [],
            'description': rating_scale.description,
            'is_mandatory': rating_scale.is_mandatory,
            'rating_scale': 5,
            'remarks': '',
            'remarks_required': text.is_mandatory,
            'score': 0,
            'weightage': 5,
            'is_open_ended': True
        }

    @classmethod
    def generate_kaar_answer_type(cls, kaar_form_design, question_type=KSA):
        return generate_kaar_answer_type(kaar_form_design, question_type)

    @classmethod
    def get_ksa_list(cls, user):
        return user.assigned_ksao.values_list('ksa__name', flat=True)

    @classmethod
    def get_kpi_list(cls, user, fiscal_year):
        assigned_kpi = user.individual_kpis.filter(
            status=CONFIRMED, fiscal_year=fiscal_year, is_archived=False).first()
        extended_kpis = ExtendedIndividualKPI.objects.none()
        if assigned_kpi:
            extended_kpis = assigned_kpi.extended_individual_kpis.all()
        return extended_kpis

    @classmethod
    def get_kra_list(cls, user):
        if user.current_experience:
            return user.current_experience.user_result_areas.filter(
                key_result_area=True
            ).values_list('result_area__title', flat=True)
        else:
            return []


def generate_question_set_wrapper(klass, performance_appraisal_slot, organization):
    # this function created because classmethod can't be pickled with cython
    # https://stackoverflow.com/questions/4677012/python-cant-pickle-type-x-attribute-lookup-failed
    cls = GenerateQuestionSet
    cls.start_generating(klass, performance_appraisal_slot, organization)


class GenerateQuestionSet(BaseForGenerateQuestionSet):
    @classmethod
    def generate_question_according_to_type(cls, user, form_design, question_type=KSA):
        generated_question = []
        answer_choice = cls.generate_answer_type(
            form_design=form_design,
            question_type=question_type
        )
        is_mandatory = answer_choice.pop('is_mandatory')

        for index, value in enumerate(getattr(cls, f'get_{question_type}_list')(user)):
            generated_question.append(
                {
                    'order': index,
                    'is_mandatory': is_mandatory,
                    'question': {
                        'title': f'Rate \'{value}\' with appropriate description?',
                        **answer_choice
                    }
                }
            )
        return generated_question

    @classmethod
    def generate_question_for_kpi(cls, user, form_design, fiscal_year, question_type=KPI):
        generated_question = []
        answer_choice = cls.generate_answer_type(
            form_design=form_design,
            question_type=question_type
        )
        is_mandatory = answer_choice.pop('is_mandatory')

        for index, value in enumerate(getattr(cls, f'get_{question_type}_list')(user, fiscal_year)):
            individual_kpi = value.individual_kpi
            generated_question.append(
                {
                    'order': index,
                    'is_mandatory': is_mandatory,
                    'question': {
                        'individual_kpi_id': individual_kpi.id,
                        'title': f'Rate \'{individual_kpi.title}\' with appropriate description?',
                        'success_criteria': value.success_criteria,
                        'kpi_weightage': value.weightage,
                        **answer_choice
                    }
                }
            )
        return generated_question

    @staticmethod
    def get_generic_question_set(user, section):
        return PerformanceAppraisalQuestion.objects.filter(
            question_section=section
        ).filter(
            Q(
                Q(appraisal_user_type__branches__isnull=True) |
                Q(appraisal_user_type__branches=user.detail.branch)
            ),
            Q(
                Q(appraisal_user_type__divisions__isnull=True) |
                Q(appraisal_user_type__divisions=user.detail.division)
            ),
            Q(
                Q(appraisal_user_type__job_titles__isnull=True) |
                Q(appraisal_user_type__job_titles=user.detail.job_title)
            ),
            Q(
                Q(appraisal_user_type__employment_levels__isnull=True) |
                Q(appraisal_user_type__employment_levels=user.detail.employment_level)
            )
        )

    @classmethod
    def generate_questions_for_general_question_set(cls, user, question_set):
        general_sections = []
        for section in question_set.sections.all():
            individual_section = {
                    'title': section.title,
                    'description': section.description,
                    'questions': []
            }
            generic_questions = cls.get_generic_question_set(user, section)
            individual_section["questions"].extend(
                AppraisalQuestionsListSerializer(
                    generic_questions,
                    many=True,
                ).data
            )
            general_sections.append(individual_section)
        return general_sections

    @classmethod
    def generate(cls, appraisal, form_design, fiscal_year=None):
        sections = []
        if form_design and form_design.include_ksa:
            sections.append(
                {
                    'title': 'KSA',
                    'description': '',
                    'questions': cls.generate_question_according_to_type(
                        user=appraisal.appraisee,
                        form_design=form_design,
                        question_type=KSA
                    )
                }
            )

        if form_design and form_design.include_kra:
            sections.append(
                {
                    'title': 'KRA',
                    'description': '',
                    'questions': cls.generate_question_according_to_type(
                        user=appraisal.appraisee,
                        form_design=form_design,
                        question_type=KRA
                    )
                }
            )

        if form_design and form_design.include_kpi:
            sections.append(
                {
                    'title': 'KPI',
                    'description': '',
                    'questions': cls.generate_question_for_kpi(
                        user=appraisal.appraisee,
                        form_design=form_design,
                        fiscal_year=fiscal_year,
                        question_type=KPI
                    )
                }
            )

        if form_design and form_design.generic_question_set:
            generic_sections = cls.generate_questions_for_general_question_set(
                user=appraisal.appraisee,
                question_set=form_design.generic_question_set
            )
            sections.extend(generic_sections)

        if form_design and form_design.add_feedback:
            sections.append(
                {
                    'title': 'Feedback',
                    'description': '',
                    'questions': [
                        {
                            'order': 0,
                            'question': {
                                'title': 'You may add some feedback '
                                         'regarding this performance appraisal.',
                                'answer_choices': LONG,
                                'answers': [],
                                'description': '',
                                'rating_scale': 0,
                                'remarks': '',
                                'remarks_required': False,
                                'score': 0,
                                'weightage': 0,
                                'is_open_ended': True
                            },
                            'is_mandatory': True,
                        }
                    ]
                }
            )
        return sections

    @classmethod
    def generate_kaar_question_set(cls, user, kaar_appraisal, kaar_form_design, fiscal_year=None):

        delete_question_set = True
        if kaar_form_design:
            if kaar_form_design.include_kpi:
                individual_kpi = user.individual_kpis.filter(
                    status=CONFIRMED,
                    fiscal_year=fiscal_year,
                    is_archived=False
                ).first()
                if individual_kpi and individual_kpi.extended_individual_kpis.exists():
                    delete_question_set = False
                    answer_choice = cls.generate_kaar_answer_type(
                        kaar_form_design=kaar_form_design,
                        question_type=KPI
                    )
                    kpi_question_set = KAARQuestionSet.objects.create(
                        kaar_appraisal=kaar_appraisal,
                        name="Key Performance Indicator",
                        question_type=KPI
                    )
                    for extended_kpi in individual_kpi.extended_individual_kpis.all():
                        KPIQuestion.objects.create(
                            question_set=kpi_question_set,
                            extended_individual_kpi=extended_kpi,
                            **answer_choice
                        )
        if delete_question_set:
            kaar_appraisal.question_set.all().delete()
        kaar_appraisal.status = ACTIVE
        kaar_appraisal.save()
        return kaar_appraisal

    @classmethod
    def generate_for_three_sixty_appraisal(cls, sub_performance_appraisal_slot,
                                           organization, fiscal_year):
        if sub_performance_appraisal_slot.modes.filter(appraisal_type=SELF_APPRAISAL).exists():
            filter_mixin = AppraisalSettingBaseFilterMixin()

            setattr(filter_mixin, 'performance_appraisal_slot', sub_performance_appraisal_slot)
            setattr(filter_mixin, 'appraisal_type', SELF_APPRAISAL)

            users = filter_mixin.get_queryset(union=False).filter(detail__organization=organization)

            for user in users:
                _ = Appraisal.objects.get_or_create(
                    sub_performance_appraisal_slot=sub_performance_appraisal_slot,
                    appraisee=user,
                    appraiser=user,
                    appraisal_type=SELF_APPRAISAL
                )
        else:
            cls.get_appraisals(sub_performance_appraisal_slot).filter(
                appraisal_type=SELF_APPRAISAL
            ).delete()

        appraisals = cls.get_appraisals(sub_performance_appraisal_slot)
        form_designs = cls.get_form_designs(sub_performance_appraisal_slot)

        for appraisal in appraisals:
            try:
                form_design = form_designs.get(appraisal_type=appraisal.appraisal_type)
                question_set = {
                    'title': 'Default Set',
                    'description': form_design.instruction_for_evaluator,
                    'sections': cls.generate(
                        appraisal=appraisal, form_design=form_design, fiscal_year=fiscal_year
                    )
                }
                appraisal.question_set = question_set
                appraisal.start_date = None
                appraisal.deadline = None
                appraisal.committed_at = None
                appraisal.approved_at = None
                appraisal.total_score = calculate_total_score(question_set, sub_performance_appraisal_slot)
                appraisal.score_deduction_factor = 0
            except PerformanceAppraisalFormDesign.DoesNotExist:
                appraisal.question_set = {}
                dj_cache.set(
                    f'error_question_set_generation_{sub_performance_appraisal_slot.id}',
                    True,
                    None
                )

                logging.debug(
                    f'Unable to generate question set for {appraisal.appraisee.full_name} as'
                    f' appraisee and {appraisal.appraiser.full_name} as appraiser.'
                )
            appraisal.save()

    @classmethod
    def generate_key_achievement_and_rating_appraisal(cls, sub_performance_appraisal_slot,
                                                      organization, fiscal_year):
        form_design = cls.get_kaar_form_designs(sub_performance_appraisal_slot)
        filter_mixin = AppraisalSettingBaseFilterMixin()

        setattr(filter_mixin, 'performance_appraisal_slot', sub_performance_appraisal_slot)
        setattr(filter_mixin, 'appraisal_type', SELF_APPRAISAL)

        question_generated_users = KAARAppraiserConfig.objects.filter(
            kaar_appraisal__sub_performance_appraisal_slot=sub_performance_appraisal_slot,
            appraiser_type=SELF_APPRAISAL,
            question_status__in=(RECEIVED, SAVED, SUBMITTED)
        ).values_list('kaar_appraisal__appraisee', flat=True)

        users = filter_mixin.get_queryset(union=False).filter(
            detail__organization=organization
        ).exclude(id__in=question_generated_users)

        create_self_appraiser = sub_performance_appraisal_slot.modes.filter(
            appraisal_type=SELF_APPRAISAL
        ).exists()
        for user in users:
            kaar_appraisal, _ = KeyAchievementAndRatingAppraisal.objects.get_or_create(
                sub_performance_appraisal_slot=sub_performance_appraisal_slot,
                appraisee=user)
            if kaar_appraisal.question_set.exists():
                kaar_appraisal.question_set.all().delete()
            cls.generate_kaar_question_set(user, kaar_appraisal, form_design, fiscal_year)
            if not create_self_appraiser:
                continue
            if not kaar_appraisal.appraiser_configs.filter(
                appraiser=user,
                appraiser_type=SELF_APPRAISAL
            ).exists():
                KAARAppraiserConfig.objects.create(
                    kaar_appraisal=kaar_appraisal,
                    appraiser=user,
                    appraiser_type=SELF_APPRAISAL
                )
            if kaar_appraisal.question_set.exists():
                kaar_appraisal.appraiser_configs.update(question_status=GENERATED)

        question_set_status = GENERATED if\
            sub_performance_appraisal_slot.question_set_status == NOT_GENERATED else REGENERATED
        sub_performance_appraisal_slot.question_set_status = question_set_status
        sub_performance_appraisal_slot.save()

    @staticmethod
    def start_generating(cls, sub_performance_appraisal_slot, organization):
        performance_appraisal_year = sub_performance_appraisal_slot.performance_appraisal_year
        fiscal_year = performance_appraisal_year.year
        performance_appraisal_type = performance_appraisal_year.performance_appraisal_type

        if performance_appraisal_type == KEY_ACHIEVEMENTS_AND_RATING:
            cls.generate_key_achievement_and_rating_appraisal(
                sub_performance_appraisal_slot, organization, fiscal_year
            )
        else:
            cls.generate_for_three_sixty_appraisal(
                sub_performance_appraisal_slot, organization, fiscal_year
            )

        text = 'Successfully generated question set for performance appraisal.'
        if dj_cache.get(f'error_question_set_generation_{sub_performance_appraisal_slot.id}',
                        False):
            text = 'Generated question set for performance appraisal with some failed generations.'
        notify_organization(
            text=text,
            action=sub_performance_appraisal_slot,
            organization=sub_performance_appraisal_slot.performance_appraisal_year.organization,
            permissions=[PERFORMANCE_APPRAISAL_PERMISSION],
            url=f'/'
        )
        dj_cache.set(
            f'block_question_set_generation_{sub_performance_appraisal_slot.id}',
            False,
            None
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='generate/question-set',
        serializer_class=DummySerializer
    )
    def generate_question_for_appraisee(self, request, *args, **kwargs):
        appraisals = self.performance_appraisal_slot.appraisals.all()
        performance_appraisal_slot_weights = self.performance_appraisal_slot.weight.all()
        appraisal_type = nested_getattr(
            self.performance_appraisal_slot,
            'performance_appraisal_year.performance_appraisal_type'
        )
        if (appraisal_type != KEY_ACHIEVEMENTS_AND_RATING and
                self.performance_appraisal_slot.question_set_status == SENT):
            raise ValidationError("You cannot regenerate forms when forms are already sent.")

        if appraisals and performance_appraisal_slot_weights:
            raise ValidationError({
                'error': f"You cannot regenerate forms when appraisal_score and "
                         f"performance_appraisal_slot_weights are already set"
            })

        if dj_cache.get(f'block_question_set_generation_{self.performance_appraisal_slot.id}',
                        False):
            return Response({
                'detail': 'Question set generation is been processed in background.'
            })

        dj_cache.set(
            f'block_question_set_generation_{self.performance_appraisal_slot.id}',
            True,
            None
        )
        _ = async_task(
            generate_question_set_wrapper,
            self.__class__,
            self.performance_appraisal_slot,
            self.organization
        )
        return Response(
            {'detail': 'Your task has been sent to background. You will be notified shortly.'},
            status=status.HTTP_200_OK
        )


def calculate_total_score(question_set, sub_performance_appraisal_slot):
    '''
    we need to find sum of score whose structure is as follow
    question_set -> section[] -> questions[] -> question -> score

    obtained = total score obtained in rating-scale questions
    final = Max rating scale score * total number of questions
    where,
    [] symbolizes list of object,
    -> symbolizes nested structure of data
    '''
    max_rating_scale_score = SubPerformanceAppraisalSlot.objects.get(
        id=sub_performance_appraisal_slot.id
    ).score_and_scaling_setting.all().aggregate(Max('score'))['score__max'] or 0
    sections = question_set['sections']
    total_score = 0
    for section in sections:
        questions = section['questions']
        for question in questions:
            actual_question = question.get('question')
            if actual_question:
                if actual_question.get('answer_choices') == RATING_SCALE:
                    total_score += max_rating_scale_score
    return total_score



def calculate_obtained_score(question_set):
    '''
    we need to find sum of score whose structure is as follow
    question_set -> section[] -> questions[] -> question -> score

    obtained = total score obtained in rating-scale questions
    final = Max rating scale score * total number of questions
    where,
    [] symbolizes list of object,
    -> symbolizes nested structure of data
    '''
    obtained_score = sum(
        map(
            lambda sections: sum(
                map(
                    lambda questions: questions['question']['score']
                    if questions['question']['answer_choices'] == RATING_SCALE else 0,
                    sections['questions']
                )
            ),
            question_set['sections']
        )
    )
    return obtained_score
