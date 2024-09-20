from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property

from irhrs.common.models import BaseModel, SlugModel
from irhrs.core.utils.common import get_upload_path, get_complete_url
from irhrs.core.validators import validate_address, validate_invalid_chars, validate_image_file_extension
from irhrs.organization.models import Organization, OrganizationBranch


class MeetingRoom(BaseModel, SlugModel):
    organization = models.ForeignKey(
        Organization,
        related_name='meeting_rooms',
        on_delete=models.CASCADE)
    branch = models.ForeignKey(
        OrganizationBranch,
        related_name='meeting_rooms',
        on_delete=models.SET_NULL,
        blank=True, null=True)
    name = models.CharField(max_length=150, unique=True, validators=[validate_invalid_chars])
    description = models.TextField(max_length=100000, blank=True)
    location = models.CharField(max_length=500, validators=[validate_address])
    floor = models.CharField(max_length=100, validators=[validate_invalid_chars])
    area = models.CharField(max_length=150, blank=True)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.name}"

    def get_available(self, start_at, end_at):
        return not self.status.filter(
                booked_from__lte=end_at,
                booked_to__gte=start_at
        ).exists()

    @cached_property
    def featured_image(self):
        featured_image = self.attachments.first()
        if featured_image:
            return get_complete_url(featured_image.image.url)
        else:
            return get_complete_url(
                'images/events/meeting.jpg',
                att_type='static'
            )


class MeetingRoomAttachment(BaseModel):
    meeting_room = models.ForeignKey(
        MeetingRoom,
        on_delete=models.CASCADE,
        related_name='attachments')
    image = models.ImageField(upload_to=get_upload_path,
                              blank=True, validators=[validate_image_file_extension])
    caption = models.CharField(max_length=255,
                               blank=True)

    def __str__(self):
        return f"{self.caption}"


class MeetingRoomStatus(BaseModel):
    meeting_room = models.ForeignKey(
        MeetingRoom,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='status'
    )
    booked_from = models.DateTimeField()
    booked_to = models.DateTimeField()

    def __str__(self):
        return f"{self.booked_from}"

    class Meta:
        verbose_name_plural = 'Meeting Room Status'
