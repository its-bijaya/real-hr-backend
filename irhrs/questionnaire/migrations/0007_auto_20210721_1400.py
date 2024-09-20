# Generated by Django 2.2.11 on 2021-07-21 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questionnaire', '0006_auto_20210716_1758'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='answer_choices',
            field=models.CharField(choices=[('multiple-mcq', 'Checkbox'), ('single-mcq', 'Radio Button'), ('linear-scale', 'Linear Scale'), ('short-text', 'Short Answer'), ('long-text', 'Long Answer'), ('rating-scale', 'Rating Scale'), ('date', 'Date'), ('time', 'Time'), ('duration', 'Duration'), ('date-without-year', 'Date without year'), ('date-time-without-year', 'Datetime without year'), ('file-upload', 'File Upload')], db_index=True, help_text='The types of answer choices. Eg: MCQ, Linear Scale, etc.', max_length=20),
        ),
    ]
