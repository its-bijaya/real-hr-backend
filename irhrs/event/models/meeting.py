from datetime import datetime
from itertools import chain

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.event.constants import MEMBER, MEMBER_POSITION
from irhrs.task.models import Task
from .event import Event, EventMembers

User = get_user_model()


class EventDetail(BaseModel):
    """
    Record about meeting
    """
    time_keeper = models.ForeignKey(EventMembers, related_name='time_keepers',
                                    on_delete=models.SET_NULL, null=True,
                                    blank=True)
    minuter = models.ForeignKey(EventMembers, related_name='minuters',
                                on_delete=models.SET_NULL, null=True,
                                blank=True)
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    other_information = models.TextField(max_length=100000, null=True,
                                         blank=True)
    prepared = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.event.title} created by {self.event.created_by}"

    def present_status(self, present_at):
        start_date = self.event.start_at
        end_date = self.event.end_at
        if datetime.now().astimezone() < start_date < end_date:
            return None
        elif not present_at and start_date < datetime.now().astimezone() < end_date:
            return None
        elif not present_at and start_date < end_date < datetime.now().astimezone():
            return 'Absent'
        elif present_at <= start_date < end_date:
            return 'On Time'
        elif start_date < present_at:
            return 'Late'


class MeetingDocument(BaseModel):
    meeting = models.ForeignKey(EventDetail, related_name='documents',
                                on_delete=models.CASCADE)
    document = models.FileField(
        upload_to=get_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=list(chain.from_iterable(settings.ACCEPTED_FILE_FORMATS.values()))
        )]
    )
    caption = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f'{self.document} | {self.caption}'


class MeetingAgenda(BaseModel):
    """
    Keeps record of agenda for meeting.
    Can be multiple agenda for a meeting.
    """
    meeting = models.ForeignKey(EventDetail, related_name='meeting_agendas',
                                on_delete=models.CASCADE)
    title = models.TextField(max_length=2000)
    discussion = models.TextField(max_length=100000, null=True, blank=True)
    decision = models.TextField(max_length=100000, null=True, blank=True)
    discussed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"


class AgendaTask(BaseModel):
    """
    Keeps record about task for a agenda.
    Can be multiple task for single agenda.
    """
    agenda = models.ForeignKey(MeetingAgenda, related_name='agenda_tasks',
                               on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='agenda_tasks',
                             on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.agenda} task {self.task}"


class MeetingAttendance(BaseModel):
    """
    Keep track of user attendance.
    """
    member = models.ForeignKey(User, related_name='present_members',
                               on_delete=models.CASCADE)
    meeting = models.ForeignKey(EventDetail, related_name='meeting_attendances',
                                on_delete=models.CASCADE)
    position = models.CharField(max_length=22, choices=MEMBER_POSITION, default=MEMBER,
                                db_index=True)
    arrival_time = models.DateTimeField(null=True)
    remarks = models.CharField(max_length=1000, null=True)

    class Meta:
        unique_together = ['member', 'meeting']

    def __str__(self):
        return f"{self.member}"


class AgendaComment(BaseModel):
    agenda = models.ForeignKey(
        MeetingAgenda, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=True, max_length=1000)
    commented_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='agenda_comments',
        editable=False)

    def __str__(self):
        return f'{self.content}'


class MeetingAcknowledgeRecord(BaseModel):
    meeting = models.ForeignKey(EventDetail, related_name='acknowledge_records',
                                on_delete=models.CASCADE)
    acknowledged = models.BooleanField(default=False)
    member = models.ForeignKey(User,
                               related_name='acknowledge_meeting',
                               on_delete=models.CASCADE)

    def __str__(self):
        return f'Acknowledged by {self.member.user}' if self.acknowledged \
            else f'Acknowledgement for pending {self.member.user}'


class MeetingNotification(BaseModel):
    meeting = models.ForeignKey(EventDetail, related_name='notifications',
                                on_delete=models.CASCADE)
    time = models.PositiveIntegerField(validators=[MinValueValidator(10)])
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f'Time is {self.time} minutes'
