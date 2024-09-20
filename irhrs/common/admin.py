from django.contrib import admin

from .models import *

from irhrs.core.utils.admin.filter import AdminFilterByStatus, SearchByName, SearchByTitle, AdminFilterByDate

# Commons
admin.site.register(Industry, SearchByName)
admin.site.register(DocumentCategory, SearchByTitle)
admin.site.register(Disability, AdminFilterByDate)
admin.site.register(ReligionAndEthnicity, SearchByName)
admin.site.register(HolidayCategory, SearchByName)
admin.site.register(Bank, SearchByName)
admin.site.register(EquipmentCategory, SearchByName)

# Exchange rate
admin.site.register(ExchangeRate, AdminFilterByDate)

# ID card
admin.site.register(IdCardSample, SearchByName)

# Notification
admin.site.register(NotificationTemplate, SearchByName)
admin.site.register(NotificationTemplateContent, AdminFilterByStatus)

# Skill
admin.site.register(Skill, SearchByName)

# SMTP server
admin.site.register(SMTPServer)
admin.site.register(SystemEmailLog, AdminFilterByStatus)

# User activity
admin.site.register(UserActivity, AdminFilterByDate)
