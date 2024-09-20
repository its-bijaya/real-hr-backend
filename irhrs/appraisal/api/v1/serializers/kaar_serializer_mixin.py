from django.core.exceptions import ValidationError

from irhrs.appraisal.constants import GRADE, RANGE
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.questionnaire.models.helpers import LONG


class KAARBaseMixin:
    question_type = ""

    @property
    def question_type_to_form_deign_field_mapper(self):
        return {
            'kpi': 'kpi',
            'ksao': 'ksa',
            'kra': 'kra'
        }

    def get_form_design_field(self):
        return self.question_type_to_form_deign_field_mapper.get(self.question_type, None)

    def get_kaar_form_design(self):
        kaar_form_design = getattr(self.sub_performance_appraisal_slot, 'kaar_form_design', None)
        if not kaar_form_design:
            raise ValidationError({'error': "Form design is not created for this appraisal."})
        return kaar_form_design

    def get_answer_type(self, question_type):
        answer_type = self.get_kaar_form_design().kaar_answer_types.filter(
            question_type=question_type,
            answer_type=LONG
        ).first()
        return answer_type

    def get_scale_config(self):
        scale_setting = getattr(self.sub_performance_appraisal_slot, 'kaar_score_setting', None)
        if not scale_setting:
            raise ValidationError({'score': 'Score setting is not created.'})

        scale_config = getattr(scale_setting, self.question_type, None)

        if not scale_config:
            raise ValidationError({'score': f'score setting for {self.question_type} not found.'})
        return scale_config

    def validate_range_score(self, value):
        scale_config = self.get_scale_config()
        range_score = getattr(scale_config, 'range_score', None)
        if not range_score:
            raise ValidationError({
                'score': 'start range and end range is not defined in score setting.'
            })
        if value is None:
            raise ValidationError({
                'score': 'Score is required.'
            })
        if not range_score.start_range <= value <= range_score.end_range:
            raise ValidationError({
                'score': f'score should be in between {range_score.start_range} '
                         f'to {range_score.end_range}'
            })

    def validate_default_score(self, value):
        scale_config = self.get_scale_config()
        default_and_grade_scale = scale_config.grade_and_default_scales.values_list(
            'score', flat=True
        )
        if value not in default_and_grade_scale:
            raise ValidationError({'score': 'Please submit valid score.'})

    def validate_grade_score_(self, value):
        scale_config = self.get_scale_config()
        if scale_config.scale_type != GRADE:
            raise ValidationError({'grade_score': "Can't assign score in grade."})
        default_and_grade_scale = scale_config.grade_and_default_scales.values_list(
            'name', flat=True
        )
        if value not in default_and_grade_scale:
            raise ValidationError({'score': 'Please submit valid score.'})

    @property
    def sub_performance_appraisal_slot(self):
        return self.context['sub_performance_appraisal_slot']


class KAARScoreSerializerMixin(KAARBaseMixin, DynamicFieldsModelSerializer):
    def validate_score(self, value):
        scale_config = self.get_scale_config()
        if scale_config.scale_type == RANGE:
            self.validate_range_score(value)
        elif scale_config.scale_type == GRADE:
            raise ValidationError({'score': "Can't assign Grade in score."})
        else:
            self.validate_default_score(value)
        return value

    def validate_grade_score(self, value):
        self.validate_grade_score_(value)
        return value

    def validate_remarks(self, value):
        form_design_field = self.get_kaar_form_design()
        is_mandatory = getattr(self.get_answer_type(self.get_form_design_field()), 'is_mandatory', False)
        if getattr(form_design_field, f"include_{self.get_form_design_field()}") \
                and is_mandatory and not value:
            raise ValidationError({'remarks': 'Remarks field is required.'})
        return value

