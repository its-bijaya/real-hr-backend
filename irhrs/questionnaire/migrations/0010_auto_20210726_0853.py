# Generated by Django 2.2.11 on 2021-07-26 03:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0009_auto_20210725_1444'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='answer_choices',
            field=models.CharField(choices=[('multiple-mcq', 'Checkbox'), ('single-mcq', 'Radio Button'), ('linear-scale', 'Linear Scale'), ('short-text', 'Short Answer'), ('long-text', 'Long Answer'), ('rating-scale', 'Rating Scale'), ('date', 'Date'), ('time', 'Time'), ('date-time', 'Date time'), ('duration', 'Duration'), ('date-without-year', 'Date without year'), ('date-time-without-year', 'Datetime without year'), ('file-upload', 'File Upload')], db_index=True, help_text='The types of answer choices. Eg: MCQ, Linear Scale, etc.', max_length=60),
        ),
    ]
