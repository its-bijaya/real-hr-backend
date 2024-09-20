from django.contrib.auth import get_user_model
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from irhrs.hris.api.v1.permissions import IDCardPermission
from irhrs.core.mixins.viewset_mixins import OrganizationMixin, OrganizationCommonsMixin
from ....models import IdCardTemplate, IdCard
from ..serializers.id_card import IdCardTemplateSerializer, IdCardSerializer, get_user_details

USER = get_user_model()


class IdCardTemplateViewSet(
    OrganizationCommonsMixin,
    OrganizationMixin,
    viewsets.ModelViewSet
):
    queryset = IdCardTemplate.objects.all()
    serializer_class = IdCardTemplateSerializer
    permission_classes = [IDCardPermission]


class IdCardViewSet(OrganizationMixin, viewsets.ModelViewSet):
    queryset = IdCard.objects.all()
    serializer_class = IdCardSerializer
    permission_classes = [IDCardPermission]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('template',)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(template__organization=self.get_organization())

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['organization'] = self.get_organization()
        return ctx

    @action(detail=False, url_path=r'user-info/(?P<user_id>\d+)')
    def user_info(self, request, **kwargs):
        user_id = kwargs.get('user_id')
        user = get_object_or_404(USER, id=user_id)
        return Response(get_user_details(user, send_representation=True))
