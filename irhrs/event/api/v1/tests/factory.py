from datetime import timedelta

import factory
from factory.django import DjangoModelFactory
from django.utils import timezone

from irhrs.event.models import (Event, EventMembers, EventDetail, MeetingDocument,
                                MeetingAgenda)
from irhrs.users.api.v1.tests.factory import UserFactory


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    title = factory.Faker('text', max_nb_chars=100)
    description = factory.Faker('paragraph', nb_sentences=3)
    start_at = timezone.now() + timedelta(days=1)
    end_at = timezone.now() + timedelta(days=2)


class EventMemberFactory(DjangoModelFactory):
    class Meta:
        model = EventMembers

    event = factory.SubFactory(EventFactory)
    user = factory.SubFactory(UserFactory)


class MeetingFactory(DjangoModelFactory):
    class Meta:
        model = EventDetail

    event = factory.SubFactory(EventFactory)


class MeetingDocumentFactory(DjangoModelFactory):
    class Meta:
        model = MeetingDocument


class MeetingAgendaFactory(DjangoModelFactory):
    class Meta:
        model = MeetingAgenda

    meeting = factory.SubFactory(MeetingFactory)
    title = factory.Faker('text')

# class AgendaTaskFactory(DjangoModelFactory):
#     class Meta:
#         model = AgendaTask


# class MeetingAttendanceFactory(DjangoModelFactory):
#     class Meta:
#         model = MeetingAttendance
#
#
# class AgendaCommentFactory(DjangoModelFactory):
#     class Meta:
#         model = AgendaComment
#
#
# class MeetingAcknowledgeRecordFactory(DjangoModelFactory):
#     class Meta:
#         model = MeetingAcknowledgeRecord
#
#
# class MeetingNotificationFactory(DjangoModelFactory):
#     class Meta:
#         model = MeetingNotification
