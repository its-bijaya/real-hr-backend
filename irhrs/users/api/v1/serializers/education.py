from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField

from irhrs.core.validators import key_exists
from irhrs.users.api.v1.serializers.user_serializer_common import \
    UserSerializerMixin
from irhrs.users.models.education_and_training import UserEducation


class UserEducationSerializer(UserSerializerMixin):
    class Meta:
        model = UserEducation
        fields = ('degree', 'field', 'institution', 'university',
                  'marks_type', 'marks', 'from_year', 'to_year',
                  'is_current', 'id')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            if 'degree' in fields:
                fields['degree'] = ReadOnlyField(source='get_degree_display')
        return fields

    def validate(self, data):
        # TODO @ravi: refactor this as per our discussion
        # Take values from data dictionary.
        # If not defined in dictionary, get it from instance,
        # If not instance, set None
        degree = data.get('degree') if key_exists(
            'degree', data) else \
            self.instance.degree if self.instance else None
        field = data.get('field') if key_exists(
            'field', data) else \
            self.instance.field if self.instance else None
        qs = UserEducation.objects.filter(
            degree=degree, field=field,
            user=self.context.get('user'))
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f" Degree '{degree}' and Field '{field}' "
                                  f"already exists for user.")
        is_current = data.get('is_current') if key_exists(
            'is_current', data) else \
            self.instance.is_current if self.instance else None

        marks = data.get('marks') if key_exists('marks', data) else \
            self.instance.marks if self.instance else None

        marks_type = data.get('marks_type') if key_exists(
            'marks_type', data) else \
            self.instance.marks_type if self.instance else None

        to_year = data.get('to_year') if key_exists('to_year', data) else\
            self.instance.to_year if self.instance else None

        from_year = data.get('from_year') if key_exists(
            'from_year', data) else \
            self.instance.from_year if self.instance else None

        if is_current:
            if marks:
                raise ValidationError("Marks is set but is current")
            if marks_type:
                raise ValidationError("Marks Type is set but is current")
            if to_year:
                raise ValidationError("Passed Year is set but is current")
        else:
            if not to_year:
                raise ValidationError("End year must be defined if not current")
            if to_year:
                if from_year >= to_year:
                    raise ValidationError("Passed year must be less than "
                                          "Started year")
            if not marks_type or not marks:
                raise ValidationError("Marks and Marks Type must be set if "
                                      "not current")
            if marks_type == 'cgpa':
                import re
                if not re.fullmatch(r'\d{1}\.\d{1,2}', str(marks)):
                    raise ValidationError("The number is not a valid CGPA")
            elif marks_type == 'percentage':
                if marks < 0 or marks > 100:
                    raise ValidationError("The percentage is not valid.")
        return super().validate(data)
