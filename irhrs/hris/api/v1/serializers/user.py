from django.contrib.auth.password_validation import validate_password
from django.db.models import Max
from django.utils.dates import MONTHS
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ReadOnlyField, DateField, \
    SerializerMethodField
from rest_framework.serializers import ModelSerializer

from irhrs.core.constants.user import TEMPORARY, SELF, PERMANENT, PARTING_REASON_CHOICES
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer, \
    DummySerializer
from irhrs.core.utils.common import DummyObject
from irhrs.hris.api.v1.serializers.onboarding_offboarding import \
    EmployeeSeparationSerializer
from irhrs.hris.constants import EMPLOYEE_LIST, EMPLOYEE_DIRECTORY
from irhrs.hris.utils import generate_user_tag
from irhrs.organization.api.v1.serializers.branch import \
    OrganizationBranchSerializer
from irhrs.users.api.v1.serializers.experience import UserExperienceSerializer
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from irhrs.users.api.v1.serializers.user import PasswordChangeSerializer, UserSerializer
from irhrs.users.models import UserExperience


class UserResignSerializer(ModelSerializer):
    end_date = DateField()

    class Meta:
        model = UserExperience
        fields = ['end_date']

    def validate(self, data):
        if self.instance.user.detail.last_working_date:
            raise ValidationError({'non_field_errors': [
                'Can not resign user. User has already resigned.'
            ]})
        if self.instance.user.detail.joined_date > data['end_date']:
            raise ValidationError({'end_date': ['This field\'s value can not '
                                                'be before joined date']})
        return data


class UserTerminateSerializer(UserResignSerializer):
    reason_for_termination = serializers.CharField(
        max_length=200,
        write_only=True
    )

    class Meta(UserResignSerializer.Meta):
        fields = ['end_date', 'reason_for_termination']


class UserActivationSerializer(DummySerializer):
    password = serializers.CharField(max_length=128, write_only=True,
                                     style={'input_type': 'password'})
    detail = serializers.CharField(read_only=True)

    @staticmethod
    def validate_password(password):
        validate_password(password)
        return password

    def validate(self, attrs):
        if self.instance and self.instance.is_active:
            raise ValidationError('Can not activate already activated user.')
        elif self.instance and self.instance.is_blocked:
            raise ValidationError(
                'Can not activate blocked user. Please unblock the user.')
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data.get('password'))
        instance.is_active = True
        instance.save()
        return DummyObject(detail="Successfully activated user.", password=None)


class HRPasswordChangeSerializer(PasswordChangeSerializer):
    def get_fields(self):
        fields = super().get_fields()
        fields.pop('old_password', None)
        return fields

    @staticmethod
    def _validate_old_password(attrs):
        # do not validate old password for HR
        pass


class UserEmploymentSerializer(UserExperienceSerializer):
    user = UserThinSerializer(
        read_only=True
    )
    joined_date = ReadOnlyField(
        source='user.detail.joined_date', allow_null=True
    )
    date_of_birth = SerializerMethodField()
    code = ReadOnlyField(source='user.detail.code', default='N/A')
    extension_number = ReadOnlyField(source='user.detail.extension_number',
                                     default='N/A')
    supervisor = UserThinSerializer(
        source='user.first_level_supervisor',
        exclude_fields=['employee_level', 'division']
    )
    profile_completeness = ReadOnlyField(
        source='user.profile_completeness')
    account_status = ReadOnlyField(source="user.account_status")
    tag = serializers.SerializerMethodField(read_only=True)
    username = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = UserExperience
        fields = (
            'id',
            'code',
            'username',
            'user',
            'account_status',
            'employment_status',
            'joined_date',
            'supervisor',
            'date_of_birth',
            'branch',
            'profile_completeness',
            'extension_number',
            'tag',
        )

    @staticmethod
    def get_date_of_birth(instance):
        dob = instance.user.detail.date_of_birth
        return {
            "month": MONTHS.get(getattr(dob, 'month'))[:3],
            "day": getattr(dob, 'day')
        }

    @staticmethod
    def get_tag(instance):
        return generate_user_tag(instance, source=EMPLOYEE_LIST)


class UserDirectorySerializer(DynamicFieldsModelSerializer):
    user = serializers.SerializerMethodField()
    branch = OrganizationBranchSerializer(
        fields=('name',),
        source='detail.branch'
    )
    supervisor = UserThinSerializer(
        read_only=True,
        source='first_level_supervisor'
    )
    date_of_birth = SerializerMethodField()
    joined_date = ReadOnlyField(source='detail.joined_date')
    code = ReadOnlyField(source='detail.code', default='N/A')
    extension_number = ReadOnlyField(source='detail.extension_number',
                                     default='N/A')
    tag = SerializerMethodField()

    class Meta(UserThinSerializer.Meta):
        fields = [
            'user', 'branch', 'supervisor', 'date_of_birth', 'joined_date',
            'code', 'extension_number', 'tag',
        ]

    @staticmethod
    def get_user(instance):
        return UserThinSerializer(instance).data

    @staticmethod
    def get_date_of_birth(instance):
        dob = instance.detail.date_of_birth
        return {
            "month": MONTHS.get(getattr(dob, 'month'))[:3],
            "day": getattr(dob, 'day')
        }

    @staticmethod
    def get_tag(instance):
        return generate_user_tag(instance, source=EMPLOYEE_DIRECTORY)


class UserDirectoryDetailSerializer(UserDirectorySerializer):
    joined_date = serializers.ReadOnlyField(
        source='detail.joined_date'
    )
    gender = serializers.ReadOnlyField(
        source='detail.gender'
    )
    phone_number = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    user = SerializerMethodField()
    code = serializers.ReadOnlyField(source='detail.code')

    class Meta(UserDirectorySerializer.Meta):
        fields = UserDirectorySerializer.Meta.fields + [
            'joined_date',
            'phone_number',
            'gender',
            'address',
            'code',
        ]

    @staticmethod
    def get_phone_number(instance):
        number = instance.contacts.filter(
            contact_of=SELF
        ).first()
        return number.number if number else None

    @staticmethod
    def get_address(instance):
        # TODO @Ravi: Refactor the code.
        # Merge two queries below to a single one.
        addr = instance.addresses.filter(
            address_type=TEMPORARY
        ).first()
        if not addr:
            addr = instance.addresses.filter(
                address_type=PERMANENT
            ).first()
        return addr.address if addr else None

    @staticmethod
    def get_user(instance):
        data = UserThinSerializer(instance).data
        data["cover_picture"] = UserSerializer.get_cover_picture(instance)
        return data


class PastUserSerializer(UserDirectorySerializer):
    parting_reason = ReadOnlyField(
        source='detail.parting_reason',
        allow_null=True
    )
    separation = EmployeeSeparationSerializer(
        source='employeeseparation_set.first'
    )
    contract_end_date = SerializerMethodField()
    class Meta(UserDirectorySerializer.Meta):
        fields = [
            'user', 'branch', 'date_of_birth', 'joined_date',
            'code', 'parting_reason', 'separation',
            'contract_end_date'
        ]

    @staticmethod
    def get_contract_end_date(instance):
        return instance.user_experiences.aggregate(
            m=Max('end_date')
        ).get('m')


class CreatePastUserSerializer(DummySerializer):
    parted_date = serializers.DateField()
    last_working_date = serializers.DateField()
    parting_reason = serializers.ChoiceField(
        choices=PARTING_REASON_CHOICES
    )

    def validate(self, attrs):
        parted_date = attrs.get('parted_date')
        last_working_date = attrs.get('last_working_date')
        user = self.context.get('user')

        if parted_date > last_working_date:
            raise ValidationError(
                "The parted date must be smaller or equal to last working date."
            )
        last_experience = getattr(
            user.user_experiences.order_by('-end_date').first(),
            'end_date', None
        )
        if last_experience and last_experience > parted_date:
            raise ValidationError(
                "The parted date must be greater than present experience."
            )
        return attrs

    def create(self, validated_data):
        detail = self.context.get('user').detail
        detail.resigned_date = validated_data.get('parted_date')
        detail.last_working_date = validated_data.get('last_working_date')
        detail.parting_reason = validated_data.get('parting_reason')
        detail.save()
        return super().create(validated_data)
