# Generated by Django 3.2.12 on 2022-11-11 09:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reimbursement', '0009_merge_20220906_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='reimbursementsetting',
            name='travel_report_mandatory',
            field=models.BooleanField(default=False),
        ),
    ]
