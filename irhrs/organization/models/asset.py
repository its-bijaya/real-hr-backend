from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property
from sorl import thumbnail

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.constants.organization import ASSET_STATUS, \
    IDLE, RELEASE_REMARK, DAMAGED, ASSIGNED_TO_CHOICES, USER, DIVISION_BRANCH, MEETING_ROOM
from irhrs.core.utils.common import get_upload_path, get_complete_url, get_today
from irhrs.core.validators import (validate_title, validate_past_date_or_today,
                                   validate_future_date, validate_image_file_extension)
from irhrs.organization.models import Organization, OrganizationDivision, \
    OrganizationBranch, MeetingRoom

User = get_user_model()


class OrganizationEquipment(BaseModel, SlugModel):
    """
    Organization Equipment refers to the tangible equipments of the organization which
    is required for the on-boarding / off-boarding process.
    """
    name = models.CharField(max_length=150, validators=[validate_title])
    code = models.CharField(max_length=50)
    brand_name = models.CharField(max_length=150, blank=True)
    amount = models.FloatField(validators=[MinValueValidator(0)], default=0)
    purchased_date = models.DateField(null=True,
                                      validators=[validate_past_date_or_today])
    service_order = models.CharField(max_length=50, blank=True)
    bill_number = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=16, blank=True)
    assigned_to = models.CharField(max_length=50,
                                   choices=ASSIGNED_TO_CHOICES,
                                   db_index=True)
    organization = models.ForeignKey(Organization, related_name='equipments',
                                     on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(to='common.EquipmentCategory',
                                 related_name='equipments',
                                 on_delete=models.CASCADE,
                                 null=True)
    is_damaged = models.BooleanField(default=False)
    specifications = models.TextField(max_length=100000, blank=True)
    acquired_date = models.DateField(auto_now_add=True, null=True)
    released_date = models.DateField(null=True, blank=True)
    released_remark = models.CharField(max_length=16, choices=RELEASE_REMARK,
                                       null=True, blank=True)
    equipment_picture = thumbnail.ImageField(
        upload_to=get_upload_path, blank=True,
        validators=[validate_image_file_extension]
    )
    remark = models.CharField(max_length=512, blank=True)

    def __str__(self):
        return "{}'s Equipment - {} ".format(
            self.organization,
            self.name
        )

    @staticmethod
    def is_currently_assigned_filter(called_from_equipment_model=False,
                                     called_from_equipment_assignments=True):
        # if filter is called from OrganizationEquipment queryset
        # first go to `assignments` reverse relation and start filtering
        if called_from_equipment_model:
            filter = Q(
                            Q(
                                assignments__isnull=False
                            ) &
                            Q(
                                Q(
                                    Q(assignments__released_date__isnull=False) &
                                    Q(
                                        assignments__released_date__gt=get_today()
                                      )
                                ) |
                                Q(
                                    assignments__released_date__isnull=True
                                ),
                                is_damaged=False
                            )
                        )

            return filter

        if called_from_equipment_assignments:
            # by default, assume this function will be called to
            # filter queryset of type EquipmentAssignedTo
            filter = Q(
                Q(
                    Q(
                        Q(released_date__isnull=False) &
                        Q(released_date__gt=get_today()
                          )
                    ) |
                    Q(
                        released_date__isnull=True
                    ),
                    equipment__is_damaged = False
                )
            )
            return filter

    @property
    def is_currently_assigned(self):
        return self.assignments.filter(
            self.is_currently_assigned_filter()
        ).exists()

    @cached_property
    def equipment_picture_thumb(self):
        if self.equipment_picture:
            return get_complete_url(
                thumbnail.get_thumbnail(
                    self.equipment_picture, '84x84',
                    crop='center', quality=90
                ).url
            )
        return None


class EquipmentAssignedTo(BaseModel):
    equipment = models.ForeignKey(OrganizationEquipment, related_name='assignments',
                                  on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, related_name='equipments',
                             on_delete=models.SET_NULL, null=True)
    division = models.ForeignKey(OrganizationDivision, related_name='equipments',
                                 on_delete=models.SET_NULL, blank=True,
                                 null=True)
    branch = models.ForeignKey(OrganizationBranch, related_name='equipments',
                               on_delete=models.SET_NULL, blank=True, null=True)
    meeting_room = models.ForeignKey(MeetingRoom, related_name='equipments',
                                     on_delete=models.SET_NULL, blank=True,
                                     null=True)
    assigned_date = models.DateField(default=get_today)
    released_date = models.DateField(null=True)

    @property
    def assigned_to(self):
        return {
            USER: self.user,
            DIVISION_BRANCH: f'{self.division} and {self.branch}',
            MEETING_ROOM: self.meeting_room
        }.get(self.equipment.assigned_to)

    def __str__(self):
        return f'{self.equipment.name} is assigned to {self.assigned_to}'

    class Meta:
        verbose_name_plural = 'Equipment Assigned To'


class AssignedEquipmentStatus(BaseModel):
    assigned_equipment = models.ForeignKey(EquipmentAssignedTo, related_name='status',
                                           on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=16, choices=ASSET_STATUS,
                              default=DAMAGED, db_index=True)
    confirmed = models.BooleanField(default=False)
    confirmed_by = models.ForeignKey(User, related_name='equipment_status',
                                     on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.assigned_equipment} has status {self.status}'

    class Meta:
        verbose_name_plural = 'Assigned Equipment Status'
