from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db.models import Prefetch, Q
from django.http import Http404
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.functional import cached_property
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from irhrs.core.utils.filters import FilterMapBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied, NotAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from irhrs.core.constants.user import SELF
from irhrs.core.mixins.viewset_mixins import ListViewSetMixin, IStartsWithIContainsSearchFilter, \
    UserMixin
from irhrs.core.utils.common import apply_filters, validate_permissions
from irhrs.core.utils.custom_mail import custom_mail as send_mail
from irhrs.core.utils.subordinates import find_all_subordinates
from irhrs.core.utils.user_settings_overview import get_user_settings_overview
from irhrs.organization.api.v1.serializers.organization import \
    OrganizationSerializer
from irhrs.organization.models import Organization, UserOrganization
from irhrs.permission.constants.permissions import (
    USER_PROFILE_PERMISSION,
    HRIS_PERMISSION, HAS_OBJECT_PERMISSION,
    HRIS_ASSIGN_SUPERVISOR_PERMISSION,
    HAS_PERMISSION_FROM_METHOD, AUTH_PERMISSION, USER_PROFILE_READ_ONLY_PERMISSION)
from irhrs.permission.models.hrs_permisssion import OrganizationGroup
from irhrs.permission.permission_classes import permission_factory
from irhrs.permission.utils.views import PermissionWithFilterMixin
from irhrs.recruitment.models import Country
from irhrs.users.api.v1.serializers.thin_serializers import (
    UserThinSerializer, ExtendedAuthUserThinSerializer)
from irhrs.users.api.v1.serializers.user import (
    PasswordChangeSerializer,
    UserSerializer, PasswordSetSerializer,
    AccountActivationSerializer)
from irhrs.users.models import (
    UserExperience, UserContactDetail,
    UserSupervisor)
from irhrs.users.utils.cache_utils import get_user_autocomplete_cache
from ..serializers.user_detail import (
    UserDetailSerializer,
    UserCreateSerializer)
from ....models import UserDetail, User

token_generator = PasswordResetTokenGenerator()

PasswordResetPermissionClass = permission_factory.build_permission(
    "ActivateAccountPermission",
    actions={
        "send_mail": [HAS_PERMISSION_FROM_METHOD]
    }
)


class UserFromUidb64Mixin:
    @staticmethod
    def _get_user_from_uidb64(uidb64):
        """get user from base64 encoded userid"""
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64)
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist,
                ValidationError):
            raise Http404
        return user


class UserDetailViewSet(PermissionWithFilterMixin, UserMixin, ModelViewSet):
    """
    list:

    List of users.

    available filters

        {
            "search": "search_query",
            "supervisor": user_id,
            "organization__slug": "org_slug"
        }

    `search` will `match email`, `first_name`, `middle_name` or `last_name`

    `send_supervisor=true` will include `first_level_supervisor` field

    create:

    Create User and UserDetail data =

        {
            "user": {
                "email": "email@example.com",
                "password": "password",
                "first_name": "First Name",
                "middle_name": "Middle Name",
                "last_name": "Last Name",
                "organization": organization.slug
            },
            "gender": "Male", // options = ['Male', 'Female', 'Other']
            "code": "emp_id" // max_length = 15,
            "nationality": "Nepalese",
            "date_of_birth": "1990-07-08",
            "marital_status": "Married",
            "marriage_anniversary": "2010-01-01",
            "religion": religion.slug,
            "ethnicity": ethnicity.slug

            # other fields <for other model>
            "contact": {
                "contact": {
                "name": "Name of contact person",

                "contact_of": "Self",
                //options = ["Self", "Spouse", "Sibling", "Parent", "Family",
                // "Relative", "Friend", "Office"]

                "address": "",
                "emergency": false/true,
                "number": "",

                "number_type": "Mobile",
                 // options = ["Fax", "Phone", "Mobile", "Work"]

                "email": ""
            }

            "current_address": {
                "address_type": "Permanent", // Required
                 // options = ["Permanent"/"Temporary"]
                "street": "",
                "city": "",
                "country": "",
                "address": "Address, Here", //Required
                "latitude": null,
                "longitude": null,
            }

            "employment": {
                "title": "Employment title",
                "organization": organization.slug,
                "is_current": false,
                "division": division.slug,
                "employee_level": employee_level.slug,
                "employment_status": employment_status.slug,
                "branch": branch.slug,
                "change_type": change_type.slug,
                "supervisors": [user_id1, user_id2],
                "start_date": date,
                "end_date": date,
                "job_description": "job description"
            },

            "send_activation": false // send activation mail or not
        }

    Note*: For now it will assign that organization to that user.

    Note*: Send options request for options of nationality and marital_status

    retrieve:

    User Detail

    update:

    Update user details.
    Refer to`create` docstring for update fields and their types.

    partial_update:

    Partial update user details
    Refer to`create` docstring for update fields and their types.

    destroy:

    Delete User

    change_password:

    Change Password

    data =

        {
            "old_password": "old_password",
            "password": "new_password",
            "repeat_password": "repeat_new_password"
        }

    """
    queryset = UserDetail.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'

    filter_backends = (FilterMapBackend, IStartsWithIContainsSearchFilter, OrderingFilter)
    ordering_fields = ('user__first_name', 'created_at')
    filter_map = {
        'organization slug': 'organization__slug',
        'email':'user__email',
        'branch':'branch',
        'gender':'gender'
    }
    search_fields = ('user__email',
                     'user__first_name',
                     'user__middle_name',
                     'user__last_name',)
    ordering = '-joined_date'
    permission_classes = [permission_factory.build_permission(
        "UserDetailPermission",
        allowed_to=[USER_PROFILE_PERMISSION, HAS_OBJECT_PERMISSION],
        actions={
            'create': [USER_PROFILE_PERMISSION],
            'destroy': [USER_PROFILE_PERMISSION],
            'change_password': [HAS_OBJECT_PERMISSION]
        },
        allowed_user_fields=['user'],
    )]

    def initial(self, *args, **kwargs):
        if (self.request.method.lower() != 'get' and self.request.query_params.get('as') == 'supervisor'):
            self.permission_denied(self.request)
        super().initial(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        if self.request.method.lower() == 'get':
            if not self.request.query_params.get('send_supervisor',
                                                 'false') == 'true':
                kwargs.update({'exclude_fields': ['first_level_supervisor']})
            if not self.request.query_params.get('send_subordinates',
                                                 'false') in ['true', 'True',
                                                              '1']:
                kwargs.update({'exclude_fields': kwargs.get(
                    'exclude_fields', []) + ['sub_ordinates']})
        if self.action == 'list':
            kwargs.update({
                'exclude_fields': kwargs.get('exclude_fields',
                                             []) + ['addresses',
                                                    'self_contacts',
                                                    'current_organization',
                                                    'sub_ordinates',
                                                    'current_experience']})
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self, from_me=False):

        fil = dict(user=self.request.user) if from_me else dict()

        # reduce size of prefetch if called from me
        user_organization_qs = UserOrganization.objects.filter(**fil)
        user_experience_qs = UserExperience.objects.filter(is_current=True,
                                                           **fil)
        user_contacts_qs = UserContactDetail.objects.filter(contact_of=SELF,
                                                            **fil)

        qs = super().get_queryset().exclude_admin().select_related(
            'user', 'organization', 'religion', 'ethnicity'
        ).prefetch_related(
            'user__addresses',
            Prefetch(
                'user__organization',
                queryset=user_organization_qs.select_related(
                    'organization'),
                to_attr='user_organizations'
            ),
            Prefetch(
                'user__user_experiences',
                queryset=user_experience_qs.select_related(
                    "division",
                    "employee_level",
                    "branch",
                    "job_title",
                    "organization"
                ),
                to_attr='_current_experiences'
            ),
            Prefetch(
                'user__contacts',
                queryset=user_contacts_qs,
                to_attr='self_contacts'
            )
        )
        return qs

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        # filter user list by switchable organization list and self
        user = self.request.user
        switchable_pks = user.switchable_organizations_pks
        if self.is_supervisor:
            fil = Q(user=self.user)

        elif switchable_pks:
            # if user.is_audit_user:
            #     viewable_organizations = set(user.switchable_organizations_pks)
            # else:
            viewable_organizations = set(OrganizationGroup.objects.filter(
                organization__id__in=switchable_pks,
                group__in=user.groups.all(),
                permissions__code__in=(
                    USER_PROFILE_PERMISSION.get('code'),
                    USER_PROFILE_READ_ONLY_PERMISSION.get('code')
                )
            ).values_list('organization_id', flat=True))
            fil = Q(
                organization_id__in=viewable_organizations
            ) | Q(organization__isnull=True) | Q(user_id=user.id)

        else:
            fil = Q(user_id=user.id)

        qs = qs.filter(fil)

        org_filter = self.request.query_params.get('organization_slug')
        if org_filter:
            qs = qs.filter(organization__slug=org_filter)

        no_experience = self.request.query_params.get('no_experience')
        fil = {
            'user__user_experiences__isnull': True
        } if no_experience == 'true' else {}
        return qs.filter(**fil)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({
            'organization': self.get_organization(),
            'is_hr': self.request.query_params.get('as') == 'hr'
        })
        return ctx

    @cached_property
    def _organization(self):
        user = self.request.user
        if not user and user.is_authenticated:
            return None
        org_slug = self.request.query_params.get('organization_slug')
        return Organization.objects.filter(
            id__in=self.request.user.switchable_organizations_pks,
            slug=org_slug
        ).first()

    def get_organization(self):
        return self._organization

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'change_password':
            return PasswordChangeSerializer

        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        # Do not allow deleting users
        # This method is kept here because there might be another implementation of delete in future
        return Response(status=status.HTTP_403_FORBIDDEN)

    @action(methods=['post'], detail=True, url_path='change-password',
            url_name='change-password')
    def change_password(self, request, user_id):
        user = self.get_object().user

        serializer_data = {
            'user': user.id,
            'old_password': request.data.get('old_password'),
            'password': request.data.get('password'),
            'repeat_password': request.data.get('repeat_password')
        }

        serializer_context = {'request': request}

        serializer = PasswordChangeSerializer(data=serializer_data,
                                              context=serializer_context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=['get'], detail=False, url_path='me',
            url_name='me')
    def user_info(self, request):
        user_detail = self.get_queryset().filter(
            user=request.user
        ).select_related(
            'organization', 'organization__appearance',
        ).get()
        user = user_detail.user
        data = self.get_serializer(user_detail).data
        switchable_organizations = Organization.objects.filter(
            users__user=user,
            users__can_switch=True
        ).select_related(
            'appearance'
        )

        # None, if supervisor=system_bot() | Single User, no prefetch.
        supervisor = user.first_level_supervisor

        organization_permissions = dict(
            commons=user.get_hrs_permissions()
        )

        for org in switchable_organizations:
            organization_permissions.update({
                org.slug: user.get_hrs_permissions(org)
            })

        switchable_organizations_data = OrganizationSerializer(
            switchable_organizations,
            many=True,
            fields=["name", "slug", "abbreviation",
                    "appearance", "disabled_applications"],
            context=self.get_serializer_context()
        ).data

        is_supervisor = UserSupervisor.objects.filter(
            supervisor=user).exists()

        if is_supervisor:
            sub_ordinates = list(find_all_subordinates(self.request.user.id))
            orgs = set(
                UserDetail.objects.filter(
                    user_id__in=sub_ordinates
                ).values_list('organization__slug', flat=True)
            )

            supervisor_switchable_organizations = OrganizationSerializer(
                Organization.objects.filter(slug__in=orgs).select_related(
                    'appearance'
                ), many=True,
                fields=[
                    "name", "slug", "abbreviation", "appearance",
                    "disabled_applications"
                ],
                context=self.get_serializer_context()
            ).data

            data.update({
                'supervisor_switchable_organizations': supervisor_switchable_organizations
            })

        data.update({
            'switchable_organizations': switchable_organizations_data,
            'is_supervisor': is_supervisor,
            'organization_permissions': organization_permissions,
            'supervisor': UserThinSerializer(supervisor).data if supervisor
            else None
        })
        return Response(data)

    @action(methods=['get'], detail=False, url_path='me/supervisor-info', url_name='supervisor')
    def supervisor_info(self, request):
        user = request.user
        is_supervisor = UserSupervisor.objects.filter(
            supervisor=user).exists()
        data = dict()
        if is_supervisor:
            sub_ordinates = list(find_all_subordinates(self.request.user.id))
            orgs = set(
                UserDetail.objects.filter(
                    user_id__in=sub_ordinates
                ).values_list('organization__slug', flat=True)
            )

            supervisor_switchable_organizations = OrganizationSerializer(
                Organization.objects.filter(slug__in=orgs).select_related(
                    'appearance'
                ), many=True,
                fields=[
                    "name", "slug", "abbreviation", "appearance",
                    "disabled_applications"
                ],
                context=self.get_serializer_context()
            ).data
            data['supervisor_switchable_organizations'] = supervisor_switchable_organizations
        data['is_supervisor'] = is_supervisor
        return Response(data)

    @action(methods=['get'], detail=False, url_path='me/admin-info', url_name='admin')
    def admin_info(self, request):
        user = request.user
        if not user.is_authenticated:
            raise NotAuthenticated()
        switchable_organizations = Organization.objects.filter(
            users__user=user,
            users__can_switch=True
        ).select_related('appearance')

        organization_permissions = dict(
            commons=user.get_hrs_permissions()
        )
        organization_permissions.update(
            {
                org.slug: user.get_hrs_permissions(org) for org in switchable_organizations
            }
        )

        switchable_organizations_data = OrganizationSerializer(
            switchable_organizations,
            many=True,
            fields=["name", "slug", "abbreviation",
                    "appearance", "disabled_applications"],
            context={"as": "hr", **self.get_serializer_context()}
        ).data
        is_admin = validate_permissions(
            self.request.user.get_hrs_permissions(),
            AUTH_PERMISSION
        )
        return Response(
            {
                'is_admin': is_admin,
                'switchable_organizations': switchable_organizations_data,
                'organization_permissions': organization_permissions,
            }
        )

    @action(methods=['get'], detail=True, url_path='profile-completeness', url_name='profile-completeness')
    def get_profile_completeness(self, request, user_id):
        user = self._get_object().user
        user_settings_overview_data = get_user_settings_overview(user_id, self.user, self.get_serializer_context())

        return Response(
            {
                "particulars": user_settings_overview_data,
                "profile_details": [
                    {
                        "name": "general_information",
                        "exists": hasattr(user, 'detail')
                    },
                    {
                        "name": "contact_details",
                        "exists": user.contacts.exists()
                    },
                    {
                        "name": "address",
                        "exists": user.addresses.exists()
                    },
                    {
                        "name": "education_details",
                        "exists": user.user_education.exists()
                    },
                    {
                        "name": "documents",
                        "exists": user.documents.exists()
                    },
                    {
                        "name": "bank_details",
                        "exists": hasattr(user, 'userbank')
                    },
                    {
                        "name": "medical_information",
                        "exists": hasattr(user, 'medical_info')
                    },
                    {
                        "name": "insurance_details",
                        "exists": user.insurances.exists()
                    },
                    {
                        "name": "past_experience",
                        "exists": user.past_experiences.exists()
                    },
                    {
                        "name": "employment_experience",
                        "exists": user.user_experiences.exists()
                    },
                    {
                        "name": "training_details",
                        "exists": user.trainings.exists()
                    },
                    {
                        "name": "volunteering_experience",
                        "exists": user.volunteer_experiences.exists()
                    },
                    {
                        "name": "legal_information",
                        "exists": hasattr(user, 'legal_info')
                    },
                    {
                        "name": "language",
                        "exists": user.languages.exists()
                    },
                    {
                        "name": "social_activity",
                        "exists": user.social_activities.exists()
                    },
                ]
            }
        )

    @action(
        methods=['GET'],
        detail=True,
        url_path='internal-detail',
        url_name='internal-detail'
    )
    def internal_detail(self, request, *args, **kwargs):
        """
        Basic Information detail of internal user while applying internal vacancy.

        Response:
        {
            "full_name": "Rajesh Shrestha",
            "dob": "2001-11-05",
            "gender": "Male",
            "phone_number": "98412345678",
            "marital_status": "Single",
            "country_id": 603,
            "city": "Kathmandu",
            "address": "Kathmandu, Nepal",
            "email": "info@aayulogic.com",
            "profile_picture": "http://localhost:8000/media/uploads/user/8a11ec92372d4b01bd64a25fe7398afd.png"
        }
        """
        user = self.request.user
        contact = user.contacts.order_by("-modified_at").first()
        addresses = user.addresses.order_by("-address_type").first()
        country_id = None

        if addresses:
            country_name = addresses.country
            country_db = Country.objects.filter(name__iexact=country_name).first()
            if country_db:
                country_id = country_db.id
        try:
            profile_picture = self.request.build_absolute_uri(user.profile_picture.url)
        except ValueError:
            profile_picture = None
        if user and user.is_authenticated:
            detail = {
                "full_name": user.full_name,
                "dob": user.detail.date_of_birth,
                "gender": user.detail.gender,
                "phone_number": contact.number if contact else None,
                "marital_status": user.detail.marital_status,
                "country_id": country_id,
                "city": addresses.city if addresses else None,
                "address": addresses.address if addresses else None,
                "email": user.email,
                "profile_picture": profile_picture
            }
            return Response(detail)

    def _get_object(self):
        user_detail = super().get_object()
        user = getattr(user_detail, 'user', None)
        as_hr = self.request.query_params.get('as') == 'hr'
        if not as_hr and self.request.user != user and not self.is_supervisor:
            self.permission_denied(self.request)
        return user_detail


class PasswordResetViewSet(UserFromUidb64Mixin, GenericViewSet):
    """
    create:
        Send reset mail

        data = {
            "email": "email"
        }

    set_password:
        Set password

        data = {
            "password": "new_password",
            "repeat_password": "new_password"
        }
    """
    permission_classes = []
    queryset = User.objects.all()

    def get_serializer(self, *args, **kwargs):
        if self.action == 'create':
            kwargs.update({'fields': ['email']})
            return UserSerializer(*args, **kwargs)
        else:
            return PasswordSetSerializer(*args, **kwargs)

    def create(self, request):
        """send reset mail"""
        user = self._get_user_from_email(request.data.get('email'))
        if user and user.is_active:
            # generate token and user_id for active user
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            self.send_mail(user, uidb64, token)
        return Response({'message': _(
            "A password reset link will be sent to your email address."
        )})

    @action(methods=['post', 'get'], detail=False,
            url_path=r'set/(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)',
            url_name='set-password'
            )
    def set_password(self, request, uidb64, token):
        user = self._get_user_from_uidb64(uidb64)

        if user.is_active and token_generator.check_token(user, token):
            # validate link if request is get
            if request.method == 'GET':
                return Response(status=200)
            data = {
                'user': user.id,
                'password': request.data.get('password'),
                'repeat_password': request.data.get('repeat_password')
            }
            serializer = PasswordSetSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            raise Http404

    def send_mail(self, user, uidb64, token):
        """
        Send reset mail
        :param email: email to send reset link
        :param uidb64: userid encoded in base64
        :param token: reset token
        :param lang: email content language
        :return:
        """
        lang = translation.get_language()
        lang_d = {
            'subject': _("RealHRSoft Password Reset Link")
        }

        reset_link = settings.FRONTEND_URL + f"/account/reset/" \
                                             f"{uidb64}/{token}/"

        context = {
            "full_name": user.full_name,
            "reset_link": settings.FRONTEND_URL + f"/{lang}" + f"/account/reset/"
                                                               f"{uidb64}/{token}/"
            if lang != 'en' else reset_link
            # since en is default, same link would work
        }
        # Here no need to validate lang if it exists or not because lang has
        # already been validated in previous steps and will contain `en` as
        # fallback

        txt_message_template = 'users/password_reset_email_{}.txt'.format(lang)
        html_message_template = 'users/password_reset_email_{}.html'.format(
            lang)
        message = render_to_string(txt_message_template,
                                   context=context,
                                   request=self.request)

        html_message = render_to_string(
            html_message_template,
            context=context,
            request=self.request)
        send_mail(lang_d['subject'], message, "admin@realhrsoft.com",
                  [user.email],
                  html_message=html_message)

    @staticmethod
    def _get_user_from_email(email):
        """get user for given email"""
        if not email:
            raise ValidationError({"email": ["This field is required"]})
        try:
            user = User.objects.get(email=email)
        except (User.DoesNotExist, ValueError):
            return None
        return user


class AccountActivationViewSet(UserFromUidb64Mixin, GenericViewSet):
    """
    activate_account:

    Activate user account

        data = {
            "password": "new_password",
            "repeat_password": "new_password"
        }

    send_mail:

    Send Account activation mail

        data = {
            "users": [user_id1, user_id2, user_id3, ...]
        }
    """
    permission_classes = []
    serializer_class = PasswordSetSerializer

    def get_serializer_class(self):
        if self.action == 'send_mail':
            return AccountActivationSerializer
        return super().get_serializer_class()

    @action(methods=['post', 'get'], detail=False,
            url_path=r'activate/(?P<uidb64>[^/.]+)/(?P<token>[^/.]+)',
            url_name='activate'
            )
    def activate_account(self, request, uidb64, token):
        user = self._get_user_from_uidb64(uidb64)

        if not (user.is_active or user.is_blocked) and \
            token_generator.check_token(user, token):
            if request.method == 'GET':
                return Response(status=200)
            data = {
                'user': user.id,
                'password': request.data.get('password'),
                'repeat_password': request.data.get('repeat_password')
            }
            serializer = PasswordSetSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            user = self._get_user_from_uidb64(uidb64)
            user.is_active = True
            user.save()
            return Response({'status': 'Successfully activated account'})
        else:
            raise Http404

    @action(methods=['post'], detail=False,
            url_path=r'send',
            url_name='send-mail'
            )
    def send_mail(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        users = serializer.validated_data.get('users', [])
        organizations = list(map(lambda user: user.detail.organization, users))
        validated = all([validate_permissions(
            self.request.user.get_hrs_permissions(organization=organization),
            USER_PROFILE_PERMISSION
        ) for organization in organizations])
        if not validated:
            raise PermissionDenied
        serializer.save()
        return Response(serializer.data)


class UserAutoComplete(ListViewSetMixin):
    """
    User Auto Complete

        filters

              organization = organization_slug
              division = division_slug
              have_experience = true ==> Returns user list having experience

    """
    queryset = User.objects.filter(detail__isnull=False)
    serializer_class = ExtendedAuthUserThinSerializer
    pagination_class = None

    def get_queryset(self):
        """
        Update: @Ravi: 17-Apr-2019. Add subordinate filter
        Update: @Ravi: 19-JUL-2019. Add user_status filter.
            * Allows HR to select between currently employed and past users.
        Patch: @Ravi: 09-JAN-2020. Fix `past_user` not visible.
            * HRIS_PERMISSION is organization-specific.
        """
        supervisor = self.request.query_params.get('supervisor')
        immediate_subordinates = self.request.query_params.get('immediate_subordinates') == 'true'
        blocked = self.request.query_params.get('is_blocked', 'false')
        active = self.request.query_params.get('is_active', 'true')
        has_attendance = self.request.query_params.get('has_attendance')
        user_type = self.request.query_params.get('user_status')
        assign_supervisor = self.request.query_params.get('assign_supervisor')
        organization_slug = self.request.query_params.get('organization')
        # Default is_hr and assign_supervisor_permission
        has_assign_supervisor = is_hr = False
        if organization_slug:
            try:
                organization = Organization.objects.get(
                    id__in=self.request.user.switchable_organizations_pks,
                    slug=organization_slug
                )
                user_permissions = self.request.user.get_hrs_permissions(organization)
                is_hr = validate_permissions(
                    user_permissions,
                    HRIS_PERMISSION
                )
                has_assign_supervisor = validate_permissions(
                    user_permissions,
                    HRIS_ASSIGN_SUPERVISOR_PERMISSION
                )
            except Organization.DoesNotExist:
                # is_hr = false, has_assign_supervisor = false by default
                # let the user use normal user autocomplete
                pass

        fil = {
            'is_blocked': False,
            'is_active': True
        }
        excludes = {}
        extra_fil = {}

        if user_type in ['current', 'past']:
            fil.pop('is_active', None)
            fil.pop('is_blocked', None)
            if user_type == 'current':
                self.queryset= self.queryset.current()
                fil.update({
                    'user_experiences__is_current': True
                })
            else:
                self.queryset = self.queryset.past()
                # excludes.update({
                #     'user_experiences__is_current': True
                # })
        else:
            if active == 'false':
                fil['is_active'] = False
            elif active == 'all':
                fil.pop('is_active', None)
            if blocked == 'true':
                fil['is_blocked'] = True
            elif blocked == 'all':
                fil.pop('is_blocked', False)

        if has_assign_supervisor and assign_supervisor in ['true', 'True', '1']:
            extra_fil.update({
                'email__iexact': getattr(settings,
                                         'SYSTEM_BOT_EMAIL',
                                         'irealhrbot@irealhrsoft.com')
            })

        if has_attendance in ['true', 't']:
            fil['attendance_setting__isnull'] = False
        elif has_attendance in ['false', 'f']:
            fil['attendance_setting__isnull'] = True
        elif supervisor:
            if supervisor == str(self.request.user.id):
                fil['id__in'] = self.request.user.subordinates_pks
            if immediate_subordinates:
                fil['id__in'] = self.request.user.as_supervisor.filter(
                    authority_order=1
                ).values_list('user', flat=True)


        return super().get_queryset().exclude(
            **excludes
        ).filter(
            Q(**fil) | Q(**extra_fil)
        ).select_related(
            'detail', 'detail__organization', 'detail__job_title',
            'detail__division', 'detail__employment_level'
        ).order_by('first_name')

    def filter_queryset(self, queryset):
        filtered_qs = apply_filters(
            self.request.query_params,
            {
                'organization': 'detail__organization__slug',
                'division': 'detail__division__slug'
            },
            super().filter_queryset(queryset)
        )
        have_experience = self.request.query_params.get("have_experience")
        supervisors_list = self.request.query_params.get("supervisors_list")
        if have_experience:
            filtered_qs = filtered_qs.filter(
                user_experiences__isnull=False).distinct()
        if supervisors_list:
            filtered_qs = filtered_qs.filter(
                as_supervisor__isnull=False).distinct()
        return filtered_qs

    def list(self, request, *args, **kwargs):
        if not request.query_params:
            return Response(get_user_autocomplete_cache())

        return super().list(request, *args, **kwargs)
