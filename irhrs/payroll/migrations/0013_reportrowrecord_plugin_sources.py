# Generated by Django 2.2.11 on 2021-05-03 19:05

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0012_merge_20210503_1553'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportrowrecord',
            name='plugin_sources',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=list),
        ),
    ]
