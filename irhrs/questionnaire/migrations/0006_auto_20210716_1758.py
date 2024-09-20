# Generated by Django 2.2.11 on 2021-07-16 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0005_auto_20210629_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='question_type',
            field=models.CharField(choices=[('assessment', 'Assessment'), ('forms', 'forms'), ('performance_appraisal', 'Performance Appraisal'), ('interview_evaluation', 'Interview'), ('feedback', 'Feedback'), ('vacancy', 'Vacancy Question'), ('reference_check', 'Reference Check'), ('exit_interview', 'Exit Interview'), ('pre_screening', 'Pre Screening'), ('post_screening', 'Post Screening'), ('pre_screening_interview', 'Pre Screening Interview')], db_index=True, help_text='Question Type. Eg: Assessment, PA, Feedback, Interview, etc.', max_length=25),
        ),
        migrations.AlterField(
            model_name='questioncategory',
            name='category',
            field=models.CharField(choices=[('assessment', 'Assessment'), ('forms', 'forms'), ('performance_appraisal', 'Performance Appraisal'), ('interview_evaluation', 'Interview'), ('feedback', 'Feedback'), ('vacancy', 'Vacancy Question'), ('reference_check', 'Reference Check'), ('exit_interview', 'Exit Interview'), ('pre_screening', 'Pre Screening'), ('post_screening', 'Post Screening'), ('pre_screening_interview', 'Pre Screening Interview')], db_index=True, max_length=25),
        ),
    ]
