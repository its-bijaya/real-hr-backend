# Generated by Django 2.2.11 on 2021-04-29 04:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris', '0002_auto_20210211_1614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='preemployment',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('hold', 'Hold'), ('stopped', 'Stopped'), ('completed', 'Completed'), ('letters-generated', 'Letters Generated'), ('pre-active', 'Pre Task Active'), ('pre-completed', 'Pre Task Completed'), ('post-active', 'Post Task Active'), ('post-completed', 'Post Task Completed'), ('employee-added', 'Employee Added'), ('supervisor-added', 'Supervisor Added'), ('equipments-assigned', 'Equipments Assigned')], default='active', max_length=20),
        ),
    ]
