# Generated by Django 2.2.11 on 2021-07-21 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appraisal', '0013_auto_20210701_1432'),
    ]

    operations = [
        migrations.AlterField(
            model_name='performanceappraisalanswertype',
            name='answer_type',
            field=models.CharField(choices=[('multiple-mcq', 'Checkbox'), ('single-mcq', 'Radio Button'), ('linear-scale', 'Linear Scale'), ('short-text', 'Short Answer'), ('long-text', 'Long Answer'), ('rating-scale', 'Rating Scale'), ('date', 'Date'), ('time', 'Time'), ('duration', 'Duration'), ('date-without-year', 'Date without year'), ('date-time-without-year', 'Datetime without year'), ('file-upload', 'File Upload')], db_index=True, default='long-text', max_length=20),
        ),
    ]
