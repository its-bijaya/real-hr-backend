from django.utils import timezone

from django.db import models
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers, status


class InputChoiceSerializer(serializers.Serializer):
    label = serializers.ReadOnlyField(source='__str__')

    def __init__(self, *args, **kwargs):
        self.input_choice = kwargs.pop('input_choice', False)
        self.choice_fields = kwargs.pop('choice_fields', False)
        super().__init__(*args, **kwargs)

    def get_field_names(self, declared_fields, info):
        if self.input_choice:
            if self.choice_fields:
                return self.choice_fields
            return ('label', 'id')
        else:
            return super().get_field_names(declared_fields, info)


class NoPaginationMixin(object):
    @property
    def paginator(self):
        self._paginator = None
        return self._paginator


class InputChoiceMixin(object):
    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        if self.action in ('choices',):
            self._paginator = None
        return self._paginator

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        choice_fields = None
        if hasattr(self, 'choice_fields'):
            choice_fields = self.choice_fields
        if self.action in ('choices',):
            kwargs['choice_fields'] = choice_fields
            kwargs['input_choice'] = True
        return serializer_class(*args, **kwargs)

    @action(methods=['get'], detail=False)
    def choices(self, request):
        return self.list(request, choice_list=True)


class VueRouteMixin(object):
    def get_vue_route_name(self):
        return 'home'

    def get_vue_route_params(self):
        return {}

    def get_vue_route_queries(self):
        return {}

class DestroyProtectedModelMixin(object):
    """
    Destroy a model protected instance.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except models.ProtectedError as err:
            protected_objects = err.protected_objects
            if isinstance(protected_objects, list):
                protected_objects = protected_objects[:2]
            response = {
                'message': 'The object is protected as it is used by the following objects.',
                'protected_obj_routes': [
                    {
                        'name': str(obj),
                        'vue_route_name': obj.get_vue_route_name(),
                        'vue_route_params': obj.get_vue_route_params(),
                        'vue_route_queries': obj.get_vue_route_queries()
                    } for obj in protected_objects
                ],
                'remaining': len(err.protected_objects) - len(protected_objects)
            }
            return Response(response, status=status.HTTP_406_NOT_ACCEPTABLE)

    def perform_destroy(self, instance):
        instance.delete()

    # @action(detail=True, methods=['delete'])
    # def soft(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     instance.soft_delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class SoftDeletionQuerySet(models.QuerySet):
    def soft_delete(self):
        return super(SoftDeletionQuerySet, self).update(deleted_at=timezone.now())

    def delete(self):
        return super(SoftDeletionQuerySet, self).delete()

    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.exclude(deleted_at=None)


class SoftDeletionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super(SoftDeletionManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            return SoftDeletionQuerySet(self.model).filter(deleted_at=None)
        return SoftDeletionQuerySet(self.model)

    def delete(self):
        return self.get_queryset().delete()


class SoftDeletionModel(VueRouteMixin, models.Model):
    """
        deleted_at acts as is_active=True/False
    """
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeletionManager()
    all_objects = SoftDeletionManager(alive_only=False)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def delete(self):
        super(SoftDeletionModel, self).delete()

    class Meta:
        abstract = True
