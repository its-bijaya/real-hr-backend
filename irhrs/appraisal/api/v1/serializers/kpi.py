from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.appraisal.constants import ARCHIVED, CONFIRMED, SUBMITTED
from irhrs.appraisal.models.kpi import KPI, IndividualKPI, ExtendedIndividualKPI, \
    IndividualKPIHistory
from irhrs.appraisal.utils.kpi import send_notification_and_create_history, \
    archive_previous_individual_kpi, create_individual_kpi_history, \
    send_notification_to_hr_and_supervisor
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_getattr
from irhrs.organization.api.v1.serializers.division import OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import EmploymentJobTitleSerializer, \
    EmploymentLevelSerializer
from irhrs.organization.api.v1.serializers.fiscal_year import FiscalYearSerializer
from irhrs.organization.api.v1.serializers.organization import OrganizationSerializer
from irhrs.users.api.v1.serializers.thin_serializers import UserThickSerializer


class KPISerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = KPI
        fields = ['id', 'title', 'success_criteria', 'job_title',
                  'division', 'is_archived',
                  'employment_level']

    def create(self, validated_data):
        validated_data['organization'] = self.context.get('organization')
        return super().create(validated_data)

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['organization'] = OrganizationSerializer(fields=['name', 'slug'])
            fields['job_title'] = EmploymentJobTitleSerializer(
                fields=['id', 'slug', 'title'],
                many=True)
            fields['division'] = OrganizationDivisionSerializer(
                fields=['id', 'slug', 'name'],
                many=True)
            fields['employment_level'] = EmploymentLevelSerializer(
                fields=['id', 'title', 'slug'],
                many=True)
        return fields

    def validate(self, attrs):
        super().validate(attrs)
        title = attrs.get('title', '')
        title_exists_in_organization = KPI.objects.filter(
            organization=self.context.get('organization'),
            title=title
        ).exists()
        if self.instance and self.instance.title != title and title_exists_in_organization:
            raise ValidationError({'title': 'KPI with this title already exists.'})
        if not self.instance and title_exists_in_organization:
            raise ValidationError({'title': 'KPI with this title already exists.'})
        return attrs


class IndividualKPIHistorySerializer(DynamicFieldsModelSerializer):
    created_by = UserThickSerializer(
        fields=['full_name', 'username', 'profile_picture', 'cover_picture', 'organization',
                'is_current']
    )

    class Meta:
        model = IndividualKPIHistory
        fields = ('status', 'remarks', 'created_by', 'created_at')


class IndividualKPISerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = IndividualKPI
        fields = ('id', 'title', 'user', 'fiscal_year', 'status', 'is_archived')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['user'] = UserThickSerializer(
                fields=(
                    'id', 'username', 'full_name', 'profile_picture', 'organization',
                    'is_current'))
            fields['fiscal_year'] = FiscalYearSerializer(fields=('id', 'name'))
            fields['extended_individual_kpis'] = ExtendedIndividualKPISerializer(
                fields=['id', 'success_criteria', 'kpi', 'weightage'], many=True,
                context={'request': self.request}
            )
            fields['histories'] = IndividualKPIHistorySerializer(many=True)
        return fields

    def create(self, validated_data):
        user = validated_data.get('user')
        fiscal_year = validated_data.get('fiscal_year')
        status = validated_data.get('status')
        archive_previous_individual_kpi(user, fiscal_year, self.request.user, status)
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        user = validated_data.get('user')
        fiscal_year = validated_data.get('fiscal_year')
        status = validated_data.get('status')
        authenticated_user = self.request.user
        instance_user = instance.user
        if self.is_user_or_fiscal_year_changed(user, fiscal_year, instance):
            archive_previous_individual_kpi(user, fiscal_year, authenticated_user, status)
        elif status and status != instance.status:
            fiscal_year = fiscal_year or instance.fiscal_year
            if status == SUBMITTED:
                organization = self.context.get('organization')
                send_notification_to_hr_and_supervisor(instance, organization, authenticated_user,
                                                       status)
            elif status == CONFIRMED:
                archive_previous_individual_kpi(instance_user, fiscal_year, authenticated_user,
                                                status, instance.id)

            remarks = f"{authenticated_user} updated the status from {instance.status}" \
                      f" to {status}."
            create_individual_kpi_history(instance, remarks)
        else:
            remarks = f"{instance.title} Updated by {authenticated_user}."
            send_notification_and_create_history(instance, '/user/pa/kpi', remarks,
                                                 authenticated_user)

        return super().update(instance, validated_data)

    def validate(self, attrs):
        super().validate(attrs)
        status = attrs.get('status')
        authenticated_user = self.request.user if self.request else None
        user = attrs.get('user')
        if self.instance:
            if self.instance.status == ARCHIVED:
                raise ValidationError({'error': f"Can't update {self.instance.status} KPI."})
            if authenticated_user and self.mode == 'user' and \
                authenticated_user != self.instance.user:
                raise ValidationError({'error': "you do not have permission to do this action."})
            if status and status == CONFIRMED:
                if self.mode == 'user':
                    raise ValidationError(
                        {'error': "You do not have permission to do this action."})
                if user and user != self.instance.user:
                    raise ValidationError({'error': f'You can not change user in {status} kpi.'})
        return attrs

    @staticmethod
    def is_user_or_fiscal_year_changed(user, fiscal_year, instance):
        return user and fiscal_year and not (
            instance.user == user and fiscal_year == instance.fiscal_year)

    @property
    def mode(self):
        return self.context.get('mode')


class ExtendedIndividualKPISerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ExtendedIndividualKPI
        fields = ('id', 'individual_kpi', 'kpi', 'success_criteria',
                  'weightage')

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.upper() == 'GET':
            fields['kpi'] = KPISerializer(fields=['id', 'title'])
        return fields

    def validate(self, attrs):
        super().validate(attrs)
        if self.instance and nested_getattr(self.instance, 'individual_kpi.status') == ARCHIVED:
            raise ValidationError({'error': f"Can't update {self.instance.status} KPI."})
        return attrs


class IndividualKPICollectionSerializer(serializers.Serializer):
    individual_kpi = IndividualKPISerializer()
    extended_kpi = ExtendedIndividualKPISerializer(
        exclude_fields=['individual_kpi'],
        many=True
    )

    def validate(self, attrs):
        extended_kpis = attrs.get('extended_kpi')
        if not extended_kpis:
            raise ValidationError(({
                "error": "No KPI has been selected."
            }))

        total_weightage = sum([x['weightage'] for x in extended_kpis])
        if total_weightage != 100:
            raise ValidationError({"error": "Total weightage must be 100%."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        individual_kpi = validated_data.pop('individual_kpi')
        status = individual_kpi.get('status')
        archive_previous_individual_kpi(
            individual_kpi.get('user'),
            individual_kpi.get('fiscal_year'),
            self.user,
            status
        )
        individual_kpi_instance = IndividualKPI.objects.create(**individual_kpi)
        extended_kpis = validated_data.get('extended_kpi')

        extended_individual_kpi = ExtendedIndividualKPI.objects.bulk_create(
            [
                ExtendedIndividualKPI(individual_kpi=individual_kpi_instance, **data)
                for data in extended_kpis
            ]
        )
        mode = self.context.get('mode', 'user')
        if mode == 'user' and status == SUBMITTED:
            organization = self.context.get('organization')
            send_notification_to_hr_and_supervisor(individual_kpi_instance, organization,
                                                   self.user,
                                                   status)
            create_individual_kpi_history(
                individual_kpi_instance, f'{self.user} has submitted kpi {individual_kpi_instance.title}'
            )
        else:
            remarks = f"{individual_kpi_instance.title} Assigned by {individual_kpi_instance.created_by}."
            send_notification_and_create_history(individual_kpi_instance, '/user/pa/kpi', remarks)
        return extended_individual_kpi

    @property
    def user(self):
        return self.context.get('user')
