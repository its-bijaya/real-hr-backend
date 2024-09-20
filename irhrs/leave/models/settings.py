from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_today
from irhrs.core.validators import validate_future_date
from irhrs.leave.constants.model_constants import LEAVE_TYPE_CATEGORIES, \
    IDLE, EXPIRED, ACTIVE, \
    APPLICABLE_GENDER_CHOICES, APPLICABLE_MARITAL_STATUS_CHOICES
from irhrs.leave.managers.setting import MasterSettingManager
from irhrs.organization.models import Organization

USER = get_user_model()


class MasterSetting(BaseModel):
    name = models.CharField(max_length=150)
    organization = models.ForeignKey(
        to="organization.Organization",
        on_delete=models.CASCADE,
        related_name="leave_master_settings"
    )
    description = models.TextField(max_length=600)
    effective_from = models.DateField(
        validators=[validate_future_date],
        null=True
    )
    effective_till = models.DateField(null=True, blank=True)

    accumulation = models.BooleanField()
    renewal = models.BooleanField()
    deductible = models.BooleanField()

    paid = models.BooleanField()
    unpaid = models.BooleanField()
    half_shift_leave = models.BooleanField()

    occurrences = models.BooleanField()
    beyond_balance = models.BooleanField()
    proportionate_leave = models.BooleanField()
    depletion_required = models.BooleanField()

    require_experience = models.BooleanField()
    require_time_period = models.BooleanField()
    require_prior_approval = models.BooleanField()
    require_document = models.BooleanField()
    leave_limitations = models.BooleanField()
    leave_irregularities = models.BooleanField()

    employees_can_apply = models.BooleanField()
    admin_can_assign = models.BooleanField()

    continuous = models.BooleanField()
    holiday_inclusive = models.BooleanField()

    encashment = models.BooleanField()
    carry_forward = models.BooleanField()
    collapsible = models.BooleanField()

    years_of_service = models.BooleanField()
    time_off = models.BooleanField()
    compensatory = models.BooleanField()

    credit_hour = models.BooleanField(null=True, help_text="Flag to enable Credit Hour System.")

    cloned_from = models.ForeignKey(
        to='leave.MasterSetting',
        related_name='cloned_settings',
        on_delete=models.SET_NULL,
        null=True,
    )

    objects = MasterSettingManager()

    class Meta:
        unique_together = ('name', 'organization')

    def __str__(self):
        return f"{self.name} - {self.organization.name}"

    @property
    def status(self):
        # to prevent circular import
        from irhrs.leave.models import LeaveRule

        today = get_today()
        if not self.effective_from or self.effective_from > today:
            return IDLE
        elif self.effective_till and self.effective_till < today:
            return EXPIRED
        elif LeaveRule.objects.filter(
            leave_type__master_setting=self,
        ).exists():
            return ACTIVE
        return IDLE


class LeaveType(BaseModel):
    master_setting = models.ForeignKey(
        MasterSetting,
        on_delete=models.CASCADE,
        related_name='leave_types'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(
        max_length=600
    )

    applicable_for_gender = models.CharField(
        choices=APPLICABLE_GENDER_CHOICES,
        max_length=10,
        blank=True,
        db_index=True
    )
    applicable_for_marital_status = models.CharField(
        choices=APPLICABLE_MARITAL_STATUS_CHOICES,
        max_length=10,
        blank=True,
        db_index=True
    )

    category = models.CharField(
        choices=LEAVE_TYPE_CATEGORIES,
        max_length=20,
        db_index=True
    )

    email_notification = models.BooleanField(null=True, )
    sms_notification = models.BooleanField(null=True, )

    is_archived = models.BooleanField(default=False)
    visible_on_default = models.BooleanField(
        default=True
    )
    multi_level_approval = models.BooleanField(default=False)
    cloned_from = models.ForeignKey(
        to='leave.LeaveType',
        related_name='cloned_leave_types',
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        unique_together = ('name', 'master_setting')

    def __str__(self):
        return self.name


class LeaveApproval(BaseModel):
    organization = models.ForeignKey(
        Organization,
        related_name='leave_approval',
        on_delete=models.CASCADE
    )
    employee = models.ForeignKey(
        USER,
        related_name='leave_approval',
        on_delete=models.CASCADE
    )
    authority_order = models.IntegerField()

    class Meta:
        unique_together = [
            ['organization', 'employee'],
            ['organization', 'authority_order']
        ]

    def __str__(self):
        return f'{self.employee}.'
