from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Prefetch, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from irhrs.core.constants.common import (
    KNOWLEDGE, SKILL, ABILITY, OTHER_ATTRIBUTES
)
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, UserMixin, IStartsWithIContainsSearchFilter, ListCreateViewSetMixin
)
from irhrs.core.utils.filters import FilterMapBackend, OrderingFilterMap
from irhrs.permission.constants.permissions import (
    HRIS_ASSIGN_KSAO_PERMISSION, HAS_PERMISSION_FROM_METHOD
)
from irhrs.permission.permission_classes import permission_factory
from ..serializers.key_skill_ability import (
    UserKSAOListSerializer, UserKSAOCreateSerializer, IndividualUserKSAOCreateSerializer,
    UserKSAOSerializer)
from ....models import UserKSAO

VALID_KSA = (KNOWLEDGE, SKILL, ABILITY, OTHER_ATTRIBUTES)


class UserKSAOViewSet(UserMixin, ListCreateViewSetMixin):
    """
    Author @rabbi

    create:
    ## Assigns KSAO to a user.

    ### Sample POST Request
    ```javascript
    {
        'ksa': 'python',
        'user': 1,
        'is_key': True
    }
    ```
    """
    serializer_class = IndividualUserKSAOCreateSerializer
    filter_backends = (
        IStartsWithIContainsSearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    permission_classes = [
        permission_factory.build_permission(
            name='UserKASOListPermission',
            limit_read_to=[
                HRIS_ASSIGN_KSAO_PERMISSION,
                HAS_PERMISSION_FROM_METHOD
            ],
            allowed_to=[HRIS_ASSIGN_KSAO_PERMISSION]
        )
    ]

    def get_queryset(self):
        qs = get_user_model().objects.filter(
            id=self.user.id
        ).only('id').prefetch_related(
            Prefetch(
                'assigned_ksao',
                queryset=self.get_ksao_queryset(),
                to_attr='ksao'
            ),
        )
        return get_object_or_404(qs, id=self.user.id)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['organization'] = self.get_organization()
        ctx['user'] = self.user
        ksa_type = self.request.query_params.get('ksa_type')
        if ksa_type and ksa_type in VALID_KSA:
            ctx['ksa_type'] = ksa_type
        return ctx

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_queryset(),
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    def has_user_permission(self):
        return self.request.user == self.user or self.is_supervisor

    # TODO: @Shital Remove or uncomment the commented lines of code if needed.
    # def get_user_queryset(self):
    #     return get_user_model().objects.all().current().only(
    #         'id'
    #     )

    @action(
        detail=False,
        url_path=r'(?P<ksao_slug>[\w\-]+)'
    )
    def get_detail_ksao(self, request, *args, **kwargs):
        instance = get_object_or_404(
            self.get_ksao_queryset(),
            ksa__slug=self.kwargs.get('ksao_slug')
        )
        return Response(
            UserKSAOSerializer(
                instance=instance,
                context={
                    **self.get_serializer_context(),
                    'description': True
                }
            ).data
        )

    def get_ksao_queryset(self):
        base_queryset = UserKSAO.objects.filter(
            user=self.user
        ).select_related(
            'ksa'
        )
        if self.action != 'get_detail_ksao':
            ksa_type = self.request.query_params.get('ksa_type')
            ordering = self.request.query_params.get('ordering')
            order_field = F('ksa__name').desc() if ordering == '-name' else F('ksa__name')
            ksa_filter = {
                'ksa__ksa_type': ksa_type
            } if ksa_type in (
                KNOWLEDGE, SKILL, ABILITY, OTHER_ATTRIBUTES
            ) else {}
            return base_queryset.filter(
                **ksa_filter
            ).order_by(
                order_field
            ).defer(
                'ksa__description'
            )
        return base_queryset.only(
            'is_key',
            'ksa__name',
            'ksa__slug',
            'ksa__description',
            'ksa__ksa_type',
        )


class UserKSAOList(OrganizationMixin, ListCreateViewSetMixin):
    queryset = get_user_model().objects.all().current()
    serializer_class = UserKSAOListSerializer
    filter_backends = (
        IStartsWithIContainsSearchFilter, OrderingFilterMap, FilterMapBackend
    )
    search_fields = (
        'first_name', 'middle_name', 'last_name'
    )
    filter_map = {
        'branch': 'detail__branch__slug',
        'division': 'detail__division__slug',
        'job_title': 'detail__job_title__slug',
        'employment_level': 'detail__employment_level__slug',
    }
    ordering_fields_map = {
        'full_name': ('first_name', 'middle_name', 'last_name',),
        KNOWLEDGE: KNOWLEDGE,
        SKILL: SKILL,
        ABILITY: ABILITY,
        OTHER_ATTRIBUTES: OTHER_ATTRIBUTES,
    }
    permission_classes = [
        permission_factory.build_permission(
            name='UserKASOPermission',
            allowed_to=[HRIS_ASSIGN_KSAO_PERMISSION]
        )
    ]

    def get_queryset(self):
        return super().get_queryset().filter(
            detail__organization=self.organization
        ).select_essentials()

    def filter_queryset(self, queryset):
        annotates = {
            ksa_type: Count(
                'assigned_ksao',
                filter=Q(assigned_ksao__ksa__ksa_type=ksa_type)
            ) for ksa_type in (KNOWLEDGE, SKILL, ABILITY, OTHER_ATTRIBUTES)
        }
        return super().filter_queryset(queryset).annotate(**annotates)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserKSAOCreateSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['organization'] = self.organization
        return ctx
