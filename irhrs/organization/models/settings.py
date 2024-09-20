from django.core.validators import MinValueValidator
from django.db import models, transaction

from irhrs.common.models import BaseModel
from irhrs.core.constants.organization import APPLICATION_CHOICES, EMAIL_TYPE_CHOICES
from irhrs.organization.models import Organization


class ContractSettings(models.Model):
    organization = models.OneToOneField(
        to=Organization, on_delete=models.CASCADE, editable=False,
        related_name='contract_settings'
    )
    safe_days = models.IntegerField(default=30, validators=[
        MinValueValidator(limit_value=0)])
    critical_days = models.IntegerField(default=15, validators=[
        MinValueValidator(limit_value=0)])

    class Meta:
        verbose_name_plural = 'Contract Settings'


class ApplicationSettings(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name='application_settings')
    application = models.CharField(choices=APPLICATION_CHOICES, max_length=25)
    enabled = models.BooleanField(default=True)
    # this condition satisfies whether application is available for HR or not
    # if queryset exists and enabled is true hr has permission else he doesn't

    class Meta:
        unique_together = ['organization', 'application']
        verbose_name_plural = 'Application Settings'

    def __str__(self):
        return f'Organization: {self.organization}, Application: {self.application}'


class EmailNotificationSetting(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='email_settings'
    )
    email_type = models.PositiveSmallIntegerField(choices=EMAIL_TYPE_CHOICES)
    send_email = models.BooleanField(default=False)
    allow_unsubscribe = models.BooleanField(default=True)

    class Meta:
        unique_together = ('organization', 'email_type')

    def __str__(self):
        return f"{self.organization.name} - {self.get_email_type_display()}"

    @classmethod
    def reset_setting(cls, organization):
        with transaction.atomic():
            for email_type, display_name in EMAIL_TYPE_CHOICES:
                cls.objects.update_or_create(
                    organization=organization,
                    email_type=email_type,
                    defaults={
                        'send_email': False,
                        'allow_unsubscribe': True
                    }
                )
