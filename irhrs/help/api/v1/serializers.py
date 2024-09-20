from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from irhrs.help.models import (HelpModule,
                               HelpCategory,
                               HelpQuestion,
                               #HelpQuestionImage,
                               HelpQuestionFeedback)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = '__all__'


class HelpQuestionFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpQuestionFeedback
        fields = ('id', 'help_question', 'helpful', 'remarks')

    def create(self, validated_data):
        validated_data.update({'user': self.context.get('request').user})
        return super().create(validated_data)


# class HelpQuestionImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = HelpQuestionImage
#         fields = ('id', 'help_question', 'image')


class HelpChildQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpQuestion
        fields = ('id', 'title', 'answer')


class HelpCategoryThinSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpCategory
        fields = ('id', 'title', 'help_module')


class HelpQuestionSerializer(serializers.ModelSerializer):
    # images = HelpQuestionImageSerializer(many=True,
    #                                      read_only=True,
    #                                      required=False)
    images = serializers.SerializerMethodField()
    child_questions = HelpChildQuestionSerializer(many=True,
                                                  read_only=True,
                                                  required=False)

    help_category = HelpCategoryThinSerializer()

    class Meta:
        model = HelpQuestion
        fields = ('id', 'help_category', 'title', 'answer',
                  'parent', 'views', 'images', 'child_questions')

    def get_images(self, obj):
        return []


class HelpCategorySerializer(serializers.ModelSerializer):
    questions = SerializerMethodField()

    class Meta:
        model = HelpCategory
        fields = ('id', 'title', 'help_module', 'questions')

    def get_questions(self, obj):
        qs = obj.questions.filter(parent__isnull=True)[:5]
        serializer = HelpQuestionSerializer(qs, many=True)
        return serializer.data


class HelpModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpModule
        fields = ('id', 'icon_class', 'name', 'views')
