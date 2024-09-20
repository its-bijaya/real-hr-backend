# Generated by Django 2.2.11 on 2021-06-29 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0003_dutystation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentcategory',
            name='associated_with',
            field=models.CharField(choices=[('Employee', 'Employee'), ('Organization', 'Organization'), ('Other', 'Other'), ('Both', 'Both')], db_index=True, default='Both', max_length=15),
        ),
        migrations.AlterField(
            model_name='equipmentcategory',
            name='type',
            field=models.CharField(choices=[('Fixed', 'Fixed'), ('Tangible', 'Tangible'), ('Intangible', 'Intangible'), ('Current', 'Current'), ('Financial', 'Financial')], db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='exchangerate',
            name='from_currency',
            field=models.CharField(choices=[('USD', 'USD'), ('NRS', 'NRS')], db_index=True, max_length=15),
        ),
        migrations.AlterField(
            model_name='exchangerate',
            name='to_currency',
            field=models.CharField(choices=[('USD', 'USD'), ('NRS', 'NRS')], db_index=True, max_length=15),
        ),
        migrations.AlterField(
            model_name='notificationtemplate',
            name='type',
            field=models.CharField(choices=[('Late In Email', 'LateIn Email'), ('Absent Email', 'Absent Email'), ('Overtime Email', 'Overtime EMail'), ('Leave Email', 'Leave Email')], db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='notificationtemplatecontent',
            name='status',
            field=models.CharField(db_index=True, default='Default', max_length=32),
        ),
        migrations.AlterField(
            model_name='religionandethnicity',
            name='category',
            field=models.CharField(choices=[('Religion', 'Religion'), ('Ethnicity', 'Ethnicity')], db_index=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='systememaillog',
            name='status',
            field=models.CharField(choices=[('Sent', 'Sent'), ('Failed', 'Failed')], db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='useractivity',
            name='category',
            field=models.CharField(choices=[('Task', 'Task'), ('HRIS', 'HRIS'), ('Noticeboard', 'Noticeboard'), ('Attendance', 'Attendance')], db_index=True, max_length=25),
        ),
    ]
