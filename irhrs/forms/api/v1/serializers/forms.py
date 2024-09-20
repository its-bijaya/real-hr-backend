from django_q.tasks import async_task
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.forms.models import Form, UserForm, UserFormAnswerSheet
from irhrs.forms.models.forms import FormSetting
from irhrs.forms.utils.answer import is_form_filled_yet
from irhrs.forms.api.v1.serializers.questions import FormQuestionSectionSerializer
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.common import get_today
from irhrs.core.utils.common import DummyObject
from irhrs.forms.utils.stats import annotate_last_experience_userform_qs
from irhrs.notification.utils import add_notification
from irhrs.forms.models import FormQuestion


User = get_user_model()


class FormSettingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = FormSetting
        fields = (
            'branch', 'gender', 'employment_type', 'employment_level', 'division',
            'job_title', 'duty_station'
        )


class ListFormSerializer(serializers.ModelSerializer):

    class Meta:
        model = Form
        fields = (
            'id', 'name', 'deadline', 'description', 'disclaimer_text',
            'is_anonymously_fillable', 'is_archived', 'is_draft',
            'is_multiple_submittable', 'organization', 'users_count',
            'is_already_filled', 'uuid'
        )

    users_count = serializers.SerializerMethodField()
    is_already_filled = serializers.SerializerMethodField()

    def get_is_already_filled(self, form):
        return is_form_filled_yet(form)

    def get_users_count(self, form):
        organization = self.context.get('organization')
        form_qs = form.form_assignments.all()
        form = annotate_last_experience_userform_qs(form_qs)
        return form.filter(
            user__is_active=True,
            user__is_blocked=False
        ).filter(
            __end_date__gte=get_today(),
            user__detail__organization=organization
        ).count()


class ListFormSerializerForUserSerializer(serializers.ModelSerializer):
    show_report_icon = serializers.ReadOnlyField()

    class Meta:
        model = Form
        fields = (
            'id', 'name', 'deadline', 'description', 'disclaimer_text',
            'is_anonymously_fillable', 'is_archived', 'is_draft',
            'is_multiple_submittable', 'organization', 'uuid', 'show_report_icon'
        )


class RetrieveAnonymousFormSerializer(serializers.ModelSerializer):

    question_set = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = (
            'id', 'name', 'deadline', 'description', 'disclaimer_text',
            'is_anonymously_fillable', 'is_archived', 'is_draft',
            'is_multiple_submittable', 'organization', 'question_set'
        )

    def get_question_set(self, form):
        question_sections = (
            form.question_set.sections.all() if form.question_set else None
        )
        if not question_sections:
            return {}
        questions = FormQuestionSectionSerializer(
            question_sections,
            context=self.context,
            many=True
        ).data
        return {
            "count": question_sections.count(),
            "sections": questions,
            "id": form.question_set.id,
            "name": form.question_set.name
        }


class RetrieveFormSerializer(serializers.ModelSerializer):
    question_set = serializers.SerializerMethodField()
    is_already_filled = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = (
            'id', 'name', 'deadline', 'description', 'disclaimer_text',
            'is_anonymously_fillable', 'is_archived', 'is_draft',
            'is_multiple_submittable', 'organization', 'question_set',
            'uuid', 'is_already_filled'
        )
        extra_kwargs = {
            'organization': {
                'required': False
            }
        }

    def get_is_already_filled(self, form):
        return is_form_filled_yet(form)

    def get_question_set(self, form):
        question_sections = (
            form.question_set.sections.all() if form.question_set else None
        )
        if not question_sections:
            return {}
        questions = FormQuestionSectionSerializer(
            question_sections,
            context=self.context,
            many=True
        ).data
        return {
            "count": question_sections.count(),
            "sections": questions,
            "id": form.question_set.id,
            "name": form.question_set.name
        }

    def create(self, validated_data):
        organization = self.context["organization"]
        validated_data.update({"organization": organization})
        return super().create(validated_data)


class PartialUpdateFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = (
            'name', 'deadline', 'description', 'disclaimer_text',
            'is_archived',
        )


class WriteFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = (
            'id', 'name', 'deadline', 'description', 'disclaimer_text',
            'is_anonymously_fillable', 'is_archived', 'is_draft',
            'is_multiple_submittable', 'organization', 'question_set',
            'uuid',
        )
        extra_kwargs = {
            'organization': {
                'required': False
            }
        }

    def create(self, validated_data):
        organization = self.context["organization"]
        validated_data.update({"organization": organization})
        return super().create(validated_data)

    def update(self, form, validated_data):
        if form.answer_sheets.filter(is_draft=False).exists():
            raise ValidationError({
                "error": (
                    "PUT request not allowed for "
                    "form with user submissions."
                )
            })
        validated_data["organization"] = self.context["organization"]
        return super().update(form, validated_data)


class UserFormSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True
    )
    select_all_users = serializers.BooleanField(required=False)
    show_user_filters = serializers.BooleanField(required=False)

    class Meta:
        model = UserForm
        fields = ('users', 'select_all_users', 'show_user_filters')

    def create(self, validated_data):
        form = self.context["form"]
        if form.is_archived:
            raise ValidationError({
                "error": "Cannot assign form which is in archived state."
            })
        if form.is_anonymously_fillable:
            raise ValidationError({
                "error": "Cannot assign anonymous form to users."
            })

        if form.deadline:
            deadline = form.deadline
            if deadline < get_today(with_time=True):
                raise ValidationError({
                    "error": "Cannot assign users to form after form deadline is exceeded."
                })

        organization = self.context["organization"]
        select_all_users = validated_data.get('select_all_users')
        show_user_filters = validated_data.get('show_user_filters')
        current_members_assignments = UserForm.objects.filter(form=form)
        current_members_ids = [assignment.user.id for assignment in current_members_assignments]
        current_members = User.objects.filter(
            id__in=current_members_ids
        )
        users_from_req = validated_data["users"]
        user_ids_from_req = [user.id for user in users_from_req]
        users_from_req_qs = User.objects.filter(
            id__in=user_ids_from_req
        )
        user_forms = []
        if select_all_users:
            all_users = User.objects.filter(detail__organization=organization)
            users_from_req_qs = all_users
            users_from_req = list(all_users)

        if show_user_filters:
            filters = self.context['datas']

            filters_data = {
                'detail__division_id': filters.get('division'),
                'detail__branch_id': filters.get('branch'),
                'detail__employment_status_id': filters.get('employment_type'),
                'detail__employment_level_id': filters.get('employment_level'),
                'detail__job_title_id': filters.get('job_title'),
                'detail__gender': filters.get('gender'),
                'assigned_duty_stations': filters.get('duty_station')
            }
            user_filters = User.objects.all()
            users_from_req = []
            for key, value in filters_data.items():
                if value is not None and value != '':
                    user_filters = user_filters.filter(**{key: value})
                    users_from_req_qs = user_filters
                    users_from_req = list(user_filters)

            default_items = {
                'division_id': filters.get('division'),
                'branch_id': filters.get('branch'),
                'employment_level_id': filters.get('employment_level'),
                'employment_type_id': filters.get('employment_type'),
                'job_title_id': filters.get('job_title'),
                'gender': filters.get('gender'),
                'duty_station_id': filters.get('duty_station')
            }
            default_data = {
                k: v or None for k, v in default_items.items() if v
            }

            FormSetting.objects.filter(form=form).delete()
            if default_data:
                FormSetting.objects.create(
                    form=form, **default_data
                )
        users_outside_organization = users_from_req_qs.exclude(
            ~Q(detail__organization=organization)
        )
        if users_outside_organization.exists() and users_outside_organization.count() == 0:
            raise ValidationError({
                "error": "Cannot assign users that don't belong to this organization."
            })

        new_members = (users_from_req_qs | current_members).difference(current_members)
        removed_members = current_members.difference(users_from_req_qs)
        removed_members_ids = [member.id for member in removed_members]

        has_unassigned_member_submitted = UserFormAnswerSheet.objects.filter(
            user__in=removed_members_ids,
            form=form
        ).exists()
        if has_unassigned_member_submitted:
            raise ValidationError({
                "error": (
                    "One or more unassigned users have already submitted the form."
                )
            })

        for user in users_from_req:
            user_forms.append(
                UserForm(form=form, user=user)
            )
        current_assignments = UserForm.objects.filter(
            user__in=current_members,
            form=form
        )
        current_assignments.delete()
        async_task(
            add_notification,
            text=f"Form '{form.name}' has been assigned to you.",
            action=form,
            recipient=new_members,
            actor=get_system_admin(),
            url='/user/organization/forms'
        )
        UserForm.objects.bulk_create(user_forms)
        return DummyObject(**validated_data)


class ListFormAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ('users', 'setting', 'show_user_filters')

    users = serializers.SerializerMethodField()
    setting = FormSettingSerializer()

    def get_users(self, obj):
        organization = obj.organization
        form_qs = obj.form_assignments.all()
        form = annotate_last_experience_userform_qs(form_qs)
        user_form = form.filter(
            user__is_active=True,
            user__is_blocked=False
        ).filter(
            __end_date__gte=get_today(),
            user__detail__organization=organization
        )

        users = [
            assignment.user.id for assignment in
            user_form
        ]
        return users
