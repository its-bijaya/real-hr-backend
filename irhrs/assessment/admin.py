from django.contrib import admin
from irhrs.assessment.models import *

from irhrs.core.utils.admin.filter import AdminFilterByDate, SearchByTitle, AdminFilterByStatus

admin.site.register(AssessmentQuestions, AdminFilterByDate)
admin.site.register(AssessmentSet, SearchByTitle)
admin.site.register(AssessmentSection, SearchByTitle)
admin.site.register(UserAssessment, AdminFilterByStatus)
admin.site.register(QuestionResponse, AdminFilterByStatus)
