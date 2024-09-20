# Generated by Django 2.2.11 on 2021-07-12 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0021_auto_20210709_1423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worklog',
            name='core_task',
        ),
        migrations.AddField(
            model_name='worklog',
            name='core_task',
            field=models.ManyToManyField(related_name='daily_tasks', to='task.CoreTask'),
        ),
    ]
