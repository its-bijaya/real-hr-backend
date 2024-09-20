from django.contrib import admin
from .models.questionnaire import *

from irhrs.core.utils.admin.filter import SearchByTitle

# Register your models here.

admin.site.register(QuestionCategory, SearchByTitle)
admin.site.register(Question, SearchByTitle)
admin.site.register(Answer, SearchByTitle)
