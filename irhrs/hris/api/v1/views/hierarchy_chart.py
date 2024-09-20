from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response

from irhrs.core.mixins.viewset_mixins import (
    UserMixin,
    RetrieveViewSetMixin)
from irhrs.core.utils import get_system_admin
from irhrs.core.utils.subordinates import find_supervisor
from irhrs.hris.api.v1.serializers.hierarchy_chart import \
    HierarchyChartSerializer
from irhrs.hris.utils.hierarchy_chart import (
    build_hierarchy_chart,
    get_relationship)

User = get_user_model()


class HierarchyChartView(UserMixin, RetrieveViewSetMixin):
    queryset = User.objects.all()
    serializer_class = HierarchyChartSerializer

    def retrieve(self, request, *args, **kwargs):
        category = self.kwargs.get('category')
        user = self.get_object()
        response = getattr(self, f'get_{category.lower()}')(user=user)
        if isinstance(response, Response):
            return response
        return Response(response)

    def get_children(self, user):
        if not isinstance(user, int):
            user = user.id

        return {'children': self.get_serializer_class()(
            build_hierarchy_chart(supervisors=user, user=user),
            many=True).data}

    def get_siblings(self, user):
        if not isinstance(user, int):
            user = user.id
        supervisor = find_supervisor(user)
        data = self.get_serializer_class()(
            build_hierarchy_chart(supervisors=supervisor, user=user),
            many=True
        ).data if supervisor else []
        return {'siblings': data}

    def get_parent(self, user):
        supervisor = find_supervisor(user.id)
        system_admin = get_system_admin().id
        if supervisor and not system_admin == supervisor:
            user = User.objects.get(id=supervisor)
            return self.get_serializer_class()({
                'user': user,
                'relationship': get_relationship(supervisor, system_admin)
            }).data
        return Response({'detail': 'Parent not found.'}, status.HTTP_404_NOT_FOUND)

    def get_family(self, user):
        if self.request.query_params.get('children') in ['true', 'True', '1']:
            family = self.get_serializer_class()({
                'user': user,
                'relationship': get_relationship(user.id, get_system_admin().id)
            }).data
            children = self.get_children(user=user)
            family.update({'children': children['children']})
        else:
            family = self.get_parent(user=user)
            children = self.get_siblings(user=user)
            if not isinstance(family, Response):
                family.update({'children': children['siblings']})
            else:
                family = {'user': {
                    'cover_picture': "http://localhost:8000/static/images/default/cover.png",
                    'employee_level': "System",
                    'full_name': "RealHRsoft",
                    'job_title': "System",
                    'profile_picture': "http://localhost:8000/static/images/default/male.png",
                },
                    'relationship': '001',
                    'children': children['siblings']
                }
        return family
