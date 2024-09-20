from django.contrib import admin

from .models import Event, EventMembers
from .models.meeting import *

from irhrs.core.utils.admin.filter import SearchByTitle, AdminFilterByDate

# Events
admin.site.register(Event, SearchByTitle)
admin.site.register(EventMembers, AdminFilterByDate)

# Meeting
admin.site.register(MeetingAgenda, SearchByTitle)
admin.site.register(EventDetail, AdminFilterByDate)
admin.site.register(MeetingAcknowledgeRecord, AdminFilterByDate)
admin.site.register(MeetingAttendance, AdminFilterByDate)
admin.site.register(MeetingDocument, AdminFilterByDate)
admin.site.register(MeetingNotification, AdminFilterByDate)
admin.site.register(AgendaComment, AdminFilterByDate)
admin.site.register(AgendaTask, AdminFilterByDate)
