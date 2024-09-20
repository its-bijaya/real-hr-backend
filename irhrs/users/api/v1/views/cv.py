from django.db.models import Value, BooleanField
from rest_framework.response import Response

from irhrs.core.constants.common import SKILL
from irhrs.core.mixins.viewset_mixins import RetrieveViewSetMixin, UserMixin, ListViewSetMixin
from irhrs.core.utils import nested_get
from irhrs.core.utils.common import DummyObject
from irhrs.permission.constants.permissions import USER_PROFILE_PERMISSION, \
    HAS_PERMISSION_FROM_METHOD
from irhrs.permission.permission_classes import permission_factory
from irhrs.users.api.v1.serializers.education import UserEducationSerializer
from irhrs.users.api.v1.serializers.experience import UserExperienceSerializer
from irhrs.users.api.v1.serializers.training import UserTrainingSerializer
from irhrs.users.api.v1.serializers.volunteer_experience import UserVolunteerExperienceSerializer


class UserCVViewSet(UserMixin, ListViewSetMixin):

    CV_FIELDS = [
            'general',
            'objectives',
            'education',
            'experience',
            'training',
            'volunteering',
            'skills',
            'language',
        ]
    permission_classes = [permission_factory.build_permission(
        "ContactDetailPermission",
        allowed_to=[USER_PROFILE_PERMISSION, HAS_PERMISSION_FROM_METHOD]
    )]

    def has_user_permission(self):
        return self.request.user == self.user

    def list(self, request, *args, **kwargs):
        return_data = {
            field: getattr(self, f'get_{field}', lambda u: None)(self.user)
            for field in self.CV_FIELDS
        }
        return Response(return_data)

    @staticmethod
    def get_general(user):
        self_contact = user.self_contacts.first()
        phone_number = getattr(self_contact, 'number', None)
        # email = getattr(self_contact, 'email', None)
        address = user.addresses.order_by('-address_type').first()  # temporary/permanent order

        return {
            'full_name': user.full_name,
            'job_title': getattr(user.detail.job_title, 'title', None),
            'phone_number': phone_number,
            'email': user.email,
            'address': getattr(address, 'address', None),
            'profile_picture': user.profile_picture_thumb,
            'cover_picture': user.cover_picture_thumb,
            'date_of_birth': user.detail.date_of_birth,
            'nationality': user.detail.nationality,
            'ethnicity': getattr(user.detail.ethnicity, 'name', None),
            'religion': getattr(user.detail.religion, 'name', None),
            'marital_status': user.detail.marital_status,
            'gender': user.detail.gender
        }

    @staticmethod
    def get_objectives(user):
        return getattr(user.current_experience, 'objective', None)

    def get_education(self, user):
        return UserEducationSerializer(
            user.user_education.all(),
            many=True,
            context=self.get_serializer_context()
        ).data

    @staticmethod
    def get_experience(user):
        past_experiences = list(user.past_experiences.annotate(
            is_current=Value(False, output_field=BooleanField())
        ).order_by('start_date').values(
            'title',
            'organization',
            'responsibility',
            'start_date',
            'end_date',
            'is_current'
        ))
        current_experiences = [
            {
                'title': nested_get(exp, 'job_title.title'),
                'organization': nested_get(exp, 'organization.name'),
                'responsibility': nested_get(exp, 'job_description'),
                'start_date': nested_get(exp, 'start_date'),
                'end_date': nested_get(exp, 'end_date'),
                'is_current': nested_get(exp, 'is_current')
            }
            for exp in
            UserExperienceSerializer(
                user.user_experiences.all().order_by('-start_date'),
                many=True,
                fields=('job_title', 'organization', 'job_description',
                        'start_date', 'end_date', 'is_current'),
                context={'request': DummyObject(method='GET')}
            ).data
        ]
        return current_experiences + past_experiences

    def get_training(self, user):
        return UserTrainingSerializer(
            user.trainings.all(),
            context=self.get_serializer_context(),
            many=True,
            exclude_fields=['user']
        ).data

    def get_volunteering(self, user):
        return UserVolunteerExperienceSerializer(
            user.volunteer_experiences.all(),
            many=True,
            context=self.get_serializer_context()
        ).data

    @staticmethod
    def get_skills(user):
        return user.assigned_ksao.filter(ksa__ksa_type=SKILL).values_list(
            'ksa__name', flat=True)

    @staticmethod
    def get_language(user):
        return user.languages.values_list('name', flat=True)
