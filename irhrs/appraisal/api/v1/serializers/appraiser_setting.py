from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from irhrs.appraisal.constants import SUPERVISOR_APPRAISAL, PEER_TO_PEER_FEEDBACK, \
    SUBORDINATE_APPRAISAL, APPRAISAL_TYPE, REVIEWER_EVALUATION, SENT, RECEIVED, SAVED, COMPLETED, \
    SUBMITTED, SELF_APPRAISAL
from irhrs.appraisal.models.appraiser_setting import Appraisal
from irhrs.appraisal.models.key_achievement_and_rating_pa import KeyAchievementAndRatingAppraisal, \
    KAARAppraiserConfig
from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import nested_get
from irhrs.core.utils.common import DummyObject
from irhrs.core.validators import MinMaxValueValidator
from irhrs.notification.utils import add_notification
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserSupervisor

User = get_user_model()


class UserSupervisorThinSerializer(DynamicFieldsModelSerializer):
    supervisor = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )
    )
    user = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )
    )
    is_selected = serializers.BooleanField()

    class Meta:
        model = UserSupervisor
        fields = ('id', 'supervisor', 'authority_order', 'is_selected', 'user')


class PerformanceAppraisalUserThinSerializer(UserThinSerializer):
    is_selected = serializers.BooleanField()

    class Meta(UserThinSerializer.Meta):
        fields = UserThinSerializer.Meta.fields + ['is_selected']


class BulkAssignSerializerMixin(serializers.Serializer):
    authority_level = serializers.ChoiceField(
        choices=(
            (1, 1),
            (2, 2),
            (3, 3)
        )
    )


class SupervisorAppraiserSettingListSerializer(UserThinSerializer):
    class Meta(UserThinSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )

    def get_fields(self):
        fields = super().get_fields()
        fields['supervisors'] = UserSupervisorThinSerializer(
            source='user_supervisors',
            many=True,
            fields=('id', 'supervisor', 'authority_order', 'is_selected')
        )
        return fields


class KAARSupervisorAppraiserListSerializer(SupervisorAppraiserSettingListSerializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['emp_supervisor'] = SerializerMethodField()
        return fields

    def get_emp_supervisor(self, instance):
        kaar_appraisal = instance.as_kaar_appraisees.filter(
            sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot')
        ).first()
        if kaar_appraisal:
            default_appraiser = kaar_appraisal.appraiser_configs.exclude(
                appraiser__in=instance.supervisors.values_list('supervisor', flat=True)
            ).filter(
                appraiser_type=SUPERVISOR_APPRAISAL
            ).first()
            if default_appraiser:
                return UserThinSerializer(
                    instance=default_appraiser.appraiser, fields=self.Meta.fields
                ).data
        return None


class AppraiserImportBaseMixin(DynamicFieldsModelSerializer):
    appraiser_type = None
    create_serializer = None
    user = serializers.CharField()

    class Meta:
        fields = ('user',)
        model = KAARAppraiserConfig

    def get_fields(self):
        fields = super().get_fields()
        fields[self.appraiser_type] = serializers.CharField()
        return fields

    def get_user_and_appraiser(self, attrs):
        user_email_or_username = attrs.get('user')
        supervisor_email_or_username = attrs.get(self.appraiser_type)
        user = User.objects.filter(
            Q(username=user_email_or_username) | Q(email=user_email_or_username)).first()
        appraiser = User.objects.filter(Q(username=supervisor_email_or_username) | Q(
            email=supervisor_email_or_username)).first()
        return user, appraiser

    def create(self, validated_data):
        user, appraiser = self.get_user_and_appraiser(validated_data)
        ser = self.create_serializer(
            data={'user': user.id}, context={**self.context, self.appraiser_type: appraiser})
        ser.is_valid()
        return ser.save()

    def validate(self, attrs):
        user, appraiser = self.get_user_and_appraiser(attrs)
        error_dict = {}
        if not user:
            error_dict['user'] = f"{attrs.get('user')} not found."
        if not appraiser:
            error_dict[self.appraiser_type] = f"{attrs.get(self.appraiser_type)} not found."
        if error_dict:
            raise ValidationError(error_dict)
        ser = self.create_serializer(
            data={'user': user.id}, context={**self.context, self.appraiser_type: appraiser})
        ser.is_valid(raise_exception=True)
        return super().validate(attrs)


class ReviewerEvaluationSettingListSerializer(UserThinSerializer):
    reviewer = serializers.SerializerMethodField()

    class Meta(UserThinSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization', 'reviewer'
        )

    def get_reviewer(self, obj):
        reviewer = KAARAppraiserConfig.objects.filter(
            kaar_appraisal__sub_performance_appraisal_slot=self.context.get(
                'sub_performance_appraisal_slot'),
            appraiser_type=REVIEWER_EVALUATION,
            kaar_appraisal__appraisee=obj
        ).first()
        if not reviewer:
            return {}
        return UserThinSerializer(
            instance=reviewer.appraiser,
            fields=(
                'id', 'full_name', 'profile_picture', 'job_title',
                'is_online', 'is_current', 'organization',
            ),
        ).data


class AppraiserSettingBulkAssignSerializer(BulkAssignSerializerMixin):
    pass


class AppraiserConfigAssignBaseSerializer(serializers.Serializer):
    appraiser_type = None
    authority_level = serializers.ChoiceField(
        choices=(
            (1, 1),
            (2, 2),
            (3, 3)
        ),
        required=False
    )

    def get_fields(self):
        fields = super().get_fields()
        fields[self.appraiser_type] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all().current(),
            required=False
        )
        return fields

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not any((attrs.get(self.appraiser_type), attrs.get('authority_level'))):
            raise ValidationError(
                {'error': f'{self.appraiser_type} or authority level is required.'}
            )
        return attrs


class ReviewerAppraiserConfigBulkAssign(AppraiserConfigAssignBaseSerializer):
    appraiser_type = 'reviewer'


class SupervisorAppraiserConfigBulkAssign(AppraiserConfigAssignBaseSerializer):
    appraiser_type = 'supervisor'


class AppraiserSettingIndividualAssignSerializer(
    BulkAssignSerializerMixin
):
    def get_fields(self):
        fields = super().get_fields()
        fields['user'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all().current()
        )
        return fields


class AssignIndividualAppraiserConfigBaseSerializer(AppraiserConfigAssignBaseSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().current(),
    )


class ReviewerIndividualAssignSerializer(AssignIndividualAppraiserConfigBaseSerializer):
    appraiser_type = 'reviewer'


class SupervisorIndividualAssignSerializer(AssignIndividualAppraiserConfigBaseSerializer):
    appraiser_type = 'supervisor'


class SupervisorAppraiserSettingActionSerializer(serializers.Serializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['user'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all().current(),
        )
        return fields

    def create(self, validated_data):
        authority_level = self.context.get('authority_level')
        user = validated_data.get('user')
        supervisor = user.supervisors.get(
            authority_order=authority_level
        ).supervisor

        instance, _ = Appraisal.objects.get_or_create(
            appraisee=user,
            appraiser=supervisor,
            appraisal_type=SUPERVISOR_APPRAISAL,
            sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot')
        )
        if self.context.get('action') == 'unassign':
            instance.delete()
        return DummyObject(**validated_data)


class AssignAppraiser:
    def __init__(
        self,
        sub_performance_appraisal_slot,
        appraiser_type,
        kaar_appraisal: KeyAchievementAndRatingAppraisal,
        appraiser: User,
        authenticated_user: User
    ):
        self.sub_performance_appraisal_slot = sub_performance_appraisal_slot
        self.appraiser_type = appraiser_type
        self.kaar_appraisal = kaar_appraisal
        self.appraiser = appraiser
        self.authenticated_user = authenticated_user

    @property
    def get_mode_deadlines(self):
        return self.sub_performance_appraisal_slot.modes.filter(
            appraisal_type=self.appraiser_type).first()

    def assign_appraiser(self):
        previous_configs = self.kaar_appraisal.appraiser_configs.filter(
            appraiser_type=self.appraiser_type
        )

        is_appraiser_changed = all((
            self.sub_performance_appraisal_slot.question_set_status == SENT,
            previous_configs.exists(),
            self.kaar_appraisal.status != COMPLETED
        ))
        send_notification = False
        appraiser_data = {
            'kaar_appraisal': self.kaar_appraisal,
            'appraiser_type': self.appraiser_type,
            'appraiser': self.appraiser,
        }
        prev_config = previous_configs.first()
        if is_appraiser_changed and prev_config.question_status in [SAVED, RECEIVED]:
            appraiser_data['question_status'] = RECEIVED
            appraiser_data['start_date'] = prev_config.start_date
            appraiser_data['deadline'] = prev_config.deadline
            send_notification = True
        else:
            prev_appraiser_type_mapper = {
                SUPERVISOR_APPRAISAL: SELF_APPRAISAL,
                REVIEWER_EVALUATION: SUPERVISOR_APPRAISAL
            }
            prev_appraiser = self.kaar_appraisal.appraiser_configs.filter(
                appraiser_type=prev_appraiser_type_mapper.get(self.appraiser_type, None)
            ).first()
            prev_appraiser_question_type = getattr(prev_appraiser, 'question_status', None)
            if prev_appraiser_question_type == SUBMITTED:
                appraiser_data['question_status'] = RECEIVED
                appraiser_data['start_date'] = self.get_mode_deadlines.start_date
                appraiser_data['deadline'] = self.get_mode_deadlines.deadline
                send_notification = True

        previous_configs.delete()
        appraiser_instance = KAARAppraiserConfig.objects.create(
            **appraiser_data
        )
        if send_notification:
            add_notification(
                text=f"Performance Appraisal Review Forms has been assigned to you.",
                recipient=self.appraiser,
                action=appraiser_instance,
                actor=self.authenticated_user,
                url=f'/user/pa/appraisal/{self.sub_performance_appraisal_slot.id}/kaarForms'
            )


class AppraiserSettingActionBaseSerializer(serializers.Serializer):
    appraiser_type = None
    context_field = None
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().current(),
    )

    def get_appraiser(self, user):
        authority_level = self.context.get('authority_level')
        appraiser = self.context.get(self.context_field)
        if not appraiser:
            appraiser = getattr(user.supervisors.filter(
                authority_order=authority_level
            ).first(), 'supervisor', 'None')
        return appraiser

    def create(self, validated_data):
        user = validated_data.get('user')
        appraiser = self.get_appraiser(user)

        instance, _ = KeyAchievementAndRatingAppraisal.objects.get_or_create(
            appraisee=user,
            sub_performance_appraisal_slot=self.sub_performance_appraisal_slot
        )

        appraiser_configs = instance.appraiser_configs.filter(
            appraiser=appraiser,
            appraiser_type=self.appraiser_type
        )
        if not appraiser_configs:
            cls = AssignAppraiser(
                self.sub_performance_appraisal_slot,
                self.appraiser_type,
                instance,
                appraiser,
                self.context.get('request').user
            )
            cls.assign_appraiser()

        if self.context.get('action') == 'unassign':
            appraiser_configs.delete()
        return DummyObject(**validated_data)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs.get('user')
        kaar_appraisal = user.as_kaar_appraisees.filter(
            sub_performance_appraisal_slot=self.sub_performance_appraisal_slot
        ).first()
        appraisal_status = getattr(kaar_appraisal, 'status', None)
        if appraisal_status == COMPLETED:
            raise ValidationError({"error": " Can not change appraiser Cycle is completed."})
        if kaar_appraisal:
            appraiser_config = kaar_appraisal.appraiser_configs.filter(
                appraiser_type=self.appraiser_type
            ).first()
            if getattr(appraiser_config, 'question_status', None) == SUBMITTED:
                raise ValidationError({
                        f'{user}': f"Can't {self.context.get('action')} appraiser, "
                                 f"{appraiser_config.appraiser} has already submitted PA Forms."})
        return attrs

    @property
    def sub_performance_appraisal_slot(self):
        return self.context.get('sub_performance_appraisal_slot')


class SupervisorAppraiserConfigSerializer(AppraiserSettingActionBaseSerializer):
    appraiser_type = SUPERVISOR_APPRAISAL
    context_field = 'supervisor'


class ReviewerEvaluationSettingActionSerializer(AppraiserSettingActionBaseSerializer):
    appraiser_type = REVIEWER_EVALUATION
    context_field = 'reviewer'


class KAARSupervisorImportSerializer(AppraiserImportBaseMixin):
    appraiser_type = 'supervisor'
    create_serializer = SupervisorAppraiserConfigSerializer


class ReviewerImportSerializer(AppraiserImportBaseMixin):
    appraiser_type = 'reviewer'
    create_serializer = ReviewerEvaluationSettingActionSerializer


class PeerToPeerFeedBackSettingCreateSerializer(DynamicFieldsModelSerializer):
    appraisee = UserThinSerializer(
        source='appraisee',
        fields=(
            'id', 'full_name', 'profile_picture',
            'job_title', 'is_online', 'is_current', 'organization',
        )
    )
    appraisers = UserThinSerializer(
        source='appraiser',
        fields=(
            'id', 'full_name', 'profile_picture',
            'job_title', 'is_online', 'is_current', 'organization',
        ),
        many=True
    )
    no_of_evaluators = serializers.IntegerField(read_only=True)
    add_default = serializers.BooleanField(write_only=True, default=False)

    class Meta(UserThinSerializer.Meta):
        model = Appraisal
        fields = ('add_default', 'appraisee', 'no_of_evaluators', 'appraisers')

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method.lower() == 'post':
            fields['appraisee'] = serializers.PrimaryKeyRelatedField(
                queryset=User.objects.all().current()
            )
            fields['appraisers'] = serializers.PrimaryKeyRelatedField(
                queryset=User.objects.all().current(),
                many=True
            )
        return fields

    def validate(self, attrs):
        if attrs.get('appraisee') in attrs.get('appraisers'):
            raise ValidationError({
                'appraisee': ['Appraisee can\'t be assigned as appraisers.']
            })
        return super().validate(attrs)

    def create(self, validated_data):
        new_appraisers = set(
            map(
                lambda user: user.id,
                validated_data.get('appraisers')
            )
        )
        old_appraisers = set(
            Appraisal.objects.filter(
                appraisee=validated_data.get('appraisee'),
                sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot'),
                appraisal_type=PEER_TO_PEER_FEEDBACK
            ).values_list('appraiser_id', flat=True)
        )
        deleted_appraisers = old_appraisers - new_appraisers
        new_appraisers = new_appraisers - old_appraisers

        if deleted_appraisers:
            _ = Appraisal.objects.filter(
                appraisee=validated_data.get('appraisee'),
                appraiser_id__in=deleted_appraisers,
                sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot'),
                appraisal_type=PEER_TO_PEER_FEEDBACK
            ).delete()

        if new_appraisers:
            for appraiser in new_appraisers:
                _ = Appraisal.objects.get_or_create(
                    appraisee=validated_data.get('appraisee'),
                    appraiser_id=appraiser,
                    appraisal_type=PEER_TO_PEER_FEEDBACK,
                    sub_performance_appraisal_slot=self.context.get(
                        'sub_performance_appraisal_slot'),
                    defaults={}
                )
        return DummyObject(**validated_data)


class PeerToPeerFeedBackSettingListSerializer(UserThinSerializer):
    appraisers = serializers.SerializerMethodField()
    no_of_evaluators = serializers.SerializerMethodField()

    class Meta(UserThinSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization','no_of_evaluators', 'appraisers'
        )

    def get_no_of_evaluators(self, obj):
        return obj.as_appraisees.filter(
            sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot'),
            appraisal_type=PEER_TO_PEER_FEEDBACK
        ).count()

    def get_appraisers(self, obj):
        return UserThinSerializer(
            User.objects.filter(
                id__in=obj.as_appraisees.filter(
                    appraisal_type=PEER_TO_PEER_FEEDBACK,
                    sub_performance_appraisal_slot=self.context.get(
                        'sub_performance_appraisal_slot')
                ).values_list('appraiser', flat=True)
            ).distinct(),
            fields=(
                'id', 'full_name', 'profile_picture', 'job_title',
                'is_online', 'is_current', 'organization',
            ),
            many=True
        ).data


class SubordinateAppraiserSettingListSerializer(UserThinSerializer):
    class Meta(UserThinSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )

    def get_fields(self):
        fields = super().get_fields()
        fields['subordinates'] = serializers.SerializerMethodField()
        return fields

    def get_user_data(self, obj, authority_order):
        users = User.objects.filter(
            supervisors__supervisor=obj.id,
            supervisors__authority_order=authority_order
        ).current().annotate(
            is_selected=Exists(
                Appraisal.objects.filter(
                    sub_performance_appraisal_slot=self.context.get(
                        'sub_performance_appraisal_slot'
                    ),
                    appraisal_type=SUBORDINATE_APPRAISAL,
                    appraisee=obj.id,
                    appraiser=OuterRef('id')
                )
            )
        ).select_related(
            'detail', 'detail__job_title'
        )
        return {
            'users': UserThinSerializer(
                users.filter(is_selected=True),
                fields=(
                    'id', 'full_name', 'profile_picture', 'job_title',
                    'is_online', 'is_current', 'organization',
                ),
                many=True
            ).data,
            'total_users': users.count(),
            'total_selected_users': users.filter(is_selected=True).count()
        }

    def get_subordinates(self, obj):
        return {
            'first_level': self.get_user_data(
                obj=obj,
                authority_order=1
            ),
            'second_level': self.get_user_data(
                obj=obj,
                authority_order=2
            ),
            'third_level': self.get_user_data(
                obj=obj,
                authority_order=3
            )
        }


class SubordinateAppraiserSettingActionSerializer(serializers.Serializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['user'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all().current()
        )
        return fields

    def create(self, validated_data):
        authority_level = self.context.get('authority_level')
        user = validated_data.get('user')
        subordinates = set(
            User.objects.filter(
                supervisors__supervisor=user,
                supervisors__authority_order=authority_level
            ).current().values_list('id', flat=True)
        )
        Appraisal.objects.filter(
            appraisee=user,
            appraiser__in=subordinates,
            appraisal_type=SUBORDINATE_APPRAISAL,
            sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot')
        ).delete()
        if self.context.get('action') == 'assign':
            subordinate_appraisal = []
            for subordinate in subordinates:
                subordinate_appraisal.append(
                    Appraisal(
                        appraisee=user,
                        appraiser_id=subordinate,
                        appraisal_type=SUBORDINATE_APPRAISAL,
                        sub_performance_appraisal_slot=self.context.get(
                            'sub_performance_appraisal_slot')
                    )
                )
            if subordinate_appraisal:
                Appraisal.objects.bulk_create(subordinate_appraisal)
        return DummyObject(**validated_data)


class SubordinateAppraiserSettingUpdateSerializer(BulkAssignSerializerMixin):
    def get_fields(self):
        fields = super().get_fields()
        fields['users'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all().current(),
            many=True
        )
        return fields


class SelfAppraisalSettingSerializer(serializers.Serializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['users'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.filter(
                detail__organization=self.context.get('organization')
            ).current(),
            many=True
        )
        return fields


class SelfAppraisalSettingListSerializer(PerformanceAppraisalUserThinSerializer):
    class Meta(PerformanceAppraisalUserThinSerializer.Meta):
        fields = (
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_selected', 'is_current', 'organization',
        )


class PerformanceAppraisalAnswerSerializer(serializers.Serializer):
    answer_choices = serializers.ChoiceField(choices=list(dict(APPRAISAL_TYPE).keys())),
    description = serializers.CharField(
        max_length=255,
        allow_blank=True
    )
    is_mandatory = serializers.BooleanField()
    rating_scale = serializers.IntegerField(
        validators=[MinMaxValueValidator(0, 10)],
        allow_null=True
    )
    correct_answer = serializers.CharField(
        max_length=255,
        allow_null=True,
        allow_blank=True
    )
    rated_value = serializers.IntegerField(
        validators=[MinMaxValueValidator(0, 10)],
        allow_null=True
    )


class PerformanceAppraisalQuestionSetSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    order = serializers.IntegerField(validators=[MinValueValidator(0)])
    answer_choices = PerformanceAppraisalAnswerSerializer(many=True)


class AppraisalListSerializer(DynamicFieldsModelSerializer):
    appraiser = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )
    )
    appraisee = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )
    )
    committed = serializers.BooleanField(source='answer_committed')
    status = serializers.CharField()
    question_set = serializers.SerializerMethodField()
    sent_at = serializers.DateTimeField(source='start_date')
    percentage_score = serializers.SerializerMethodField()

    class Meta:
        model = Appraisal
        fields = [
            'id', 'appraisee', 'appraiser', 'committed', 'score_deduction_factor',
            'status', 'created_at', 'question_set', 'approved', 'committed_at',
            'sent_at', 'approved_at', 'deadline', 'approved','final_score', 'total_score',
            'percentage_score'
        ]
        read_only_fields = 'total_score', 'final_score', 'percentage_score'

    def get_percentage_score(self, instance):
        try:
            percent_score = (instance.final_score/instance.total_score) * 100
            formatted = float(format(percent_score, ".2f"))
            return formatted
        except (TypeError, ZeroDivisionError):
            return None

    @staticmethod
    def get_question_set(obj):
        return {
            'title': obj.question_set.get('title'),
            'description': obj.question_set.get('description')
        } if obj.question_set else {}


class AppraisalQuestionSetSerializer(DynamicFieldsModelSerializer):
    appraisee = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )
    )
    appraiser = UserThinSerializer(
        fields=(
            'id', 'full_name', 'profile_picture', 'job_title',
            'is_online', 'is_current', 'organization',
        )
    )
    committed = serializers.BooleanField(source='answer_committed')
    status = serializers.CharField()
    can_download_form_by_hr = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField('get_resend_reason')
    percentage_score = serializers.SerializerMethodField()

    class Meta:
        model = Appraisal
        fields = [
            'appraisee', 'appraiser', 'committed', 'final_score', 'score_deduction_factor', 'reason',
            'status', 'created_at', 'can_download_form_by_hr', 'question_set', 'answer_committed',
            'total_score', 'final_score', 'percentage_score', 'is_draft'
        ]
        extra_kwargs = {
            'answer_committed': {'write_only': True}
        }
        read_only_fields = 'percentage_score', 'final_score', 'total_score', 'score_deduction_factor', 'can_download_form_by_hr', 'resend'

    def get_percentage_score(self, instance):
        try:
            percent_score = (instance.final_score/instance.total_score) * 100
            formatted = float(format(percent_score, ".2f"))
            return formatted
        except (TypeError, ZeroDivisionError):
            return None

    def get_resend_reason(self, instance):
        try:
            return instance.resend.reason
        except AttributeError:
            return None

    @staticmethod
    def get_can_download_form_by_hr(obj):
        slot = obj.sub_performance_appraisal_slot
        form_review_setting = getattr(slot, 'form_review_setting', False)
        return form_review_setting.can_hr_download_form if form_review_setting else False


    def validate(self, attrs):
        if attrs.get('answer_committed'):
            sub_pa_slot = self.context.get('sub_performance_appraisal_slot')
            appraisal = self.context.get('appraisal')
            form_design = sub_pa_slot.form_design.filter(
                appraisal_type=appraisal.appraisal_type
            ).first()

            feedback = list(filter(
                lambda x: x.get('title') == 'Feedback',
                nested_get(attrs, 'question_set.sections')
            ))

            if form_design and form_design.add_feedback:
                if feedback:
                    question = feedback[0].get('questions')[0].get('question')
                    if not question.get('answers'):
                        raise ValidationError({
                            'non_field_errors': ['You must provide your feedback.']
                        })
                else:
                    raise ValidationError({
                        'non_field_errors': ['You must provide your feedback.']
                    })
        return super().validate(attrs)

    @staticmethod
    def str2bool(draft):
        if draft.lower() in ("true", "True"):
            return True
        elif draft.lower() in ("false", "False"):
            return False
        else:
            raise ValidationError("Draft must be either True or False.")

    def update(self, instance, validated_data):
        answer_committed = validated_data.get('answer_committed')
        is_draft = self.str2bool(self.context.get('is_draft'))

        instance.is_draft = is_draft
        instance.save()
        if answer_committed:
            instance.committed_at = timezone.now()
            # instance.final_score = calculate_obtained_score(instance.question_set)
            instance.save()
        return super().update(instance, validated_data)


class ApproveAllAppraisalSerializer(serializers.Serializer):

    def get_fields(self):
        fields = super().get_fields()
        fields['appraisals'] = serializers.PrimaryKeyRelatedField(
            queryset=Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot'),
                answer_committed=True,
                approved=False
            ),
            many=True
        )
        return fields

    def create(self, validated_data):
        appraisals = self.initial_data.getlist('appraisals')
        _ = Appraisal.objects.filter(
            id__in=appraisals
        ).update(
            approved=True,
            approved_at=timezone.now()
        )
        return DummyObject(**validated_data)


class EditDeadlineOfAppraisalSerializer(serializers.Serializer):
    deadline = serializers.DateTimeField()

    def get_fields(self):
        fields = super().get_fields()
        fields['appraisals'] = serializers.PrimaryKeyRelatedField(
            queryset=Appraisal.objects.filter(
                sub_performance_appraisal_slot=self.context.get('sub_performance_appraisal_slot'),
                answer_committed=False,
                approved=False,
                deadline__isnull=False
            ),
            many=True
        )
        return fields

    def create(self, validated_data):
        deadline = validated_data.get('deadline')
        appraisals = validated_data.get('appraisals')
        appraisals_id = list(
            map(
                lambda x: x.id,
                appraisals
            )
        )
        _ = Appraisal.objects.filter(
            id__in=appraisals_id
        ).update(
            deadline=deadline
        )

        for appraisal in appraisals:
            add_notification(
                text=f'Deadline of Performance Appraisal Review Form of {appraisal.appraisee.full_name}'
                     f' has been changed.',
                recipient=appraisal.appraiser,
                action=appraisal,
                actor=self.context['user'],
                url=f'/user/pa/appraisal/{appraisal.sub_performance_appraisal_slot.id}/forms'
            )

        return DummyObject(**validated_data)


class RemoveAppraisalSerializer(serializers.Serializer):
    def get_fields(self):
        fields = super().get_fields()
        fields['appraisee'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.filter(
                as_appraisees__isnull=False,
                detail__organization=self.context.get('organization')
            ).current()
        )
        fields['appraisers'] = serializers.PrimaryKeyRelatedField(
            queryset=User.objects.all().current(),
            many=True
        )
        return fields

    def validate(self, attrs):
        attrs['appraisals'] = Appraisal.objects.filter(
            appraisee=attrs.get('appraisee'),
            appraiser__in=attrs.get('appraisers')
        )
        if not attrs['appraisals']:
            raise ValidationError({
                'non_field_errors': ['Detail not found.']
            })
        return super().validate(attrs)

    def create(self, validated_data):
        appraisal = validated_data.get('appraisals')
        appraisal.delete()
        return DummyObject(**validated_data)
