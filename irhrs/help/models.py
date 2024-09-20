from django.contrib.auth import get_user_model
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.utils.common import get_upload_path
from irhrs.core.validators import validate_image_file_extension
from .validators import validate_title, validate_invalid_chars


class HelpModule(BaseModel):
    icon_class = models.CharField(max_length=250)
    name = models.CharField(max_length=200, validators=[validate_title,
                                                        validate_invalid_chars])
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    def increase_view_count(self):
        self.views += 1
        self.save()


class HelpCategory(BaseModel):
    help_module = models.ForeignKey(HelpModule, on_delete=models.CASCADE,
                                    related_name='categories')
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class HelpQuestion(BaseModel):
    help_category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE,
                                      related_name='questions', null=True,
                                      blank=True)
    title = models.TextField()
    answer = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               related_name='child_questions', null=True,
                               blank=True)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    def increase_view_count(self):
        self.views += 1
        self.save()


# class HelpQuestionImage(BaseModel):
#     help_question = models.ForeignKey(HelpQuestion, on_delete=models.CASCADE,
#                                       related_name='images')
#     image = models.ImageField(upload_to=get_upload_path, validators=[validate_image_file_extension])

#     def __str__(self):
#         return f"{self.help_question.title}: Image Id - {self.id}"


class HelpQuestionFeedback(BaseModel):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,
                             related_name='feedback_given')
    help_question = models.ForeignKey(HelpQuestion, on_delete=models.CASCADE,
                                      related_name='feedback')
    helpful = models.BooleanField()
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.help_question.title}: Helpful - {self.helpful}"
