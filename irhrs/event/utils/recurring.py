"""@irhrs_docs"""

import datetime
from copy import deepcopy

from dateutil.rrule import rrulestr
from django.utils import timezone

from irhrs.event.constants import PENDING, INSIDE, MEETING
from ..models import Event, EventMembers


def create_recurring_events(event, update=False):
    rule = event.repeat_rule
    first_run = event.start_at.date()
    if update:
        deleted, _ = Event.objects.filter(
            generated_from=event, start_at__gt=timezone.now()
        ).delete()
        # print("total deleted objects %d" % deleted)
        first_run = Event.objects.filter(
            generated_from=event
        ).order_by('-created_at').first() or first_run
    try:
        date_list = list(rrulestr(rule, dtstart=first_run))
    except ValueError:
        date_list = []
    for date in date_list:
        if date.date() == first_run:
            continue
        _start_end_difference = event.end_at - event.start_at
        _start = datetime.datetime.combine(date, event.start_at.time())
        _end = datetime.datetime.combine(
            (_start + _start_end_difference).date(), event.end_at.time()
        )
        _start_at = timezone.localtime(_start.replace(tzinfo=timezone.utc))
        _end_at = timezone.localtime(_end.replace(tzinfo=timezone.utc))
        _start_at = timezone.make_aware(_start)
        _end_at = timezone.make_aware(_end)
        evnt = deepcopy(event)
        evnt.id = None
        evnt.start_at = _start_at
        evnt.end_at = _end_at
        evnt.repeat_rule = None
        evnt.generated_from = event
        if evnt.event_location == INSIDE:
            room = evnt.room
            if room:
                _room = deepcopy(room)
                _room.id = None
                _room.booked_from = _start_at
                _room.booked_to = _end_at
                _room.save()
                evnt.room = _room
        evnt.save()
        for i in EventMembers.objects.filter(event=event):
            _i = deepcopy(i)
            _i.id = None
            _i.event = evnt
            _i.invitation_status = PENDING
            _i.save()

        if evnt.event_category == MEETING:
            meeting = getattr(event, 'meeting', None)
            if meeting:
                _meeting = deepcopy(meeting)
                _meeting.id = None
                _meeting.event = evnt
                _meeting.save()

                _documents = meeting.documents.all()
                for doc in _documents:
                    _doc = deepcopy(doc)
                    _doc.id = None
                    _doc.meeting = _meeting
                    _doc.save()

                agendas = meeting.meeting_agendas.all()
                for agenda in agendas:
                    _agenda = deepcopy(agenda)
                    _agenda.id = None
                    _agenda.meeting = _meeting
                    _agenda.discussion = None
                    _agenda.decision = None
                    _agenda.discussed = False
                    _agenda.save()

                attendances = meeting.meeting_attendances.all()
                for attendance in attendances:
                    _attendance = deepcopy(attendance)
                    _attendance.id = None
                    _attendance.meeting = _meeting
                    _attendance.arrival_time = None
                    _attendance.remark = None
                    _attendance.save()

                notifications = meeting.notifications.all()
                for notification in notifications:
                    _notification = deepcopy(notification)
                    _notification.meeting = _meeting
                    _notification.id = None
                    _notification.notified = False
                    _notification.save()

