# Generated by Django 2.2.11 on 2021-05-21 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0019_uservoluntaryrebate_uservoluntaryrebateaction_uservoluntaryrebatedocument'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uservoluntaryrebate',
            name='is_deleted',
        ),
        migrations.AddField(
            model_name='uservoluntaryrebate',
            name='title',
            field=models.CharField(default='Default title', max_length=120),
            preserve_default=False,
        ),
    ]
