from django.http import Http404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.appraisal.api.v1.permissions import PerformanceAppraisalQuestionSetPermission
from irhrs.appraisal.api.v1.serializers.question_set import \
    PerformanceAppraisalQuestionSetSerializer, QuestionSetUserTypeSerializer, \
    CopyQuestionSetSerializer, EditQuestionSetSerializer
from irhrs.appraisal.api.v1.views.performance_appraisal import SubPerformanceAppraisalMixin
from irhrs.appraisal.models.question_set import PerformanceAppraisalQuestionSet
from irhrs.core.mixins.viewset_mixins import (
    OrganizationMixin, OrganizationCommonsMixin, ListViewSetMixin
)


class PerformanceAppraisalQuestionSetViewSet(OrganizationCommonsMixin, OrganizationMixin,
                                             ModelViewSet):
    queryset = PerformanceAppraisalQuestionSet.objects.all()
    serializer_class = PerformanceAppraisalQuestionSetSerializer
    permission_classes = [PerformanceAppraisalQuestionSetPermission]

    @action(
        detail=True,
        methods=['get'],
        url_path=r'question/(?P<question_id>\d+)/user-type',
        serializer_class=QuestionSetUserTypeSerializer
    )
    def user_type(self, request, *args, **kwargs):
        instance = self.get_object().appraisal_user_type.filter(
            question=kwargs.get('question_id')
        ).first()
        if not instance:
            raise Http404
        serializer = self.get_serializer(
            instance,
            context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @user_type.mapping.post
    def post_user_type(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        instance = self.get_object().appraisal_user_type.filter(
            question=kwargs.get('question_id')
        ).first()

        if not instance:
            raise Http404

        for user_type in ['branches', 'divisions', 'job_titles', 'employment_levels']:
            user_type_instance = getattr(instance, user_type)
            user_type_instance.clear()
            user_type_instance.add(*validated_data.get(user_type))
        instance.save()
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['delete'],
        url_path=r'question/(?P<question_id>\d+)'
    )
    def delete_user_type(self, request, *args, **kwargs):
        queryset = self.get_object().appraisal_user_type.filter(
            question=kwargs.get('question_id')
        )
        if not queryset:
            raise Http404
        queryset.delete()
        return Response({'detail': 'Deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class QuestionSetActionViewSet(OrganizationMixin, SubPerformanceAppraisalMixin, ListViewSetMixin):

    def list(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='get')

    @action(
        detail=False, methods=['post'],
        serializer_class=EditQuestionSetSerializer,
        url_path='edit'
    )
    def edit_question_set(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        serializer_class=CopyQuestionSetSerializer,
        url_path='copy'
    )
    def copy_question_set(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
