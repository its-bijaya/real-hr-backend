from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models as M

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_complete_url
from irhrs.core.validators import validate_future_datetime
from irhrs.event.constants import (MEMBERS_INVITATION_STATUS, PENDING,
                                   EVENT_TYPE_CHOICES, PUBLIC, PRIVATE,
                                   EVENT_CATEGORY_CHOICES, OTHERS,
                                   EVENT_LOCATION, INSIDE)
from irhrs.event.utils import get_event_featured_image
from irhrs.noticeboard.models import Post
from irhrs.organization.models import MeetingRoomStatus

USER = get_user_model()


class Event(BaseModel):
    generated_from = M.ForeignKey('self', on_delete=M.CASCADE,
                                  blank=True, null=True,
                                  db_column='parent',
                                  help_text='Parent events for '
                                            'the recurring events')
    title = M.CharField(max_length=200, help_text='Title of the Event')
    description = M.TextField(blank=True, null=True, max_length=100000,
                              help_text='Description of the Event')
    location = M.CharField(blank=True, null=True, max_length=150)
    event_type = M.CharField(choices=EVENT_TYPE_CHOICES,
                             default=PUBLIC, max_length=8,
                             db_index=True)

    # this event_category is used to generate featured_image
    event_category = M.CharField(choices=EVENT_CATEGORY_CHOICES,
                                 default=OTHERS, max_length=20,
                                 db_index=True)

    start_at = M.DateTimeField(validators=[validate_future_datetime])
    end_at = M.DateTimeField(validators=[validate_future_datetime])
    _featured_image = M.ImageField(upload_to=get_event_featured_image,
                                   blank=True, null=True,
                                   db_column='featured_image')

    members = M.ManyToManyField(USER, through='EventMembers',
                                through_fields=('event', 'user'),
                                related_name='+', blank=True)
    members_can_modify = M.BooleanField(default=False,
                                        db_column='m_can_modify',
                                        help_text='If set members can '
                                                  'modify event')
    members_can_invite = M.BooleanField(default=False,
                                        db_column='m_can_invite',
                                        help_text='If set members can '
                                                  'invite other members to '
                                                  'join event')
    members_can_see_guest = M.BooleanField(default=False,
                                           db_column='m_can_see_guest',
                                           help_text='If set members can '
                                                     'see guest list')

    repeat_rule = M.CharField(blank=True, null=True, max_length=100)
    interactive_event = M.BooleanField(default=False,
                                       help_text='If set members of '
                                                 'this event can post and comment')

    event_posts = GenericRelation(Post, related_query_name="event_posts")
    enabled_event = M.BooleanField(default=True)
    event_location = M.CharField(choices=EVENT_LOCATION,
                                 default=INSIDE, max_length=8,
                                 db_index=True)
    room = M.OneToOneField(MeetingRoomStatus, related_name='event',
                           on_delete=M.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.title, self.event_type, self.created_by}"

    @property
    def featured_image(self):
        if self._featured_image:
            return get_complete_url(self._featured_image.url)

        # send featured image according to the event category
        if self.event_category in dict(EVENT_CATEGORY_CHOICES).keys():
            return get_complete_url('images/events/{}.jpg'.format(
                # Issue seen at production 'group discussion' was hit as group%20discussion.jpg
                self.event_category.lower().replace(' ', '')), att_type='static'
            )

        return get_complete_url('images/events/others.jpg', att_type='static')

    @featured_image.setter
    def featured_image(self, image):
        self._featured_image = image


class EventMembers(BaseModel):
    event = M.ForeignKey(Event, on_delete=M.CASCADE,
                         related_name='event_members')
    user = M.ForeignKey(USER, on_delete=M.CASCADE)
    invitation_status = M.CharField(choices=MEMBERS_INVITATION_STATUS,
                                    default=PENDING, max_length=9,
                                    db_index=True)

    class Meta:
        unique_together = ('event', 'user',)

    def __str__(self):
        return f"{self.event, self.user, self.invitation_status}"

