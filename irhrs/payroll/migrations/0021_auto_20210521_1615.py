# Generated by Django 2.2.11 on 2021-05-21 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0020_auto_20210521_1421'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uservoluntaryrebate',
            name='duration_unit',
            field=models.CharField(choices=[('Yearly', 'Yearly'), ('Monthly', 'Monthly')], max_length=20),
        ),
    ]
