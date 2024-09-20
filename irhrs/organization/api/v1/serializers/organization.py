import itertools

from dateutil.rrule import DAILY, rrule
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django_q.tasks import async_task
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import FileField

from irhrs.common.api.serializers.common import (HolidayCategorySerializer,
                                                 ReligionEthnicitySerializer,
                                                 DocumentCategorySerializer)
from irhrs.common.models import (DocumentCategory, HolidayCategory,
                                 ReligionAndEthnicity)
from irhrs.core.constants.common import RELIGION, ETHNICITY, ORGANIZATION
from irhrs.core.mixins.serializers import (DynamicFieldsModelSerializer,
                                           ContactsSerializer)
from irhrs.core.utils.common import DummyObject, get_complete_url, get_today
from irhrs.core.validators import (validate_image_size, DocumentTypeValidator,
                                   validate_future_date, validate_future_date_or_today)
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import \
    OrganizationDivisionSerializer
from irhrs.organization.models import OrganizationBranch
from irhrs.users.api.v1.serializers.thin_serializers import \
    UserThinSerializer
from ....do_not_compile import async_past_holiday_added_post_action
from ....models import (OrganizationAppearance, OrganizationAddress,
                        Organization, OrganizationDocument, Holiday,
                        HolidayRule, Industry, OrganizationDivision)


class OrganizationAppearanceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = OrganizationAppearance
        fields = (
            'organization',
            'primary_color',
            'secondary_color',
            'header_logo',
            'logo',
            'background_image'
        )
        extra_kwargs = {
            'header_logo': {'required': False},
            'logo': {'required': False}
        }

    def validate_logo(self, image):
        return validate_image_size(image)

    def validate_header_logo(self, image):
        return validate_image_size(image)


class OrganizationAddressSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = OrganizationAddress
        fields = (
            'organization',
            'address',
            'mailing_address',
            'street',
            'city',
            'country',
            'address',
            'latitude',
            'longitude',
        )


class OrganizationSerializer(DynamicFieldsModelSerializer):
    parent = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True
    )
    slug = serializers.ReadOnlyField()
    appearance = OrganizationAppearanceSerializer(
        fields=('logo', 'header_logo'))
    address = OrganizationAddressSerializer(
        fields=('address', 'mailing_address', 'latitude', 'longitude')
    )
    industry = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Industry.objects.all()
    )
    contacts = ContactsSerializer()
    disabled_applications = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            'name',
            'abbreviation',
            'registration_number',
            'vat_pan_number',
            'industry',
            'appearance',
            'ownership',
            'size',
            'established_on',
            'address',
            'contacts',
            'email',
            'about',
            'website',
            'parent',
            'organization_head',
            'administrators',
            'slug',
            'disabled_applications'
        )
        read_only_fields = ['disabled_applications']

    def get_disabled_applications(self, obj):
        _as = self.context.get('as', 'user')
        disabled_apps = obj.disabled_applications
        return disabled_apps.get(f'for_{_as}')

    def update(self, instance, validated_data):
        appearance_data = validated_data.pop('appearance', None)
        if appearance_data:

            appearance_data.update({
                'organization': instance.pk,
            })
            if hasattr(self.instance, 'appearance'):
                appearance_data_serializer = OrganizationAppearanceSerializer(
                    self.instance.appearance,
                    data=appearance_data)
            else:
                appearance_data_serializer = OrganizationAppearanceSerializer(
                    data=appearance_data)
            if appearance_data_serializer.is_valid(raise_exception=True):
                appearance = appearance_data_serializer.save()
                validated_data.update({'appearance': appearance})

        address_data = validated_data.pop('address', None)
        if address_data:
            address_data.update({
                'organization': instance.pk,
            })
            if hasattr(instance, 'address'):
                address_data_serializer = OrganizationAddressSerializer(
                    instance.address, data=address_data)
            else:
                address_data_serializer = OrganizationAddressSerializer(
                    data=address_data)
            if address_data_serializer.is_valid(raise_exception=True):
                address = address_data_serializer.save()
                validated_data.update({'address': address})
        contacts_data = validated_data.pop('contacts')
        instance = super().update(instance, validated_data)
        instance.contacts = contacts_data
        instance.save()
        return instance

    def validate_email(self, email):
        return email.lower()

    def validate_parent(self, parent):
        if self.instance == parent:
            raise ValidationError("Organization can't be parent of itself.")
        return parent

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request:
            if request.method == 'GET':
                fields['parent'] = serializers.SerializerMethodField()
                fields['industry'] = serializers.SerializerMethodField()
                fields['organization_head'] = UserThinSerializer(
                    read_only=True
                )
                fields['administrators'] = serializers.SerializerMethodField()
                fields['appearance'] = serializers.SerializerMethodField()

            elif request.method in ['PUT', 'PATCH']:
                if self.instance:
                    fields['name'].read_only = True
                    fields['parent'] = serializers.SlugRelatedField(
                        slug_field='slug',
                        queryset=Organization.objects.exclude(
                            pk=self.instance.pk
                        ),
                        allow_null=True
                    )
                pass
        return fields

    def get_parent(self, obj):
        if obj.parent:
            return {
                'slug': obj.parent.slug,
                'name': obj.parent.name
            }
        return None

    def get_industry(self, obj):
        if obj.industry:
            return {
                'slug': obj.industry.slug,
                'name': obj.industry.name
            }
        return None

    def get_administrators(self, obj):
        return [UserThinSerializer(admin).data for admin in
                obj.administrators.all()]

    def get_appearance(self, obj):
        organization_appearance = getattr(obj, 'appearance', None)
        if organization_appearance:
            ret = OrganizationAppearanceSerializer(
                fields=('logo', 'header_logo'),
                instance=organization_appearance,
                context={'request': self.request}
            ).data
            if ret.get('logo') is None:
                ret.update({
                    'logo': get_complete_url(
                        'images/default/cover.png',
                        att_type='static'
                    )
                })
            elif ret.get('logo') is None:
                ret.update({
                    'header_logo': get_complete_url(
                        'images/default/cover.png',
                        att_type='static'
                    )
                })
            return ret
        return dict(
            header_logo=get_complete_url(
                'images/default/cover.png',
                att_type='static'
            ),
            logo=get_complete_url(
                'images/default/cover.png',
                att_type='static'
            )
        )


class OrganizationDocumentSerializer(DynamicFieldsModelSerializer):
    slug = serializers.ReadOnlyField()
    _accepted_extensions = list(itertools.chain.from_iterable(
        settings.ACCEPTED_FILE_FORMATS.values()
    ))
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=DocumentCategory.objects.all(),
        validators=[DocumentTypeValidator(association_type=ORGANIZATION)]
    )

    attachment = serializers.FileField(
        allow_empty_file=True,
        required=False,
        validators=[
            validate_image_size,
            FileExtensionValidator(
                allowed_extensions=list(_accepted_extensions),
                message='Not a valid file format.',
                code='Invalid File Format'
            )
        ])
    has_acknowledged = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationDocument
        fields = (
            'title',
            'category',
            'description',
            'attachment',
            'slug',
            'created_at',
            'modified_at',
            'organization',
            'is_archived',
            'is_public',
            'is_downloadable',
            'for_resignation',
            'require_acknowledgement',
            'has_acknowledged',
            'document_text'
        )

    def get_has_acknowledged(self, document):
        return document.acknowledgements.filter(id=self.request.user.id).exists()

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method == 'GET':
            fields['category'] = serializers.SerializerMethodField()
        return fields

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # ensuring the organization value is retained.
        if hasattr(instance, 'organization'):
            validated_data.update({'organization': instance.organization})
        return super().update(instance, validated_data)

    def validate(self, attrs):
        organization = self.context.get('organization')
        unique_together_params = {k: v for k, v in attrs.items() if k
                                  in ['category', 'title']}
        unique_together_params.update({
            'organization': organization
        })
        qs = OrganizationDocument.objects.filter(**unique_together_params)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("An attachment with the name for this "
                                  "organization and category already exists.")

        for_resignation = attrs.get('for_resignation')
        if for_resignation:
            if not self.instance and OrganizationDocument.objects.filter(
                organization=organization,
                for_resignation=True
            ).exists():
                raise ValidationError(
                    "Resignation Document Already Exists For This Organization.")
            attrs['is_downloadable'] = False

        is_downloadable = attrs.get('is_downloadable')
        if not is_downloadable:
            attrs['attachment'] = None

        require_acknowledgement = attrs.get('require_acknowledgement')
        is_downloadable = attrs.get('is_downloadable')

        if require_acknowledgement:
            if is_downloadable:
                raise ValidationError({
                    'is_downloadable': 'Acknowledgement is available for non-downloadable '
                                       'documents only'
                })
        return attrs

    @staticmethod
    def get_category(instance):
        """
        Modifying category to return 'name' and 'slug' values for AutoComplete.
        """
        return DocumentCategorySerializer(instance=instance.category).data


class HolidayRuleSerializer(DynamicFieldsModelSerializer):
    religion = serializers.SlugRelatedField(
        slug_field='slug',
        required=False, allow_null=True,
        queryset=ReligionAndEthnicity.objects.filter(category=RELIGION),
        many=True
    )
    ethnicity = serializers.SlugRelatedField(
        slug_field='slug',
        required=False, allow_null=True,
        queryset=ReligionAndEthnicity.objects.filter(category=ETHNICITY),
        many=True
    )

    class Meta:
        model = HolidayRule
        fields = (
            'division', 'religion', 'ethnicity', 'branch',
            'gender', 'lower_age', 'upper_age')

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method.lower() != 'get':
            fields['division'] = serializers.SlugRelatedField(
                slug_field='slug',
                queryset=OrganizationDivision.objects.filter(
                    organization=self.context.get('organization')
                ),
                required=False, allow_null=True, many=True
            )
            fields['branch'] = serializers.SlugRelatedField(
                slug_field='slug',
                queryset=OrganizationBranch.objects.filter(
                    organization=self.context.get('organization')
                ),
                required=False, allow_null=True, many=True
            )
        if request and request.method == 'GET':
            fields['religion'] = ReligionEthnicitySerializer(
                fields=['name', 'slug'],
                many=True
            )
            fields['division'] = OrganizationDivisionSerializer(
                fields=['name', 'slug'],
                many=True
            )
            fields['ethnicity'] = ReligionEthnicitySerializer(
                fields=[
                    'name', 'slug'],
                many=True
            )
            fields['branch'] = OrganizationBranchSerializer(
                fields=['name', 'slug'],
                many=True
            )
        return fields

    def validate(self, attrs):
        instance = getattr(self, 'instance')
        lower_age = attrs.get('lower_age') or (instance.lower_age if instance
                                               else None)
        upper_age = attrs.get('upper_age') or (instance.upper_age if instance
                                               else None)
        if lower_age:
            if not upper_age:
                pass
            elif lower_age > upper_age:
                raise ValidationError(
                    "The lower age cannot be greater than upper age"
                )
        return super().validate(attrs)


class HolidaySerializer(DynamicFieldsModelSerializer):
    """
    Serializer Class for Organization Holiday.
    """
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=HolidayCategory.objects.all())
    rule = HolidayRuleSerializer()
    start_date = serializers.DateField()
    end_date = serializers.DateField(
        required=False
    )

    class Meta:
        model = Holiday
        fields = ('slug', 'name', 'description', 'start_date', 'end_date',
                  'category', 'image', 'rule', 'created_at', 'modified_at')
        read_only_fields = ('slug',)

    def create(self, validated_data):
        today = get_today()
        created_slugs = []
        data_copy = dict(validated_data)
        rule_data = validated_data.pop('rule', None)
        validated_data.update({
            'organization': self.context.get('organization')
        })
        # Multiple Holiday Create
        start_date = validated_data.pop('start_date')
        end_date = validated_data.pop('end_date', None) or start_date
        date_iterator = rrule(dtstart=start_date, until=end_date,
                              freq=DAILY)

        extracted_rule_data = self.extract_extra_rule(rule=rule_data)

        for each_day in date_iterator:
            holiday_date = each_day.date()
            validated_data.update({
                'date': holiday_date
            })
            created_object = Holiday.objects.create(**validated_data)

            holiday_rule, _ = HolidayRule.objects.get_or_create(
                **extracted_rule_data[0],
                holiday=created_object
            )
            self.create_or_update_rule(
                instance=holiday_rule,
                rule_data=extracted_rule_data[1]
            )

            if holiday_date <= today:
                async_task(async_past_holiday_added_post_action, created_object)

            if created_object and created_object.slug:
                created_slugs.append(created_object.slug)
            if not created_slugs:
                raise ValidationError("Could not create. Please insert valid "
                                      "data.")
        data_copy.update(slug=created_slugs)
        return DummyObject(**data_copy)

    @staticmethod
    def extract_extra_rule(rule):
        extra_rules_list = ['branch', 'division', 'ethnicity', 'religion']
        extra_rules = {}  # contains all items of above list
        basic_rules = {}  # contains gender, lower age, upper age and date

        for key, value in rule.items():
            if key in extra_rules_list:
                extra_rules[key] = value
            else:
                basic_rules[key] = value
        return basic_rules, extra_rules

    @staticmethod
    def create_or_update_rule(instance, rule_data):
        for key, value in rule_data.items():
            getattr(instance, key).set(value)

    def update(self, instance, validated_data): ...

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method != 'POST':
            fields.pop('start_date')
            fields.pop('end_date')
            fields['date'] = serializers.DateField(
                validators=[validate_future_date]
            )
        if request and request.method == 'GET':
            fields['category'] = HolidayCategorySerializer(fields=[
                'name', 'slug'])
        return fields

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date') or start_date
        if end_date:
            if end_date < start_date:
                raise ValidationError("End Date must be greater than start "
                                      "date.")

        qs = Holiday.objects.filter(
            organization=self.context.get('organization')
        )

        date_iterator = map(
            lambda dt: dt.date(),
            rrule(dtstart=start_date, until=end_date, freq=DAILY)
        )

        new_rule = attrs['rule']

        new_branch = new_rule['branch']
        for date in date_iterator:
            # Test for the following properties: ('branch', 'gender', 'religion')
            # Conflict test for 'gender' and 'religion' is put on hold due to impracticality
            conflicting_branches = []

            for holiday in qs.filter(date=date):
                # expected to be a single run qs.
                # The loop size is determined by the no. of Holiday defined for the same date.

                old_branches = getattr(holiday.rule, 'branch').values_list('slug', flat=True)
                new_branch_slugs = {branch.slug for branch in new_branch}

                # branch_conflict <= same branch will cause Attendance Calendar to show holiday csv
                branch_conflict = set(old_branches).intersection(new_branch_slugs)

                predicted_conflict = len(old_branches) == 0 or len(new_branch) == 0
                if branch_conflict or predicted_conflict:
                    conflicting_branches.append(holiday.name)

            if conflicting_branches:
                raise ValidationError({
                    'branch': 'Could not create holiday because of observed conflicts in following'
                              f' holidays: {", ".join(conflicting_branches)}'
                })
        return super().validate(attrs)

    @staticmethod
    def validate_description(description):
        if len(description) > 600:
            raise ValidationError(
                "Make sure this field is less than 600 characters.")
        return description


class HolidayImportSerializer(serializers.Serializer):
    file = FileField(write_only=True, validators=[
        FileExtensionValidator(
            allowed_extensions=['xlsx'],
            message='Not a valid file format.',
            code='Invalid Format'
        )])


class HolidayRuleRelatedNameSerializer(HolidayRuleSerializer):
    religion = serializers.SlugRelatedField(
        slug_field='name',
        required=False, allow_null=True,
        queryset=ReligionAndEthnicity.objects.filter(category=RELIGION))
    ethnicity = serializers.SlugRelatedField(
        slug_field='name',
        required=False, allow_null=True,
        queryset=ReligionAndEthnicity.objects.filter(category=ETHNICITY))
    division = serializers.SlugRelatedField(
        slug_field='name',
        queryset=OrganizationDivision.objects.all(),
        required=False, allow_null=True
    )

    def get_fields(self):
        fields = super().get_fields()
        organization = self.context.get('organization')

        fields['division'] = serializers.SlugRelatedField(
            slug_field='name',
            queryset=OrganizationDivision.objects.all().filter(organization=organization),
            required=False, allow_null=True
        )
        return fields
