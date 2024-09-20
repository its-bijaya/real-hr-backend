from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from irhrs.common.api.serializers.skill import SkillSerializer, \
    SkillHelperSerializer
from irhrs.common.models import Skill
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils.change_request import create_add_change_request, get_changes
from irhrs.core.utils.dependency import get_dependency
from irhrs.core.validation_messages import END_DATE_CANNOT_SET_MESSAGE
from irhrs.core.validators import (
    validate_title, validate_userdetail_replacing,
    validate_start_end_dob_doj_dates, validate_contract_current,
    validate_end_date_is_current,
    throw_validation_error)
from irhrs.hris.models import ChangeType
from irhrs.hris.utils import validate_experience_conflicts
from irhrs.notification.utils import add_notification
from irhrs.organization.api.v1.serializers.branch import \
    OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import \
    EmploymentStatusSerializer, \
    EmploymentLevelSerializer, EmploymentJobTitleSerializer
from irhrs.organization.api.v1.serializers.organization import \
    OrganizationSerializer
from irhrs.organization.models import (
    OrganizationDivision, EmploymentLevel, EmploymentStatus,
    Organization, OrganizationBranch, EmploymentJobTitle
)
from .user_serializer_common import UserSerializerMixin
from ....models.experience import UserExperience, UserExperienceStepHistory

USER = get_user_model()


class UserExperienceStepHistorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = UserExperienceStepHistory
        fields = (
            '__all__'
        )


class UserExperienceSerializer(UserSerializerMixin):
    skill = SkillHelperSerializer(many=True)
    job_title = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=EmploymentJobTitle.objects.all(),
        required=True
    )
    organization = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Organization.objects.all(),
        required=True
    )
    division = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=OrganizationDivision.objects.all(),
        required=True
    )
    employee_level = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=EmploymentLevel.objects.all(),

    )
    employment_status = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=EmploymentStatus.objects.all(),
        allow_null=False,
        required=True
    )
    change_type = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=ChangeType.objects.all(),
    )
    branch = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=OrganizationBranch.objects.all(),
        allow_null=True,
        required=False
    )
    replacing = serializers.PrimaryKeyRelatedField(
        queryset=USER.objects.all(),
        required=False,
        allow_null=True
    )
    is_current = serializers.BooleanField(
        default=True,
    )
    steps_history = UserExperienceStepHistorySerializer(
        source='step_histories',
        many=True,
        read_only=True,
        allow_null=True
    )

    objective = serializers.CharField(max_length=100000, allow_blank=True, required=False)

    class Meta:
        model = UserExperience
        fields = (
            'id', 'job_title', 'organization', 'user', 'is_current',
            'division', 'employee_level', 'employment_status', 'branch',
            'change_type', 'skill', 'start_date', 'current_step',
            'end_date', 'job_description', 'job_specification', 'replacing',
            'steps_history', 'objective', 'in_probation', 'probation_end_date'
        )

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance, data, **kwargs)
        organization = None
        if not data == empty:
            org_slug = data.get('organization')
            if org_slug:
                try:
                    organization = Organization.objects.get(slug=org_slug)
                except:
                    pass

        if not organization and instance and not isinstance(instance,
                                                            (list, QuerySet)):
            organization = instance.organization
        self.organization_value = organization

    @staticmethod
    def has_user_assigned_core_task(instance: UserExperience) -> bool:
        return instance.user_result_areas.exists()

    def run_validation(self, data=empty):
        if not self.organization_value and data != empty:
            try:
                self.organization_value = Organization.objects.get(
                    slug=data.get('organization'))
            except:
                pass
        return super().run_validation(data)

    def get_fields(self):
        from irhrs.hris.api.v1.serializers.onboarding_offboarding import \
            ChangeTypeSerializer
        fields = super().get_fields()
        request = self.context.get('request', None)
        if request and request.method == 'GET':
            if 'job_title' in fields:
                fields.update({'job_title': EmploymentJobTitleSerializer(
                    fields=['title', 'slug'],
                    read_only=True)})
            if 'organization' in fields:
                fields.update(
                    {'organization':
                        OrganizationSerializer(
                            fields=['name', 'slug'],
                            read_only=True)})
            if 'division' in fields:
                fields.update({'division': OrganizationDivisionSerializer(
                    fields=['name', 'slug'],
                    read_only=True)})

            if 'employee_level' in fields:
                fields.update({'employee_level': EmploymentLevelSerializer(
                    fields=['title', 'slug'],
                    read_only=True)})

            if 'employment_status' in fields:
                fields.update({'employment_status': EmploymentStatusSerializer(
                    fields=['title', 'slug'],
                    read_only=True)})

            if 'branch' in fields:
                fields.update({
                    'branch': OrganizationBranchSerializer(
                        fields=['organization', 'name', 'slug'],
                        read_only=True)})

            if 'change_type' in fields:
                fields.update({
                    'change_type': ChangeTypeSerializer(
                        fields=['title', 'slug'],
                        read_only=True)})

            if 'skill' in fields:
                fields.update({
                    'skill': SkillSerializer(many=True)
                })

        return fields

    def validate_job_title(self, job_title):
        if job_title and \
            not job_title.organization == self.organization_value:
            raise ValidationError("Job Title must be of same organization as"
                                  " employee")
        return job_title

    def validate_employee_level(self, employee_level):
        if employee_level and \
            not employee_level.organization == self.organization_value:
            raise ValidationError("Employee Level must be of same organization"
                                  " as employee")
        return employee_level

    def validate_employment_status(self, employment_status):
        if employment_status and \
            not employment_status.organization == self.organization_value:
            raise ValidationError("Employment Status must be of same"
                                  " organization as employee")
        return employment_status

    def validate_change_type(self, change_type):
        if change_type and not change_type.organization == self.organization_value:
            raise ValidationError("Change Type must be of same"
                                  " organization as employee")
        return change_type

    def validate_branch(self, branch):
        if branch and not branch.organization == self.organization_value:
            raise ValidationError("Branch must be of same"
                                  " organization as employee")
        return branch

    def validate_division(self, division):
        if self.instance and self.instance.division != division:
            if self.instance.is_current:
                raise ValidationError(
                    _("You can not change division of current experience.")
                )
            if self.has_user_assigned_core_task(self.instance):
                raise ValidationError(
                    _("You can not change division of experience whose core task is assigned.")
                )

        return division

    def validate(self, attrs):
        from irhrs.payroll.utils.generate import (
            raise_validation_error_if_payroll_in_generated_or_processing_state
        )
        raise_validation_error_if_payroll_in_generated_or_processing_state(
            organization=self.organization_value
        )
        is_current = attrs.get('is_current')
        replacing = attrs.get('replacing')
        user = self.context.get('user') or attrs.get('user')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        employment_status = attrs.get('employment_status')
        current_step = attrs.get('current_step', 0)
        employee_level = attrs.get('employee_level')
        employee_level = employee_level if employee_level else \
            self.instance.employee_level if self.instance else None
        max_step = getattr(employee_level, 'scale_max', 0)

        in_probation = attrs.get('in_probation')
        probation_end_date = attrs.get('probation_end_date')
        if in_probation and not probation_end_date:
            raise ValidationError({
                'probation_end_date': 'Probation end date is required if user is in probation.'
            })
        elif probation_end_date and not in_probation:
            raise ValidationError({
                'probation_end_date': 'Probation end date can not be set for user not in '
                                      'probation.'
            })

        if not in_probation:
            attrs['probation_end_date'] = None

        if current_step > max_step:
            raise ValidationError(
                f"The current step (i.e. {current_step}) exceeds max step "
                f"defined in Employment Level (i.e. {max_step})"
            )
        validate_userdetail_replacing(
            replacing=replacing,
            user=user
        )
        validate_start_end_dob_doj_dates(
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        validate_contract_current(
            employment_status=employment_status,
            end_date=end_date,
            is_current=is_current
        )
        validate_end_date_is_current(
            end_date=end_date,
            is_current=is_current,
            employment_status=employment_status
        )
        validate_experience_conflicts(
            user=user,
            start_date=start_date,
            end_date=end_date,
            instance=getattr(self, 'instance', None),
            is_current=is_current
        )

        if user:
            preceding_experiences = user.user_experiences.filter().order_by('-start_date')
            if end_date:
                preceding_experiences = preceding_experiences.filter(start_date__lte=end_date)
            if self.instance:
                preceding_experiences = preceding_experiences.exclude(id=self.instance.id)
            preceding_experience = preceding_experiences.first()
            if preceding_experience and start_date <= preceding_experience.start_date:
                raise ValidationError({
                    "start_date": _(
                        'Start date must be greater than previous experience start date.'
                    )
                })

            if self.instance:
                # [HRIS-2794] First employment experience end date  can not be changed if second
                # employment experience is available.
                upcoming_experiences_exists = user.user_experiences.filter(
                    start_date__gte=self.instance.start_date
                ).exclude(id=self.instance.id).exists()
                if upcoming_experiences_exists and end_date != self.instance.end_date:
                    raise ValidationError({
                        "end_date": _("Can not change end date when another experience"
                                      " exists after this experience.")
                    })

            # user is None from pre employment

            get_last_payroll_generated_date, installed = get_dependency(
                'irhrs.payroll.utils.helpers.get_last_payroll_generated_date')
            last_paid_date = get_last_payroll_generated_date(user)

            if last_paid_date:
                if not self.instance and start_date <= last_paid_date:
                    raise serializers.ValidationError({
                        'start_date': _("Can not add experience before last payroll generated date"
                                        f" {last_paid_date}.")
                    })
                if end_date and end_date < last_paid_date:
                    raise serializers.ValidationError({
                        'end_date': _("This value can not be before last payroll generated date"
                                      f" {last_paid_date}.")
                    })

                if (
                    self.instance and self.instance.start_date <= last_paid_date and
                    self.instance.start_date != start_date
                ):
                    raise serializers.ValidationError({
                        'start_date': _(
                            "Can not edit this value because payroll has been generated after "
                            "this date.")
                    })

                if (
                    self.instance and
                    self.instance.start_date <= last_paid_date and
                    self.instance.current_step != current_step
                ):
                    raise serializers.ValidationError({
                        'current_step': _("Can not change this value because payroll has been "
                                          "generated using this experience.")
                    })

        if self.instance and self.instance.user_experience_packages.exists():
            errors = {}
            if start_date != self.instance.start_date:
                errors["start_date"] = _("Can not change this value. Payroll "
                                         "package is assigned to this experience.")

            # end date can be changed in this case
            # if end_date != self.instance.end_date:
            #     errors["end_date"] = _("Can not change this value. Payroll "
            #                            "package is assigned to this experience.")

            if errors:
                raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        validated_data.pop('skill', None)
        instance = super().create(validated_data)

        if instance.is_current:
            self.update_experience_is_current(
                instance,
                instance.user
            )

            # add organization to userdetail
            user = instance.user

            # set end_date for old user experience.
            # The previous mechanism for setting end date for old experience
            # is flawed. i.e. it does not work for experiences that has
            # end date (such as contract types).
            preceding_experience = user.user_experiences.exclude(
                pk=instance.pk
            ).order_by('-start_date').first()
            if preceding_experience:
                preceding_experience.is_current = False
                preceding_experience.end_date = (
                    instance.start_date - timezone.timedelta(days=1)
                )
                preceding_experience.save()
        create_add_change_request(
            instance.user, self.Meta.model, data=validated_data,
            category=self.Meta.model._meta.verbose_name.replace(
                "user ", "").title(), approved=True
        )
        add_notification(
            text=f'Your experience detail has been created by HR.',
            recipient=instance.user,
            action=instance.modified_by,
            url='/user/profile/change-request/?status=approved'
        )
        return instance

    def update(self, instance, validated_data):
        if 'skill' in validated_data.keys():
            skills = validated_data.pop('skill', None)
            skill_list = self.create_skill(skills)
            instance.skill.clear()
            instance.skill.add(*skill_list)

        changes = get_changes(instance=instance, new_data=validated_data)

        instance = super().update(instance, validated_data)
        if instance.is_current:
            self.update_experience_is_current(instance,
                                              instance.user)

        # if changes:
        #     create_update_change_request(
        #         instance.user, instance, changes,
        #         category=self.Meta.model._meta.verbose_name.replace(
        #             "user ", "").title(), approved=True
        #     )

        add_notification(
            text=f'Your experience detail has been updated by HR.',
            recipient=instance.user,
            action=instance.modified_by,
            url='/user/profile/change-request/?status=approved'
        )
        return instance

    @staticmethod
    def create_skill(skills):
        skill_list = list()
        if skills:
            for skill in skills:
                name = skill.get('name')
                validate_title(name)
                description = skill.get('description')
                if not description:
                    description = "Description Not Available"
                i, _ = Skill.objects.get_or_create(
                    defaults={'name': name, 'description': description},
                    name__iexact=name
                )
                skill_list.append(i)
        return skill_list

    @staticmethod
    def update_experience_is_current(instance, user):
        UserExperience.objects.filter(
            user=user
        ).update(is_current=False)
        instance.is_current = True
        # update user_detail organization if experience is current
        user_detail = instance.user.detail
        user_detail.organization = instance.organization
        user_detail.branch = instance.branch
        user_detail.division = instance.division
        user_detail.job_title = instance.job_title
        user_detail.employment_level = instance.employee_level
        user_detail.employment_status = instance.employment_status

        user_detail.save()
        instance.save()
        return instance


class UserUpcomingExperienceSerializer(UserExperienceSerializer):
    def validate(self, attrs):
        upcoming = True
        attrs.update({
            'upcoming': upcoming
        })
        is_current = True  # for validation purposes, is reset all the way down
        replacing = attrs.get('replacing')
        user = self.context.get('user') or attrs.get('user')
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        employment_status = attrs.get('employment_status')
        current_step = attrs.get('current_step', 0)
        employee_level = attrs.get('employee_level')
        employee_level = employee_level if employee_level else \
            self.instance.employee_level if self.instance else None
        max_step = getattr(employee_level, 'scale_max', 0)

        if current_step > max_step:
            raise ValidationError(
                f"The current step (i.e. {current_step}) exceeds max step "
                f"defined in Employment Level (i.e. {max_step})"
            )
        validate_userdetail_replacing(
            replacing=replacing,
            user=user
        )  # cannot replace self.
        validate_start_end_dob_doj_dates(
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        validate_contract_current(
            employment_status=employment_status,
            end_date=end_date,
            is_current=is_current
        )
        if end_date:
            if not employment_status.is_contract:
                throw_validation_error(
                    'end_date', END_DATE_CANNOT_SET_MESSAGE
                )
        validate_experience_conflicts(
            user=user,
            start_date=start_date,
            end_date=end_date,
            check_active_conflicts=True,
            instance=getattr(self, 'instance', None),
            is_current=is_current
        )
        attrs.update({
            'is_current': False,
            'upcoming': True
        })
        return attrs


class UserExperienceHistorySerializer(DummySerializer):
    start_date = serializers.DateField()
    text = serializers.CharField()
    change_type = serializers.CharField()
