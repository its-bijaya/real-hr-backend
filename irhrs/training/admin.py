from django.contrib import admin
from irhrs.training.models.training_models import (
        TrainingType,
        Training,
        RecurringTrainingDate,
        UserTraining,
        UserTrainingRequest,
        Trainer,
        TrainerAttachments,
        TrainingFeedback,
        TrainingAttachments,
        TrainingAttachment,
        TrainingAttendance
        )
from irhrs.core.utils.admin.filter import (
        AdminFilterByStatus, SearchByTitle, SearchByNameAndFilterByStatus, 
        AdminFilterByDate, 
)
from rangefilter.filter import DateRangeFilter

admin.site.register(TrainingType, SearchByTitle)
admin.site.register(Training, SearchByNameAndFilterByStatus)
admin.site.register(UserTrainingRequest, AdminFilterByStatus)

class TrainerAdmin(admin.ModelAdmin):
        search_fields = ('full_name', )
        list_display = (
                'created_at', 
                'modified_at', 
        )
        list_filter = (
                ('created_at', DateRangeFilter),
        )

admin.site.register(Trainer, TrainerAdmin)
admin.site.register(RecurringTrainingDate, AdminFilterByDate)
admin.site.register(UserTraining, AdminFilterByDate)
admin.site.register(TrainerAttachments, AdminFilterByDate)
admin.site.register(TrainingFeedback, AdminFilterByDate)
admin.site.register(TrainingAttachments, AdminFilterByDate)
admin.site.register(TrainingAttachment)
admin.site.register(TrainingAttendance, AdminFilterByDate)
