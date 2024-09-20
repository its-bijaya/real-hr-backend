from django.contrib import admin

from .models import Task, Activity, Project, WorkLog, WorkLogAction
from .models.settings import UserActivityProject
from .models.task import (
    TaskAssociation, RecurringTaskDate, TaskReminder,
    TaskProject, TaskAttachment,
    TaskComment, TaskCheckList, TaskActivity,
    TaskVerificationScore
)
from .models.ra_and_core_tasks import *

from irhrs.core.utils.admin.filter import (
    AdminFilterByStatus, SearchByName, SearchByTitle,
    SearchByTitleAndFilterByStatus, AdminFilterByDate
)

# Project
admin.site.register(TaskProject, SearchByName)

# RA and core tasks
admin.site.unregister(ResultArea)
admin.site.register(ResultArea, SearchByTitle)
admin.site.unregister(CoreTask)
admin.site.register(CoreTask, SearchByTitle)
admin.site.unregister(UserResultArea)
admin.site.register(UserResultArea, AdminFilterByDate)

# Tasks
admin.site.register(Task, SearchByTitleAndFilterByStatus)
admin.site.register(TaskReminder, AdminFilterByStatus)
admin.site.register(TaskCheckList, SearchByTitle)
admin.site.register(TaskAssociation, AdminFilterByDate)
admin.site.register(RecurringTaskDate, AdminFilterByDate)
admin.site.register(TaskAttachment, AdminFilterByDate)
admin.site.register(TaskComment, AdminFilterByDate)
admin.site.register(TaskActivity, AdminFilterByDate)
admin.site.register(TaskVerificationScore, AdminFilterByDate)

# Setting
admin.site.register(Activity, SearchByName)
admin.site.register(Project, SearchByName)
admin.site.register(UserActivityProject, AdminFilterByDate)

# WorkLog
admin.site.register(WorkLog, AdminFilterByDate)
admin.site.register(WorkLogAction, AdminFilterByDate)
