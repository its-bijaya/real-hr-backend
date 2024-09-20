from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, BooleanField
from rest_framework.relations import SlugRelatedField, PrimaryKeyRelatedField
from rest_framework.serializers import Serializer
from dateutil.relativedelta import relativedelta

from irhrs.common.api.serializers.common import ReligionEthnicitySerializer
from irhrs.common.models import ReligionAndEthnicity
from irhrs.core.constants.common import RELIGION, ETHNICITY
from irhrs.core.constants.user import MARRIED, SINGLE
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils.change_request import get_changes, \
    create_update_change_request, \
    send_change_request
from irhrs.core.utils.common import DummyObject, get_today, validate_permissions
from irhrs.core.utils.subordinates import find_immediate_subordinates
from irhrs.hris.models import DutyStationAssignment
from irhrs.hris.models import UserResultArea
from irhrs.hris.utils import update_user_profile_completeness
from irhrs.organization.api.v1.serializers.organization import \
    OrganizationSerializer
from irhrs.permission.constants.permissions import USER_PROFILE_PERMISSION
from irhrs.users.api.v1.serializers.address_detail import UserAddressSerializer
from irhrs.users.api.v1.serializers.contact_detail import \
    UserContactDetailSerializer
from irhrs.users.api.v1.serializers.experience import UserExperienceSerializer
from irhrs.common.models import DutyStation
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserContactDetail, UserAddress, UserExperience
from irhrs.users.utils import send_activation_mail, send_user_update_signal
from .user import UserSerializer, NestableUserSerializer
from ....models import UserDetail
from ....utils.notification import send_change_notification_to_user

User = get_user_model()


class UserDetailSerializer(DynamicFieldsModelSerializer):
    user = NestableUserSerializer()
    religion = SlugRelatedField(
        queryset=ReligionAndEthnicity.objects.filter(category=RELIGION),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    ethnicity = SlugRelatedField(
        queryset=ReligionAndEthnicity.objects.filter(category=ETHNICITY),
        slug_field='slug',
        required=False,
        allow_null=True
    )
    addresses = UserAddressSerializer(
        source='user.addresses',
        read_only=True, many=True,
        fields=["address_type", "address"]
    )
    self_contacts = UserContactDetailSerializer(
        fields=["name", "number", "number_type", "email"],
        many=True,
        read_only=True,
        allow_null=True,
        source='user.self_contacts'
    )
    current_organization = OrganizationSerializer(
        source='organization',
        fields=['name', 'slug', 'abbreviation',
                'appearance', 'disabled_applications'],
        read_only=True,
        default=None
    )
    first_level_supervisor = UserThinSerializer(
        source="user.first_level_supervisor",
        fields=('id', 'full_name', 'profile_picture', 'cover_picture',
                'job_title', 'is_current', 'organization'),
        read_only=True, allow_null=True)

    sub_ordinates = serializers.SerializerMethodField(read_only=True,
                                                      allow_null=True,
                                                      required=False)
    key_result_area = serializers.SerializerMethodField(read_only=True,
                                                        allow_null=True,
                                                        required=False)
    current_duty_station = serializers.SerializerMethodField()
    current_duty_station_name = serializers.SerializerMethodField()
    years_of_service = serializers.SerializerMethodField()

    class Meta:
        model = UserDetail
        fields = [
            'user', 'code', 'gender', 'date_of_birth',
            'religion', 'ethnicity', 'nationality', 'marital_status',
            'marriage_anniversary', 'addresses', 'self_contacts',
            'joined_date', 'last_working_date', 'current_organization', 'extension_number',
            'first_level_supervisor', 'sub_ordinates', 'key_result_area',
            'current_duty_station', 'current_duty_station_name', 'years_of_service'
        ]
        read_only_fields = ('id',)

    @staticmethod
    def get_years_of_service(obj):
        to_date = obj.last_working_date
        if not to_date:
            to_date = get_today()
        if obj.joined_date > get_today():
            return "0 day"
        yos = relativedelta(to_date, obj.joined_date)
        mapper = {
            "years": yos.years,
            "months": yos.months,
            "days": yos.days
        }
        years_of_service = ''
        for key, val in mapper.items():
            if val:
                years_of_service += f"{val} {key} "
        return years_of_service

    def validate(self, attrs):
        marital_status = attrs.get('marital_status')
        marriage_anniversary = attrs.get('marriage_anniversary')
        dob = attrs.get('date_of_birth')
        doj = attrs.get('joined_date')
        if marital_status == MARRIED:
            if marriage_anniversary and marriage_anniversary <= dob:
                raise ValidationError({
                    'marriage_anniversary': _(
                        "This field must be greater than date of birth.")
                })

        elif marital_status == SINGLE and marriage_anniversary:
            raise ValidationError({
                'marriage_anniversary': _(
                    "This field can not be set for `Single` marital status."
                )
            })
        if dob and doj and doj <= dob:
            raise ValidationError({
                'joined_date': _(
                    "Joined date must be greater than date of birth"),
                'date_of_birth': _(
                    "Date of birth must be smaller than joined_date."
                )
            })
        return attrs

    def validate_user(self, user_data):
        user_data_raw = dict(user_data)
        organization = user_data.get('organization')
        if not user_data_raw.get('username'):
            user_data_raw.update({'username': user_data_raw.get('email')})

        if organization:
            user_data_raw.update({'organization': organization.slug})
        data = {'data': user_data_raw, 'partial': self.partial}

        if self.instance:
            data.update({'instance': self.instance.user})
        serializer = UserSerializer(**data)
        serializer.is_valid(raise_exception=True)
        return user_data

    def validate_joined_date(self, joined_date):
        request = self.request

        if self.instance:
            # compare joined date with user experiences and if user experience exists and joined date is after the
            # oldest of experience then raise validation error

            first_experience = self.instance.user.user_experiences.order_by(
                'start_date').first()

            if first_experience and joined_date and joined_date > first_experience.start_date:
                raise ValidationError(
                    "An experience exists before the joined date. Please set joined date less than or"
                    f" equal to {first_experience.start_date}.")

        # we do not require to validate joined date for normal users for create
        # as they cannot access POST method.
        if self.instance and not validate_permissions(
            request.user.get_hrs_permissions(
                self.instance.organization
            ),
            USER_PROFILE_PERMISSION
        ):
            raise ValidationError(
                f"You are not allowed to change Joined date."
            )
        return joined_date

    def create(self, validated_data):
        user_data = self._get_user_data(validated_data.pop('user', None))

        user_serializer = UserSerializer(data=user_data, context=self.context)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        validated_data.update({'user': user})
        instance = super().create(validated_data)
        #send_change_notification_to_user(self, instance, instance.user, self.request.user,'created')
        return instance

    @staticmethod
    def has_change(changes):
        for change in changes.values():
            if (
                change["old_value"] != change["new_value"] or
                change["old_value_display"] != change["new_value_display"]
            ):
                return True
        return False

    def update(self, instance, validated_data):
        # None value is set because the frontend sends form-data, and None value cannot be sent in
        # form-data. So, here we manually check if field is present in validated_data, if not, we
        # set value to None manually
        mapper = {'religion':instance.religion, 'ethnicity':instance.ethnicity}
        for field, value in mapper.items():
            if field not in validated_data.keys():
                validated_data[field] = value

        request = self.request
        if request:
            # cr --> change request
            send_cr = (not self.context.get('is_hr')) or send_change_request(
                request.user,
                instance.user
            )
        else:
            send_cr = None
        user_data = self._get_user_data(validated_data.pop('user', None))
        if user_data:
            user_serializer = UserSerializer(instance=instance.user,
                                             data=user_data,
                                             context=self.context,
                                             partial=self.partial)
            user_serializer.is_valid(raise_exception=True)

            if send_cr:
                old_user = instance.user
                new_data = dict(user_data)
                if 'cover_picture' in new_data:
                    # change cover picture to _cover_picture which is our field
                    new_data['_cover_picture'] = new_data['cover_picture']

                changes = get_changes(instance=old_user, new_data=new_data)
                if self.has_change(changes):
                    create_update_change_request(
                        user=instance.user, obj=instance.user,
                        changes=changes,
                        category="General Information"
                    )
            else:
                user_serializer.save()
                send_user_update_signal(instance.user)

        if send_cr:
            new_data = dict(validated_data)

            changes = get_changes(new_data=new_data, instance=instance)
            if self.has_change(changes):
                create_update_change_request(
                    user=instance.user, obj=instance,
                    changes=changes,
                    category="General Information"
                )
            return instance
        if instance.user.detail.organization:
            send_change_notification_to_user(
                self, instance, instance.user, request.user, 'updated')

        update_user_profile_completeness(instance.user)
        return super().update(instance, validated_data)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request and request.method == 'GET':
            fields['religion'] = ReligionEthnicitySerializer(
                fields=['name', 'slug'])
            fields['ethnicity'] = ReligionEthnicitySerializer(
                fields=['name', 'slug'])
            fields['current_experience'] = UserExperienceSerializer(
                source="user.current_experience",
                fields=[
                    "job_title",
                    "organization",
                    "division",
                    "branch",
                    "employee_level",
                    "employment_status",
                    "start_date",
                    "end_date",
                    "job_description",
                    "objective",
                    "current_step"
                ],
                context=self.context)
        elif request and request.method in ['PUT', 'PATCH']:
            fields['user'] = NestableUserSerializer(
                instance=getattr(self.instance, 'user', None),
                context=self.context
            )
        return fields

    @staticmethod
    def get_sub_ordinates(obj):
        return UserThinSerializer(
            User.objects.filter(
                id__in=find_immediate_subordinates(obj.user.id)
            ).select_related('detail__job_title'),
            many=True,
            fields=['id',
                    'full_name',
                    'profile_picture',
                    'cover_picture',
                    'organization',
                    'is_current',
                    'job_title']
        ).data


    @staticmethod
    def get_current_duty_station(obj):
        try:
            current_duty_station_assignment = obj.user.assigned_duty_stations.filter(
                Q(to_date__gte=get_today()) | Q(to_date__isnull=True),
                from_date__lte=get_today(),
            ).first()
            if current_duty_station_assignment:
                return current_duty_station_assignment.duty_station.id
        except DutyStation.DoesNotExist:
            return None

    @staticmethod
    def get_current_duty_station_name(obj):
        try:
            current_duty_station_assignment = obj.user.assigned_duty_stations.filter(
                Q(to_date__gte=get_today()) | Q(to_date__isnull=True),
                from_date__lte=get_today(),
            ).first()
            if current_duty_station_assignment:
                return current_duty_station_assignment.duty_station.name
        except DutyStation.DoesNotExist:
            return None

    @staticmethod
    def get_key_result_area(obj):
        user_experience = UserExperience.objects.filter(
            user=obj.user, is_current=True
        ).prefetch_related(
            Prefetch(
                'user_result_areas',
                queryset=UserResultArea.objects.filter(key_result_area=True),
                to_attr='key_result_area'
            )
        ).first()
        return [
            kra.result_area.title for kra in user_experience.key_result_area
        ] if user_experience else []

    @staticmethod
    def _get_user_data(user_data):
        """
        Replace organization instance by its slug
        to use it with serializer
        """
        if user_data and user_data.get('organization'):
            user_data['organization'] = user_data['organization'].slug
        return user_data


class MeSerializer(UserDetailSerializer):
    user = UserThinSerializer(
        fields=(
            'id',
            'full_name',
            'profile_picture',
            'job_title',
            'email',
            'organization',
            'is_current',
            'is_audit_user'
        )
    )
    current_organization = OrganizationSerializer(
        source='organization',
        fields=(
            'name', 'slug', 'abbreviation', 'disabled_applications'
        )
    )
    organization_specific_employee_directory = serializers.SerializerMethodField()

    class Meta(UserDetailSerializer.Meta):
        fields = [
            'user',
            'current_organization',
            'organization_specific_employee_directory'
        ]

    def get_organization_specific_employee_directory(self, obj):
        if hasattr(settings, 'ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY'):
            return settings.ORGANIZATION_SPECIFIC_EMPLOYEE_DIRECTORY
        return False


class UserCreateSerializer(UserDetailSerializer):
    contact = UserContactDetailSerializer(required=False)
    current_address = UserAddressSerializer(required=False)
    employment = UserExperienceSerializer(
        exclude_fields=["skill", ],
        required=False
    )
    send_activation = BooleanField(default=False)
    group = PrimaryKeyRelatedField(queryset=Group.objects.all(),
                                   allow_null=True,
                                   required=False,
                                   allow_empty=True)

    class Meta(UserDetailSerializer.Meta):
        fields = UserDetailSerializer.Meta.fields + ["contact",
                                                     "current_address",
                                                     "employment",
                                                     "send_activation",
                                                     "group"]

    def validate(self, attrs):
        experience = attrs.get("employment")
        if experience:
            start_date = experience.get('start_date')
            joined_date = attrs.get('joined_date') or get_today()
            if not joined_date:
                raise ValidationError()
            if start_date < joined_date:
                raise ValidationError(
                    "Please set start date after joined date"
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')

        send_activation = validated_data.pop('send_activation', False)
        contact = validated_data.pop("contact", None)
        current_address = validated_data.pop("current_address", None)
        employment = validated_data.pop("employment", None)
        group = validated_data.pop("group", None)

        with transaction.atomic():
            userdetail = super().create(validated_data)
            user = userdetail.user
            if group:
                group.user_set.add(user)
                group.save()

            if contact:
                contact.update({'user': user})
                UserContactDetail.objects.create(**contact)

            if current_address:
                current_address.update({'user': user})
                UserAddress.objects.create(**current_address)

            if employment:
                employment.update({'user': user, 'is_current': True})
                skills = employment.pop('skills', None)

                experience = UserExperience.objects.create(**employment)

                UserExperienceSerializer.update_experience_is_current(
                    experience, user=user)

                if skills:
                    experience.skill.add(*skills)

            if send_activation:
                send_activation_mail(request=request, user=userdetail.user)

        return userdetail


class BulkUserCreateSerializer(Serializer):
    user_details = UserDetailSerializer(many=True, required=True)
    status = CharField(read_only=True, default="Sorry could not create users")

    def create(self, validated_data):
        user_details = validated_data.get('user_details')
        for detail in user_details:
            serializer = UserDetailSerializer(data=detail)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        validated_data.update({'status': 'Successfully Created'})

        return DummyObject(**validated_data)

    def update(self, instance, validated_data):
        return instance

    @staticmethod
    def validate_user_details(user_details):
        if not user_details:
            raise ValidationError("This field may not be empty")
        return user_details
