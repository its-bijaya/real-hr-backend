from django.db.models.signals import post_save
from django.dispatch import receiver

from irhrs.recruitment.models import (
    Job, JobSetting
)


@receiver(post_save, sender=Job)
def create_job_setting(sender, instance, created, **kwargs):
    if created:
        JobSetting.objects.create(job=instance)

