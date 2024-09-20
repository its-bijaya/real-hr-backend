import operator
from functools import reduce

from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.db.models import Sum, Q, FloatField
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import SlugRelatedField

from django_q.tasks import async_task

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import get_system_admin
from irhrs.core.utils import email
from irhrs.core.utils.email import send_notification_email
from irhrs.core.utils.training import set_training_members
from irhrs.core.validators import validate_future_datetime, ExcelFileValidator
from irhrs.notification.utils import add_notification
from irhrs.organization.api.v1.serializers.branch import OrganizationBranchSerializer
from irhrs.organization.api.v1.serializers.division import OrganizationDivisionSerializer
from irhrs.organization.api.v1.serializers.employment import EmploymentJobTitleSerializer, \
    EmploymentLevelSerializer, EmploymentStatusSerializer
from irhrs.organization.api.v1.serializers.meeting_room import MeetingRoomStatusSerializer
from irhrs.organization.models import MeetingRoom, MeetingRoomStatus
from irhrs.organization.models import OrganizationBranch, OrganizationDivision, EmploymentJobTitle, \
    EmploymentLevel, EmploymentStatus
from irhrs.task.api.v1.serializers.recurring import RecurringTaskSerializer
from irhrs.training.models import (TrainingType, Training, UserTraining, UserTrainingRequest,
                                   Trainer, TrainerAttachments, TrainingAttachments,
                                   TrainingAttachment, TrainingFeedback, TrainingAttendance)
from irhrs.training.models.helpers import DECLINED, APPROVED, PENDING, REQUESTED, TRAINER, MEMBER, \
    ONSITE, OFFSITE
from irhrs.core.constants.organization import (
    TRAINING_ASSIGNED_UNASSIGNED_EMAIL,
    TRAINING_REQUESTED_ACTION_EMAIL
)
from irhrs.training.utils import calibrate_average_rating
from irhrs.training.utils.util import add_or_update_members_of_training, \
    delete_members_from_training
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer

User = get_user_model()


class RecurringTrainingSerializer(RecurringTaskSerializer):
    """
    This serializer has been inherited from RecurringTaskSerializer.
    This is used to create recurring training.
    """
    pass


class TrainingTypeSerializer(DynamicFieldsModelSerializer):
    used_budget = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainingType
        fields = (
            'title', 'description', 'budget_limit', 'slug',
            'trainings', 'used_budget', 'amount_type'
        )
        read_only_fields = 'slug', 'trainings',

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'get':
            fields['trainings'] = TrainingSerializer(
                many=True,
                context=self.context,
                fields=('name', 'start', 'end', 'status', 'slug')
            )
        return fields

    def validate(self, attrs):
        budget_limit = attrs.get('budget_limit')
        used_budget = self.request.data.get('used_budget', 0)

        if budget_limit < used_budget:
            raise ValidationError({
                'budget_limit': f'Budget limit cannot be less than used budget which is {used_budget}'
            })
        return attrs

    @staticmethod
    def validate_budget_allocated(budget):
        if budget and budget > 20000000:
            raise serializers.ValidationError(_("Ensure this value is not more than 2,00,00,000"))
        return budget

    @staticmethod
    def validate_budget_hours(budget_hours):
        if budget_hours and budget_hours > 10000:
            raise serializers.ValidationError(_("Ensure this value is not more than 10,000"))
        return budget_hours

    def create(self, validated_data):
        validated_data.update({
            'organization': self.context.get('organization')
        })
        return super().create(validated_data)


class TrainingSerializer(DynamicFieldsModelSerializer):
    created_by = UserThinSerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True
    )
    program_cost = serializers.FloatField(default=0)
    tada = serializers.FloatField(default=0)
    accommodation = serializers.FloatField(default=0)
    trainers_fee = serializers.FloatField(default=0)
    others = serializers.FloatField(default=0)

    class Meta:
        model = Training
        fields = [
            'name', 'description', 'image', 'start', 'end', 'training_type', 'id',
            'nature', 'location', 'budget_allocated', 'created_by',
            'members', 'slug', 'status', 'created_at', 'modified_at',
            'average_score', 'internal_trainers', 'external_trainers', 'coordinator',
            'visibility', 'meeting_room', 'branch', 'job_title', 'employment_type',
            'employment_level', 'division', 'program_cost','tada','accommodation',
            'trainers_fee', 'others'
        ]
        read_only_fields = 'slug', 'average_score'
        extra_kwargs = {
            'external_trainers': {
                'required': False,
                'allow_empty': True
            },
            'internal_trainers': {
                'required': False,
                'allow_empty': True
            }
        }

    def validate(self, attrs):
        start_date = attrs.get('start')
        end_date = attrs.get('end')
        nature = attrs.get('nature')
        meeting_room = attrs.get('meeting_room')
        meeting_room_id = meeting_room.id if meeting_room else None

        if nature == ONSITE and not meeting_room:
            raise serializers.ValidationError({
                'meeting_room': [
                    'Meeting room is mandatory for onsite nature.'
                ]
            })

        if nature == OFFSITE and not attrs.get('location'):
            raise serializers.ValidationError({
                'location': [
                    'Location is mandatory for offsite nature.'
                ]
            })

        if nature == OFFSITE and meeting_room:
            raise serializers.ValidationError({
                "meeting_room": [
                    'Meeting room can not be booked for Offsite nature training'
                ]
            })

        if meeting_room:
            meeting_room_instance = MeetingRoom.objects.filter(id=meeting_room_id).first()
            meeting_room_status = meeting_room_instance.get_available(
                start_at=start_date, end_at=end_date
            )
            if not meeting_room_instance:
                raise serializers.ValidationError({
                    'meeting_room': ['Invalid Meeting Room.']
                })
            elif self.instance:
                previous_room_instance = self.instance.meeting_room.meeting_room \
                    if self.instance.meeting_room else None

                if not previous_room_instance == meeting_room_instance and not meeting_room_status:
                    raise serializers.ValidationError({
                        'meeting_room': [
                            f'Meeting Room for {start_date} - {end_date} is not available.'
                        ]
                    })

            else:
                if not meeting_room_status:
                    raise serializers.ValidationError({
                        'meeting_room': [
                            f'Meeting Room for {start_date} - {end_date} is not available.'
                        ]
                    })

        if not self.instance and start_date and end_date and start_date > end_date:
            raise ValidationError({
                'start': ['Start date can\'t be greater than end date']
            })

        self._validate_training_budget(attrs)

        self._validate_trainer(attrs)

        return super().validate(attrs)

    def _validate_trainer(self, attrs):
        start_date = attrs.get('start')
        end_date = attrs.get('end')

        training = Training.objects.filter(start__lte=end_date, end__gte=start_date)
        if self.instance:
            training = training.exclude(id=self.instance.id)

        internal_trainers = attrs.get('internal_trainers')
        external_trainers = attrs.get('external_trainers')
        if internal_trainers:
            internal_trainer_training = training.filter(
                internal_trainers__in=internal_trainers
            )
            if internal_trainer_training.exists():
                raise ValidationError({
                    "internal_trainers": [
                        "Some of the internal trainers has been"
                        " already assigned to other training."
                    ]
                })

        if external_trainers:
            external_trainer_training = training.filter(
                external_trainers__in=external_trainers
            )
            if external_trainer_training.exists():
                raise ValidationError({
                    "external_trainers": [
                        "Some of the external trainers has been"
                        " already assigned to other training."
                    ]
                })

    def _validate_training_budget(self, attrs):
        budget_allocated = attrs.get('budget_allocated')
        training_type = attrs.get('training_type')
        program_cost = attrs.get('program_cost')
        tada = attrs.get('tada')
        accommodation = attrs.get('accommodation')
        trainers_fee = attrs.get('trainers_fee')
        others = attrs.get('others')

        if budget_allocated and training_type:
            _type_budget_allocated = training_type.budget_limit

            trainings_qs = training_type.trainings.all()
            if self.instance:
                trainings_qs = trainings_qs.exclude(id=self.instance.id)

            _trainings = trainings_qs.aggregate(
                total_budget_allocated=Coalesce(Sum('budget_allocated',
                                                output_field=FloatField()), 0.0),
            )

            _total_budget_allocated = _trainings.get('total_budget_allocated')

            if _total_budget_allocated:
                _total_budget_allocated += budget_allocated
            else:
                _total_budget_allocated = budget_allocated

            if _total_budget_allocated > _type_budget_allocated:
                raise ValidationError({
                    'budget_allocated': [
                        'Total budget allocated exceeded allocated budget for training type.'
                        f' Available budget is {_type_budget_allocated}'
                    ]
                })
            total_budget_breakdown = program_cost + tada + accommodation + trainers_fee + others

            if total_budget_breakdown > _total_budget_allocated:
                raise ValidationError({
                    'error': 'Sum of budget breakdown' f' {total_budget_breakdown} exceeded allocated budget for training type.'
                    f' Available budget is {budget_allocated}'
                })

            if budget_allocated < total_budget_breakdown:
                raise ValidationError({
                    'budget_allocated': f'Budget allocated cannot be less than total budget breakdown i.e. {total_budget_breakdown}'
                })

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['training_type'] = TrainingTypeSerializer(
                fields=('title', 'slug', 'amount_type')
            )
            fields['coordinator'] = UserThinSerializer(
                fields=[
                    'id', 'full_name', 'profile_picture', 'cover_picture',
                    'job_title', 'is_online','is_current', 'organization', 'email',
                    'employee_level', 'division'
                ],
                context=self.context
            )
            fields['external_trainers'] = serializers.SerializerMethodField()
            fields['internal_trainers'] = serializers.SerializerMethodField()
            fields['members'] = UserThinSerializer(many=True, read_only=True)
            fields['meeting_room'] = MeetingRoomStatusSerializer(
                fields=['id', 'room', 'booked_from', 'booked_to'],
                context=self.context
            )
            fields['branch'] = OrganizationBranchSerializer(
                many=True, context=self.context, fields=('name', 'slug')
            )
            fields['division'] = OrganizationDivisionSerializer(
                many=True, context=self.context, fields=('name', 'slug')
            )
            fields['job_title'] = EmploymentJobTitleSerializer(
                many=True, context=self.context, fields=('title', 'slug')
            )
            fields['employment_level'] = EmploymentLevelSerializer(
                many=True, context=self.context, fields=('title', 'slug')
            )
            fields['employment_type'] = EmploymentStatusSerializer(
                many=True, context=self.context, fields=('title', 'slug')
            )
        else:
            fields['training_type'] = SlugRelatedField(
                queryset=TrainingType.objects.filter(
                    organization=self.context['organization']
                ),
                slug_field='slug'
            )
            fields['meeting_room'] = serializers.PrimaryKeyRelatedField(
                queryset=MeetingRoom.objects.filter(
                    organization=self.context['organization']
                ),
                write_only=True, required=False
            )
            fields['job_title'] = serializers.SlugRelatedField(
                queryset=EmploymentJobTitle.objects.filter(
                    organization=self.context.get('organization')
                ),
                slug_field='slug', many=True, allow_null=True, allow_empty=True
            )
            fields['division'] = serializers.SlugRelatedField(
                queryset=OrganizationDivision.objects.filter(
                    organization=self.context.get('organization')
                ),
                slug_field='slug', many=True, allow_null=True, allow_empty=True
            )
            fields['employment_level'] = serializers.SlugRelatedField(
                queryset=EmploymentLevel.objects.filter(
                    organization=self.context.get('organization')
                ),
                slug_field='slug', many=True, allow_null=True, allow_empty=True
            )
            fields['branch'] = serializers.SlugRelatedField(
                queryset=OrganizationBranch.objects.filter(
                    organization=self.context.get('organization')
                ),
                slug_field='slug', many=True, allow_null=True, allow_empty=True
            )
            fields['employment_type'] = serializers.SlugRelatedField(
                queryset=EmploymentStatus.objects.filter(
                    organization=self.context.get('organization')
                ),
                slug_field='slug', many=True, allow_null=True, allow_empty=True
            )
        return fields

    def create(self, validated_data):
        external_trainers = validated_data.pop('external_trainers', [])
        internal_trainers = validated_data.pop('internal_trainers', [])
        _ = validated_data.pop('members')
        meeting_room = validated_data.get('meeting_room', None)
        if validated_data.get('nature') == ONSITE:
            meeting_room = MeetingRoomStatus.objects.create(
                meeting_room=meeting_room,
                booked_from=validated_data.get('start'),
                booked_to=validated_data.get('end')
            )
            validated_data.update({
                'meeting_room': meeting_room
            })

        instance = super().create(validated_data)
        training_attendances = self.create_trainers(
            instance=instance,
            trainers=external_trainers,
            trainer_type='external_trainers'
        )
        training_attendances += self.create_trainers(
            instance=instance,
            trainers=internal_trainers,
            trainer_type='internal_trainers'
        )

        if training_attendances:
            TrainingAttendance.objects.bulk_create(training_attendances)
            recipient_users = [
                (training_attendance.member or \
                 training_attendance.external_trainer)
                for training_attendance in training_attendances
            ]
            # send email
            email_subject = "New Training Assigned."
            email_body = (
                f"You have been assigned to training '{instance.name}' "
                f"as a trainer."
            )
            email_recipients = []
            for user in recipient_users:
                if isinstance(user, Trainer):
                    can_send_mail = email.is_email_setting_enabled_in_org(
                        instance.training_type.organization,
                        TRAINING_ASSIGNED_UNASSIGNED_EMAIL
                    )
                else:
                    can_send_mail = email.can_send_email(user, TRAINING_ASSIGNED_UNASSIGNED_EMAIL)
                if can_send_mail:
                    email_recipients.append(user.email)

            if email_recipients:
                async_task(
                    send_notification_email,
                    recipients=email_recipients,
                    subject=email_subject,
                    notification_text=email_body
                )

        initial_data = self.get_initial()

        # converting list_item from string to int
        members = set(map(int, initial_data.get('members', [])))
        members_from_hris_aspects = self.employee_under_hris_aspects(initial_data)
        users = list(members) + list(members_from_hris_aspects)

        if users:
            add_or_update_members_of_training(
                self,
                training=instance,
                users=users
            )
        return instance

    def update(self, instance, validated_data):
        start_date = validated_data.get('start')
        end_date = validated_data.get('end')
        initial_members = set(
            instance.members.values_list('id', flat=True)
        )
        members_to_be_removed = self.employee_under_hris_aspects(instance, remove=True)
        meeting_room = validated_data.pop('meeting_room', None)
        training_attendance = self.update_trainers(instance, validated_data)
        training_attendance += self.update_trainers(
            instance=instance,
            validated_data=validated_data,
            trainer_type='internal_trainers'
        )
        TrainingAttendance.objects.bulk_create(training_attendance)
        if start_date > end_date:
            raise ValidationError({
                'start': ['Start date can\'t be greater than end date']
            })
        # _current_recurring_status = False
        # _past_recurring_status = True if instance.recurring_rule else False
        #
        # if 'recurring' in validated_data.keys():
        #     recurring = validated_data.pop('recurring')
        #     if recurring:
        #         _current_recurring_status = True
        #         validated_data.update(recurring)
        #     else:
        #         # delete previous generated dates if recurring is null
        #         _ = RecurringTrainingDate.objects.filter(template=instance,
        #                                                  created_task__isnull=True).delete()
        #         validated_data.update({
        #             'recurring_first_run': None,
        #             'recurring_rule': None
        #         })

        if 'members' in validated_data:
            _ = validated_data.pop('members')
        training = super().update(instance, validated_data)

        if meeting_room:
            room = self._update_meeting_room(
                instance=instance,
                created_instance=training,
                meeting_room=meeting_room
            )
            training.meeting_room = room
            training.save()

        initial_data = self.get_initial()

        # converting list_item from string to int
        members_in_request = set(map(int, initial_data.get('members', [])))
        members = set(map(int, members_in_request)) if members_in_request else set()
        members_from_hris_aspects = self.employee_under_hris_aspects(initial_data)
        users = list(members.difference(members_to_be_removed)) + list(members_from_hris_aspects)
        members_to_remove = set(
            initial_members.difference(members_in_request)
        )
        if users or members_to_remove:
            add_or_update_members_of_training(
                self,
                training=training,
                users=users,
                update_member=True
            )

        # if _past_recurring_status and _current_recurring_status:
        #     # updated the recurring rule , so update the recurring dates accordingly.
        #     recurring_date_for_training(instance, update=True)
        # elif _current_recurring_status:
        #     # Created recurring rule so add recurring dates
        #     recurring_date_for_training(instance)

        return training

    def _update_meeting_room(self, instance, created_instance, meeting_room):
        prev_room_is_inside = (instance.nature == ONSITE)
        curr_room_is_inside = (created_instance.nature == ONSITE)
        prev_meeting_room = instance.meeting_room
        prev_meeting_room_id = instance.meeting_room_id
        if curr_room_is_inside:
            if not prev_room_is_inside:
                booked_room = MeetingRoomStatus.objects.create(
                    meeting_room_id=meeting_room,
                    booked_from=created_instance.start,
                    booked_to=created_instance.end
                )
            else:
                is_valid_meeting_room = self._validate_meeting_room(
                    training=created_instance,
                    meeting_room=meeting_room,
                    prev_room=prev_meeting_room
                )
                if not is_valid_meeting_room:
                    if prev_meeting_room:
                        MeetingRoomStatus.objects.get(id=prev_meeting_room_id).delete()
                    booked_room = MeetingRoomStatus.objects.create(
                        meeting_room_id=meeting_room.id,
                        booked_from=created_instance.start,
                        booked_to=created_instance.end
                    )
                else:
                    booked_room = prev_meeting_room
            return booked_room
        elif prev_room_is_inside and not curr_room_is_inside:
            MeetingRoomStatus.objects.get(id=prev_meeting_room_id).delete()
            return None

    @staticmethod
    def _validate_meeting_room(training, meeting_room, prev_room):
        if not prev_room or not (
            meeting_room == prev_room.meeting_room.id and training.start == prev_room.booked_from
            and training.end == prev_room.booked_to
        ):
            return False
        return True

    def update_trainers(self, instance, validated_data, trainer_type='external_trainers'):
        """
        Update trainers and send list of TrainingAttendance objects

        :param instance: Training Instance
        :type instance: Object
        :param validated_data: validated data from serializer
        :type validated_data: dict
        :param trainer_type: either 'trainers' or 'internal_trainers'
        :type trainer_type: str
        :return: list of TrainingAttendance objects
        """
        initial_data = self.get_initial()
        existing_trainers = set(getattr(instance, trainer_type).all())
        trainers = set(validated_data.pop(trainer_type, []))
        removed_trainers = existing_trainers.difference(trainers)

        if trainer_type == 'external_trainers':
            initial_external_trainers = set(
                instance.training_attendance.all().values_list('external_trainer', flat=True)
            )
            updated_external_trainers = set(map(int, initial_data.get('external_trainers', [])))
            removed_external_trainers = initial_external_trainers.difference(
                updated_external_trainers)
            added_external_trainers = updated_external_trainers.difference(
                initial_external_trainers)

            # send mail to external trainers
            if removed_external_trainers:
                email_subject = "Training unassigned."
                email_body = (
                    f"You have been removed from training '{instance.name}' "
                    f"as a trainer."
                )
                email_recipients = []
                organization = instance.training_type.organization
                for trainer_id in removed_external_trainers:
                    if trainer_id:
                        trainer = Trainer.objects.get(id=trainer_id)
                    can_send_mail = email.is_email_setting_enabled_in_org(
                        organization,
                        TRAINING_ASSIGNED_UNASSIGNED_EMAIL
                    )
                    if can_send_mail and trainer_id:
                        email_recipients.append(trainer.email)
                if email_recipients:
                    async_task(
                        send_notification_email,
                        recipients=email_recipients,
                        subject=email_subject,
                        notification_text=email_body
                    )

            if added_external_trainers:
                email_subject = "New Training Assigned."
                email_body = (
                    f"You have been assigned to training '{instance.name}' "
                    f"as a trainer."
                )
                email_recipients = []
                organization = instance.training_type.organization
                for trainer_id in added_external_trainers:
                    if trainer_id:
                        trainer = Trainer.objects.get(id=trainer_id)
                    can_send_mail = email.is_email_setting_enabled_in_org(
                        organization,
                        TRAINING_ASSIGNED_UNASSIGNED_EMAIL
                    )
                    if can_send_mail and trainer_id:
                        email_recipients.append(trainer.email)

                if email_recipients:
                    async_task(
                        send_notification_email,
                        recipients=email_recipients,
                        subject=email_subject,
                        notification_text=email_body
                    )

        if trainer_type == 'internal_trainers':
            initial_internal_trainers = set(
                instance.internal_trainers.all().values_list('id', flat=True)
            )
            updated_internal_trainers = set(map(int, initial_data.get('internal_trainers', [])))
            removed_internal_trainers = initial_internal_trainers.difference(
                updated_internal_trainers)
            added_internal_trainers = updated_internal_trainers.difference(
                initial_internal_trainers)
            # send mail to internal trainers
            if removed_internal_trainers:
                email_subject = "Training unassigned."
                email_body = (
                    f"You have been removed from training '{instance.name}' "
                    f"as a trainer."
                )
                email_recipients = []
                organization = instance.training_type.organization
                for trainer_id in removed_internal_trainers:
                    if trainer_id:
                        trainer = User.objects.get(id=trainer_id)
                        can_send_mail = email.can_send_email(
                            trainer,
                            TRAINING_ASSIGNED_UNASSIGNED_EMAIL
                        )
                        if can_send_mail:
                            email_recipients.append(trainer.email)

                if email_recipients:
                    async_task(
                        send_notification_email,
                        recipients=email_recipients,
                        subject=email_subject,
                        notification_text=email_body
                    )

            if added_internal_trainers:
                email_subject = "New Training Assigned."
                email_body = (
                    f"You have been assigned to training '{instance.name}' "
                    f"as a trainer."
                )
                email_recipients = []
                organization = instance.training_type.organization
                for trainer_id in added_internal_trainers:
                    if trainer_id:
                        trainer = User.objects.get(id=trainer_id)
                    can_send_mail = email.is_email_setting_enabled_in_org(
                        organization,
                        TRAINING_ASSIGNED_UNASSIGNED_EMAIL
                    )
                    if can_send_mail and trainer_id:
                        email_recipients.append(trainer.email)

                if email_recipients:
                    async_task(
                        send_notification_email,
                        recipients=email_recipients,
                        subject=email_subject,
                        notification_text=email_body
                    )

        if removed_trainers:
            for invalid in removed_trainers:
                getattr(instance, trainer_type).remove(invalid)

            fil = {
                'external_trainer__in': removed_trainers
            } if trainer_type == 'external_trainers' else {'member__in': removed_trainers}

            to_be_removed_trainers_attendance = instance.training_attendance.filter(**fil)
            to_be_removed_trainers_attendance.delete()

        return self.create_trainers(
            instance=instance,
            trainers=trainers.difference(existing_trainers),
            trainer_type=trainer_type
        )

    @staticmethod
    def create_trainers(instance, trainers, trainer_type):
        training_attendance = []
        if trainers:
            for new in trainers:
                getattr(instance, trainer_type).add(new)
                data = {'external_trainer': new} if trainer_type == 'external_trainers' \
                    else {'member': new}
                training_attendance.append(
                    TrainingAttendance(
                        **data,
                        training=instance,
                        position=TRAINER
                    )
                )
        return training_attendance

    @staticmethod
    def employee_under_hris_aspects(initial_data, remove=False):
        """
        Returns list of unique employee which are under different hris aspect such as division,
        branch, job_title, employment_level and employment_status/employment_type
        """
        fil = dict()
        mapping = {
            "job_title": "detail__job_title__slug__in",
            "division": "detail__division__slug__in",
            "employment_level": "detail__employment_level__slug__in",
            "branch": "detail__branch__slug__in",
            "employment_type": "detail__employment_status__slug__in"
        }
        for key, item in mapping.items():
            value = [branch.slug for branch in getattr(initial_data, key).all()] if remove \
                else initial_data.get(key)
            if value:
                fil[item] = value

        if not fil:
            return set()

        # Performs OR operation in each element of dictionary (fil)
        query = reduce(operator.or_, (Q(**{key: item}) for key, item in fil.items()))
        members_id = User.objects.filter(query).current().values_list('id', flat=True)
        return set(members_id)

    def get_external_trainers(self, instance):
        return TrainerSerializer(
            instance=instance.external_trainers.all(),
            fields=(
                'id', 'full_name', 'email', 'contact_info', 'image', 'attachments'
            ),
            context=self.context,
            many=True
        ).data

    def get_internal_trainers(self, instance):
        return UserThinSerializer(
            instance=instance.internal_trainers.all(),
            fields=[
                'id', 'full_name', 'profile_picture', 'cover_picture',
                'job_title', 'is_online','is_current', 'organization', 'email',
                'employee_level', 'division'
            ],
            context=self.context,
            many=True
        ).data


class UserTrainingSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = UserTraining
        fields = '__all__'


class UserTrainingRequestSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(read_only=True)

    class Meta:
        model = UserTrainingRequest
        fields = (
            'training', 'status', 'action_remarks', 'request_remarks', 'id', 'user'
        )

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method == 'GET':
            fields['training'] = TrainingSerializer(
                context=self.context,
                fields=('name', 'id', 'slug')
            )
        return fields

    def create(self, validated_data):
        validated_data.update({
            'user': self.request.user,
        })
        return super().create(validated_data)

    @staticmethod
    def _validate_trainee(training, user):
        start_at = training.start
        end_at = training.end

        user_training = user.user_trainings.filter(
            training__start__lte=end_at,
            training__end__gte=start_at
        ).exclude(training=training)
        if user_training.exists():
            raise ValidationError('Some of your training\'s are scheduled for this time range.')

        user_training_request = user.training_requests.filter(
            status=REQUESTED,
            training__start__lte=end_at,
            training__end__gte=start_at
        ).exclude(training=training)
        if user_training_request.exists():
            raise ValidationError(
                'You have requested for some training\'s within this time range.')

    def validate(self, attrs):
        training = attrs.get('training')
        if not training and self.instance:
            training = self.instance.training

        self._validate_trainee(training=training, user=self.request.user)
        qs = UserTrainingRequest.objects.filter(
            user=self.request.user,
            training=training
        )
        if self.instance:
            if self.instance.status in (APPROVED, DECLINED):
                raise ValidationError(
                    f'Can not act on {self.instance.get_status_display()} request.'
                )
            qs = qs.exclude()

        if qs.filter(status=REQUESTED).exists():
            raise ValidationError({
                'training': 'User have already requested for this training.'
            })
        if training and training.user_trainings.filter(user=self.request.user).exists():
            raise ValidationError({
                'training': 'User have already been assigned to this training.'
            })

        return super().validate(attrs)

    @staticmethod
    def validate_training(training):
        if training.status != PENDING:
            raise ValidationError(
                f'Can not request on {training.get_status_display()} training.'
            )
        return training

    def validate_status(self, status):
        if self.request and self.request.method in ('PUT', 'PATCH') and status == REQUESTED:
            raise ValidationError(
                'You can only approve/decline this request.'
            )
        return status

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        if status == APPROVED:
            UserTraining.objects.create(
                user=instance.user,
                training=instance.training,
                start=instance.training.start,
                end=instance.training.end,
            )

            TrainingAttendance.objects.create(
                member=instance.user,
                training=instance.training,
                position=MEMBER
            )
        actor = self.request.user if self.request.user != instance.user else get_system_admin()
        add_notification(
            text=f"Requested training \'{instance.training.name}\' has been {status}",
            recipient=instance.user,
            action=instance,
            url=f"/user/my-training",
            actor=actor,
        )

        email_subject = f"Requested training was {status}."
        email_body = f"Requested training '{instance.training.name}' has been {status}."
        email_recipients = []
        can_send_mail = email.can_send_email(instance.user, TRAINING_REQUESTED_ACTION_EMAIL)
        if can_send_mail:
            email_recipients.append(instance.user.email)

        if email_recipients:
            async_task(
                send_notification_email,
                recipients=email_recipients,
                subject=email_subject,
                notification_text=email_body
            )
        return super().update(instance, validated_data)


class TrainingMembersSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = UserTrainingRequest
        fields = ['user', ]

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['user'] = serializers.PrimaryKeyRelatedField(
                # slug_field='slug',
                queryset=User.objects.all(),
                many=True
            )
        return fields

class UserTrainingImportSerializer(serializers.Serializer):
    excel_file = serializers.FileField(
        max_length=100,
        validators=[
            FileExtensionValidator(allowed_extensions=["xlsx", "xlsm", "xltx", "xltm"]),
            ExcelFileValidator()
        ],
        write_only=True,
    )


class UserTrainingRequestMultiActionSerializer(TrainingMembersSerializer):
    class Meta:
        model = TrainingMembersSerializer.Meta.model
        fields = TrainingMembersSerializer.Meta.fields + ['status', 'action_remarks']

    def get_fields(self):
        fields = super().get_fields()
        if self.request and self.request.method.lower() == 'post':
            fields['user'] = serializers.PrimaryKeyRelatedField(
                # slug_field='slug',
                queryset=User.objects.filter(
                    id__in=self.context.get('users', [])
                ),
                many=True
            )
        return fields


class TrainerAttachmentsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TrainerAttachments
        fields = (
            'file',
            # 'attachment_type', 'file',
        )


class TrainerSerializer(DynamicFieldsModelSerializer):
    attachments = TrainerAttachmentsSerializer(
        many=True, required=False, read_only=True
    )

    class Meta:
        model = Trainer
        fields = (
            'full_name', 'email', 'description', 'contact_info', 'image',
            'attachments', 'id',
        )

    @staticmethod
    def extract_attachments(attrs, field_name='attachment'):
        attachment_keys = [x for x in attrs.keys() if x.startswith(field_name)]
        ret = dict()
        for attachment_key in attachment_keys:
            parent = attachment_key.split('.')[0]
            key = attachment_key.split('.')[-1]
            parent_dict = ret.get(parent, {})
            parent_dict.update({
                key: attrs.get(attachment_key)
            })
            ret.update({
                parent: parent_dict
            })
        return ret.values()

    @transaction.atomic()
    def create(self, validated_data):
        attachments = validated_data.pop('attachments', list())
        validated_data.update({
            'organization': self.context.get('organization')
        })
        trainer = super().create(validated_data)
        TrainerAttachments.objects.bulk_create([
            TrainerAttachments(
                **attachment,
                trainer=trainer
            ) for attachment in attachments
        ])
        return trainer

    def validate(self, attrs):
        ser = TrainerAttachmentsSerializer(
            data=list(self.extract_attachments(self.initial_data)),
            many=True
        )
        ser.is_valid(raise_exception=True)
        attrs.update({
            'attachments': ser.validated_data
        })
        return super().validate(attrs)


class TrainingAttachmentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TrainingAttachment
        fields = ('file', 'name')


class TrainingAttachmentsSerializer(DynamicFieldsModelSerializer):
    files = TrainingAttachmentSerializer(many=True, read_only=True)
    user = UserThinSerializer(
        source='created_by',
        fields=[
            'full_name', 'profile_picture', 'cover_picture',
            'job_title', 'is_online', 'organization','is_current'
        ],
        read_only=True
    )

    class Meta:
        model = TrainingAttachments
        fields = (
            'attachments_remarks', 'files', 'user'
        )
        read_only_fields = 'files',

    @staticmethod
    def extract_attachments(request_data):
        attachments = []
        if hasattr(request_data, 'getlist'):
            files = request_data.getlist('files')
        else:
            files = request_data.get('files')

        if not isinstance(files, list):
            files = [files]

        for file in files:
            attachments.append({
                'file': file,
                'name': file.name if not isinstance(file, str) else ''
            })
        return attachments

    def validate(self, attrs):
        attrs['files'] = self.extract_attachments(
            request_data=self.initial_data
        )
        remarks = attrs.get('attachments_remarks')
        files = attrs.get('files')
        if not files:
            raise ValidationError({
                'files': ['At least one file must be attached.']
            })

        if not remarks:
            raise ValidationError({
                'remarks': ['This field is required.']
            })

        return super().validate(attrs)

    @transaction.atomic()
    def create(self, validated_data):
        files = validated_data.pop('files')
        validated_data['training'] = self.context['training']
        instance = super().create(validated_data)
        TrainingAttachment.objects.bulk_create(
            [
                TrainingAttachment(
                    training_attachment=instance,
                    file=data.get('file'),
                    name=data.get('name')
                ) for data in files
            ]
        )
        return instance


class TrainingFeedbackSerializer(DynamicFieldsModelSerializer):
    user = UserThinSerializer(read_only=True, source='created_by')

    class Meta:
        model = TrainingFeedback
        fields = (
            'id', 'remarks', 'rating', 'user'
        )

    def create(self, validated_data):
        if self.request:
            validated_data['user'] = self.request.user
        validated_data['training'] = self.context.get('training')
        created = super().create(validated_data)
        calibrate_average_rating(instance=created)
        return created

    # def update(self, instance, validated_data):
    #     calibrate_average_rating(instance=instance)
    #     return super().update(instance, validated_data)

    def validate(self, attrs):
        user = self.request.user
        training = self.context.get('training')
        qs = training.feedbacks.filter(
            created_by=user
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                'You have already reviewed this training.'
            )
        return super().validate(attrs)


class TrainingAttendanceSerializer(DynamicFieldsModelSerializer):
    member = UserThinSerializer(
        fields=[
            'full_name', 'profile_picture', 'cover_picture',
            'job_title', 'is_online', 'organization','is_current'
        ],
        read_only=True
    )
    external_trainer = TrainerSerializer(
        fields=['full_name', 'email', 'description',
                'contact_info', 'image'],
        read_only=True
    )

    class Meta:
        model = TrainingAttendance
        fields = ('id', 'member', 'external_trainer', 'position', 'arrival_time', 'remarks')
        read_only_fields = 'position',
