# Generated by Django 3.2.12 on 2022-03-07 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reimbursement', '0004_auto_20210629_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advanceexpenserequest',
            name='detail',
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name='expensesettlement',
            name='detail',
            field=models.JSONField(),
        ),
    ]
