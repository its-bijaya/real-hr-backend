import types
from typing import Optional

from django.db.models import ProtectedError
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from irhrs.core.mixins.viewset_mixins import UserCommonsMixin, ListViewSetMixin
from irhrs.core.utils.common_utils import nested_getattr
from irhrs.core.utils.dependency import get_dependency
from irhrs.users.api.v1.serializers.experience import \
    UserExperienceSerializer, UserExperienceHistorySerializer
from irhrs.users.models.experience import UserExperience


class UserExperienceViewSet(UserCommonsMixin, ModelViewSet):
    """
    list:
    Lists User Experience for the selected User.

    create:
    Create new User Experience for the given User.

    retrieve:
    Get User Experience of the User.

    delete:
    Deletes the selected User Experience of the User.

    update:
    Updates the selected User Experience details for the given User.

    """
    queryset = UserExperience.objects.filter(
        upcoming=False
    )
    serializer_class = UserExperienceSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('job_title__title',)

    def initial(self, *args, **kwargs):
        if (
            self.request.method.lower() != 'get'
            and self.request.query_params.get('as') == 'supervisor'
        ):
            self.permission_denied(self.request)
        super().initial(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            kwargs.update({'exclude_fields': ['job_description', 'objective']})
        return super().get_serializer(*args, **kwargs)

    def has_user_permission(self):
        if self.request.method.upper() == "GET":
            if self.is_current_user() or self.is_supervisor:
                return True
        return super().has_user_permission()

    @action(detail=False, url_path='inactive-experiences')
    def list_inactive(self, request, *args, **kwargs):
        def get_queryset(self):
            return UserExperience.objects.include_upcoming().filter(
                upcoming=True
            ).filter(
                user=self.user
            )

        self.get_queryset = types.MethodType(get_queryset, self)
        return super().list(request, *args, **kwargs)

    @action(detail=False, url_path='current')
    def current_experience(self, request, *args, **kwargs):
        def get_object(self_):
            return self.user.current_experience

        self.get_object = types.MethodType(get_object, self)
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        start_date = obj.start_date

        get_last_payroll_generated_date, installed = get_dependency(
            'irhrs.payroll.utils.helpers.get_last_payroll_generated_date')
        payroll_last_generated = get_last_payroll_generated_date(obj.user)

        if payroll_last_generated and start_date <= payroll_last_generated:
            raise ValidationError({
                'detail': 'Could not delete experience. '
                          'Payroll has been generated using this experience.'
            })

        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ValidationError({
                'detail': 'Could not delete experience. '
                          'Please remove assigned payroll packages first'
            })


class UserExperienceHistoryViewSet(UserCommonsMixin, ListViewSetMixin):
    serializer_class = UserExperienceHistorySerializer
    queryset = UserExperience.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        history_list = []

        for i in range(queryset.count() - 1):
            current_experience = queryset[i]
            previous_experience = queryset[i + 1]
            text = get_user_experience_history_text(current_experience, previous_experience)
            history_list.append({
                'start_date': current_experience.start_date,
                'text': text,
                'change_type': current_experience.change_type or 'Updated'
            })

        history_list.append({
            'start_date': self.user.detail.joined_date,
            'text': "As " + (nested_getattr(queryset.last(), "job_title.title") or "N/A"),
            'change_type': 'Joined'
        })

        page = self.paginate_queryset(history_list)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(history_list, many=True)
        return Response(serializer.data)


def get_user_experience_history_text(
    current_experience: UserExperience,
    previous_experience: UserExperience
) -> Optional[str]:
    """

    :param current_experience:
    :param previous_experience:
    :return: text

    The priority of text to be displayed depends on the order of attributes in
    text_attributes list.

    To get the attribute's value attrgetter is used. In case there is an attribute error,
    the attribute's value is set to "N/A". Return early if we detect attribute change
    and return the corresponding text.
    """

    text_attributes = [
        'job_title.title',
        'employment_status.title',
        'branch.name',
        'employee_level.title',
        'current_step'
    ]

    for nested_attr in text_attributes:
        previous_value = nested_getattr(previous_experience, nested_attr) or "N/A"
        current_value = nested_getattr(current_experience, nested_attr) or "N/A"

        if nested_attr == "current_step":
            previous_value = f"Step {previous_value}"
            current_value = f"Step {current_value}"

        if previous_value != current_value:
            text = f"To {current_value} From {previous_value}"
            return text
