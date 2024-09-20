from django.contrib import admin

from .models import HelpCategory, HelpQuestion, HelpModule, HelpQuestionFeedback

admin.site.register(HelpModule)
admin.site.register(HelpCategory)
admin.site.register(HelpQuestion)
admin.site.register(HelpQuestionFeedback)
