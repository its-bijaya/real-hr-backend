from django.db.models.signals import pre_delete, post_delete, post_save
from irhrs.hris.utils.utils import update_user_profile_completeness
from irhrs.users.models import (
    UserDetail,
    UserAddress,
    UserContactDetail,
    UserMedicalInfo,
    UserLegalInfo,
    UserEducation,
    UserLanguage
)
from django.dispatch import receiver

from irhrs.hris.models import EmployeeChangeTypeDetail


@receiver(pre_delete, sender=EmployeeChangeTypeDetail)
def delete_upcoming_experiences(sender, instance, using, **kwargs):
    delete_experience = instance.new_experience
    if delete_experience:
        delete_experience.delete()


@receiver(post_save, sender=UserEducation)
@receiver(post_delete, sender=UserEducation)
@receiver(post_save, sender=UserContactDetail)
@receiver(post_delete, sender=UserContactDetail)
@receiver(post_save, sender=UserAddress)
@receiver(post_delete, sender=UserAddress)
@receiver(post_save, sender=UserMedicalInfo)
@receiver(post_delete, sender=UserMedicalInfo)
@receiver(post_save, sender=UserLegalInfo)
@receiver(post_delete, sender=UserLegalInfo)
@receiver(post_save, sender=UserLanguage)
@receiver(post_delete, sender=UserLanguage)
@receiver(post_save, sender=UserEducation)
@receiver(post_delete, sender=UserEducation)
def recacalculate_user_profile_completeness(sender, instance, using, **kwargs):
    update_user_profile_completeness(instance.user)
