# Generated by Django 3.2.12 on 2022-07-29 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0017_merge_0015_auto_20220307_1143_0016_auto_20220718_1152'),
    ]

    operations = [
        migrations.AddField(
            model_name='leaverule',
            name='prior_approval',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='leaverule',
            name='prior_approval_unit',
            field=models.CharField(blank=True, choices=[('Days', 'Days'), ('Hours', 'Hours'), ('Minutes', 'Minutes')], max_length=20),
        ),
    ]
