from django.db import models


class PostManager(models.Manager):
    # def get_queryset(self):
    #     return super().get_queryset().filter(object_id__isnull=True)

    def get_events_posts(self):
        return super().get_queryset().filter(object_id__isnull=False)

    def get_posts(self):
        return super().get_queryset().filter(objects_id__isnull=True)
