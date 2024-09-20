from django.contrib.auth import get_user_model
from django.forms import model_to_dict
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.mixins.serializers import DynamicFieldsModelSerializer
from irhrs.core.utils import get_system_admin, nested_getattr
from irhrs.core.utils.common import DummyObject
from irhrs.users.api.v1.serializers.thin_serializers import UserThinSerializer
from irhrs.users.models import UserSupervisor

User = get_user_model()


class UserSupervisorSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = UserSupervisor
        fields = ('id', 'user', 'supervisor', 'authority_order', 'approve',
                  'forward', 'deny', 'user_organization', 'supervisor_organization')
        extra_kwargs = {
            'user_organization': {'write_only': True},
            'supervisor_organization': {'write_only': True},
        }

    def get_fields(self):
        fields = super().get_fields()
        if self.request.method == 'GET':
            fields['supervisor'] = UserThinSerializer()
        return fields

    def validate(self, attrs):
        request_data = self.context['request'].data
        # Validation for request data in list
        if isinstance(request_data, list):
            supervisors_id = list()
            no_supervisor_errors = []
            error_raised = False
            for data in request_data:
                if data.get('supervisor'):
                    supervisors_id.append(data['supervisor'])
                    no_supervisor_errors.append({})
                else:
                    no_supervisor_errors.append(
                        {'supervisor': ['Please provide supervisor.']})
                    error_raised = True
            if error_raised:
                raise serializers.ValidationError(no_supervisor_errors)
            unique_supervisors = set(supervisors_id)
            if len(supervisors_id) != len(unique_supervisors):
                raise serializers.ValidationError(
                    {'supervisor': ['Duplicate supervisors found.']})

        # validate for same user as supervisor
        user = attrs.get('user')
        approve = attrs.get('approve')
        forward = attrs.get('forward')
        deny = attrs.get('deny')
        authority_order = attrs.get('authority_order')
        if user == attrs['supervisor']:
            raise serializers.ValidationError(
                {'supervisor': ['Cannot assign supervisor to self.']})

        # validate for no authority given at all
        if not any([approve, forward, deny]):
            raise serializers.ValidationError(
                {'supervisor': ['At least one authority is required.']})

        user_supervisor = UserSupervisor.objects.filter(user=user)
        if user_supervisor:
            upper_authority = user_supervisor.filter(
                authority_order__gt=authority_order
            ).exists()
            lower_authority = user_supervisor.filter(
                authority_order__lt=authority_order
            ).exists()
            if not lower_authority and authority_order > 1:
                raise serializers.ValidationError({
                    'authority_order': 'Please assign supervisor in chain.'
                })
            if not upper_authority:
                if not approve:
                    raise serializers.ValidationError({
                        'approve': 'Further authority not found. '
                                   'Final authority must include approval authority.'
                    })
                if authority_order == 3 and forward:
                    raise serializers.ValidationError({
                        'forward': 'Further authority not found. '
                                   'Final authority cannot include forward authority.'
                    })

        return attrs


class UserSupervisorsViewSerializer(UserThinSerializer):
    supervisors = serializers.SerializerMethodField(read_only=True)

    class Meta(UserThinSerializer.Meta):
        model = User
        fields = UserThinSerializer.Meta.fields + ['supervisors', 'username']

    def get_supervisors(self, instance):
        supervisors = instance.user_supervisors
        return UserSupervisorSerializer(supervisors,
                                        context={'request': self.context['request']},
                                        many=True).data

    def get_system(self, instance):
        return instance.supervisors.filter(supervisor=get_system_admin()).exists()

    def get_fields(self):
        fields = super().get_fields()
        request = self.context['request']
        if request and request.method.lower() == 'get':
            fields['system'] = serializers.SerializerMethodField()
        return fields


class SupervisorDetailSerializer(DynamicFieldsModelSerializer):
    supervisor = serializers.IntegerField(min_value=0)

    class Meta:
        model = UserSupervisor
        fields = ('supervisor', 'authority_order', 'approve',
                  'forward', 'deny')


class UserSupervisorDetailSerializer(DynamicFieldsModelSerializer):
    supervisors = SupervisorDetailSerializer(many=True,
                                             required=False,
                                             allow_null=True,
                                             write_only=True)
    has_supervisor = serializers.BooleanField(default=True, write_only=True)
    ignore_all_authority_change = serializers.BooleanField(default=False, write_only=True, allow_null=True, required=False)
    ignore_first_level_authority_change = serializers.BooleanField(default=False, write_only=True, allow_null=True, required=False)
    ignore_second_level_authority_change = serializers.BooleanField(default=False, write_only=True, allow_null=True, required=False)
    ignore_third_level_authority_change = serializers.BooleanField(default=False, write_only=True, allow_null=True, required=False)

    class Meta:
        model = UserSupervisor
        fields = ('user', 'supervisors', 'has_supervisor',
                   'ignore_all_authority_change', 'ignore_first_level_authority_change',
                    'ignore_second_level_authority_change', 'ignore_third_level_authority_change')

    def validate(self, attrs):
        if not attrs.get('has_supervisor'):
            return attrs
        errors = dict()
        supervisors = attrs.get('supervisors', None)
        for supervisor in supervisors:
            approve = supervisor.get('approve', None)
            forward = supervisor.get('forward', None)
            deny = supervisor.get('deny', None)
            if approve is None:
                errors.update({
                    "approve": _("This field may not be blank.")
                })
            if forward is None:
                errors.update({
                    "forward": _("This field may not be blank.")
                })
            if deny is None:
                errors.update({
                    "deny": _("This field may not be blank.")
                })
        if errors:
            raise ValidationError(errors)

        if attrs['has_supervisor'] and not supervisors:
            raise ValidationError({'supervisors': 'Supervisor is required.'})

        # check the missing authority, or maintenance of authority order.
        authority_sum_expected = sum(
            range(len(supervisors) + 1))
        authority_sum = sum([
            f.get('authority_order') for f in supervisors
        ])
        if authority_sum != authority_sum_expected:
            raise ValidationError({
                "message": f"Please set the authority in order for {attrs.get('user').full_name}."
            })
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        has_supervisor = validated_data['has_supervisor']
        if has_supervisor:
            supervisors = validated_data.get('supervisors', None)
            for supervisor in supervisors:
                _supervisor = User.objects.get(id=supervisor.get('supervisor'))
                _supervisor_organization = nested_getattr(_supervisor, 'detail.organization')
                if not _supervisor_organization:
                    raise ValidationError(
                        "Unable to assign supervisor. Selected supervisor has no organization."
                    )
                supervisor.update({
                    'user': user.id,
                    'user_organization': user.detail.organization.id,
                    'supervisor_organization': _supervisor_organization.id
                })
        else:
            supervisors = [
                {
                    'user': user.id,
                    'supervisor': get_system_admin().id,
                    'authority_order': 1,
                    'approve': True,
                    'forward': False,
                    'deny': False,
                    'user_organization': user.detail.organization.id,
                    'supervisor_organization': None
                }
            ]
        UserSupervisor.objects.filter(user=validated_data.get('user')).delete()
        serializer = UserSupervisorSerializer(data=supervisors,
                                              context=self.context,
                                              many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return DummyObject(**validated_data)



def append_error(_full_name, errors, error_msg):
    if _full_name in errors.keys():
        errors[_full_name] += ", " + _full_name + " " + error_msg
        return errors
    errors[_full_name] = _full_name + " " + error_msg
    return errors



def get_existing_supervisor(_user, _supervisors, authority_order, ignore_level):
    if ignore_level:
        supervisor = _user.supervisors.filter(authority_order=authority_order).first()
        if supervisor:
            _supervisors.append(model_to_dict(supervisor))



def handle_forward_error(_max_authority_order, _full_name, _authority_order, errors, error_msg):
    if _max_authority_order and _max_authority_order.get('forward') and \
            _max_authority_order.get('authority_order') == _authority_order:
        errors = append_error(_full_name, errors, error_msg)
        return errors
    


def handling_missing_authority(_ids:list, _max_authority_number,  authority_orders_tbc:int, 
                                       _authority_orders:list, _full_name, errors, error_msg):
    if (_max_authority_number in _ids) and authority_orders_tbc not in _authority_orders:
        errors = append_error(_full_name, errors, error_msg)


class BulkAssignSupervisorSerializer(UserSupervisorDetailSerializer):
    def validate(self, attrs):
        attrs = dict(attrs)
        errors = {}
        user = attrs.get('user')
        full_name = user.full_name
        ignore_first = attrs.get('ignore_first_level_authority_change')
        ignore_second = attrs.get('ignore_second_level_authority_change')
        ignore_third = attrs.get('ignore_third_level_authority_change')
        supervisors = attrs.get('supervisors', [])

        get_existing_supervisor(user, supervisors, 1, ignore_first)
        get_existing_supervisor(user, supervisors, 2, ignore_second)
        get_existing_supervisor(user, supervisors, 3, ignore_third)

        supervisors_id = [item["supervisor"] for item in supervisors]
        authority_orders = [item["authority_order"] for item in supervisors]

        if user.id in supervisors_id:
            append_error(
                full_name,
                errors,
                "can not have self as a supervisor."
            )
        
        if len(supervisors_id) != len(set(supervisors_id)):
            errors = append_error(
                full_name,
                errors,
                "has conflict in assigning supervisor due to duplicate\
                 supervisor at different level."
            )
        if supervisors:
            max_authority_order = max(supervisors,
                                  key=lambda x: x.get('authority_order', float('-inf')))
            max_authority_number = max_authority_order.get('authority_order')

            handling_missing_authority([2, 3], max_authority_number, 
                                       1, authority_orders, full_name, errors, 
                                       "do not have first level supervisor."
                                       )
            handling_missing_authority([3], max_authority_number,
                                        2, authority_orders, full_name, errors,
                                        "do not have second level supervisor."
                                        )
            
            handle_forward_error(max_authority_order, full_name, 1, errors,
                                "do not have second level supervisor to set forward \
                                      permission for first level supervisor.")
            handle_forward_error(max_authority_order, full_name, 2, errors,
                                "do not have third level supervisor to set forward \
                                      permission for second level supervisor.")

        if errors:
            raise ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        user = validated_data['user']
        has_supervisor = validated_data['has_supervisor']
        if has_supervisor:
            supervisors = validated_data.get('supervisors', [])

            for supervisor in supervisors:
                _supervisor = User.objects.get(id=supervisor.get('supervisor'))
                _supervisor_organization = nested_getattr(_supervisor, 'detail.organization')

                if not _supervisor_organization:
                    raise ValidationError(
                        "Unable to assign supervisor. Selected supervisor has no organization."
                    )

                supervisor.update({
                    'user': user.id,
                    'user_organization': user.detail.organization.id,
                    'supervisor_organization': _supervisor_organization.id
                })

        else:
            supervisors = [
                {
                    'user': user.id,
                    'supervisor': get_system_admin().id,
                    'authority_order': 1,
                    'approve': True,
                    'forward': False,
                    'deny': False,
                    'user_organization': user.detail.organization.id,
                    'supervisor_organization': None
                }
            ]
        user.supervisors.all().delete()
        serializer = UserSupervisorSerializer(data=supervisors,
                                              context=self.context,
                                              many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return DummyObject(**validated_data)

class BulkReplaceSupervisorSerializer(serializers.Serializer):

    existing_supervisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    new_supervisor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    def validate(self, attrs):
        existing_supervisor = attrs.get('existing_supervisor')
        new_supervisor = attrs.get('new_supervisor')
        if not new_supervisor.current_experience:
            raise serializers.ValidationError({
                'new_supervisor': ['Cannot replace past employee.']
            })
        if new_supervisor == get_system_admin().id:
            raise serializers.ValidationError({
                'new_supervisor': ["Cannot replace system bot as supervisor."]
            })
        if existing_supervisor == new_supervisor:
            raise serializers.ValidationError({
                'new_supervisor': ['Cannot replace exiting supervisor as new supervisor.']
            })

        return attrs

    def create(self, validated_data):
        self.replace_supervisor_in_bulk(validated_data)

        return DummyObject(**validated_data)

    def replace_supervisor_in_bulk(self, validated_data):
        existing_supervisor = validated_data['existing_supervisor']
        new_supervisor = validated_data['new_supervisor']
        user_supervisors = UserSupervisor.objects.filter(
            supervisor=existing_supervisor
        ).exclude(user=new_supervisor)
        self.replace_supervisor_after_deleting_user_as_supervisor(
            new_supervisor, existing_supervisor
        )

        for user_supervisor in user_supervisors:
            base_qs = UserSupervisor.objects.filter(
                user=user_supervisor.user
            )

            new_user_supervisor = base_qs.filter(
                supervisor_id=new_supervisor
            ).first()

            if not new_user_supervisor:
                user_supervisor.supervisor = new_supervisor
                user_supervisor.save()
                continue

            self.replace_if_same_supervisor_found_in_other_level(
                user_supervisor, new_user_supervisor, new_supervisor
            )
            self.replace_if_higher_authority_not_found(base_qs)

    @staticmethod
    def replace_if_same_supervisor_found_in_other_level(
        user_supervisor, new_user_supervisor, new_supervisor
    ):
        # replace supervisor to highest priority if same supervisor
        # is found in other level
        existing_authority = user_supervisor.authority_order
        new_supervisor_authority = new_user_supervisor.authority_order
        authority_order = (
            existing_authority
            if existing_authority < new_supervisor_authority
            else new_supervisor_authority
        )

        user_supervisor.authority_order = authority_order
        user_supervisor.supervisor = new_supervisor
        user_supervisor.save()
        # deleting supervisor with lowest priority after replacing to highest
        # priority if same supervisor is found in other level
        new_user_supervisor.delete()

    @staticmethod
    def replace_if_higher_authority_not_found(base_qs):
        # replace supervisor to higher authority if higher authority doesn't exist
        highest_level_supervisor = base_qs.order_by("-authority_order").first()

        if highest_level_supervisor:
            highest_level_supervisor.forward = False
            authority_orders = set(base_qs.values_list(
                "authority_order", flat=True
            ))
            # after replacing supervisor if there is gap between supervisor shift
            # lower authority to higher
            if authority_orders == {1, 3}:
                highest_level_supervisor.authority_order -= 1

            highest_level_supervisor.save()

    @staticmethod
    def replace_supervisor_after_deleting_user_as_supervisor(
        new_supervisor, existing_supervisor
    ):
        # Deleting supervisor if replaced supervisor is the user.
        user_as_supervisor = UserSupervisor.objects.filter(
            user=new_supervisor,
            supervisor=existing_supervisor
        ).first()

        if not user_as_supervisor:
            return
        users_authority_order = user_as_supervisor.authority_order
        user_as_supervisor.delete()
        users_supervisors_authority_order = new_supervisor.supervisors.filter(
            authority_order__gt=users_authority_order
        )

        # after deleting user as supervisor replace remaining supervisors to
        # higher authority
        for user_supervisor in users_supervisors_authority_order:
            user_supervisor.authority_order -= 1
            user_supervisor.save()

        # changing forward = false if only one supervisor is available after
        # deleting user as supervisor
        available_supervisor = new_supervisor.supervisors.all().order_by(
            "authority_order"
        ).last()
        if not available_supervisor:
            return
        available_supervisor.forward = False
        available_supervisor.save()
