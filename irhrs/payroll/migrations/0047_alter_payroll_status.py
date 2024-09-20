# Generated by Django 3.2.12 on 2022-11-08 06:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0046_remove_uservoluntaryrebate_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payroll',
            name='status',
            field=models.CharField(choices=[('Processing', 'Processing'), ('Generated', 'Generated'), ('Approval Pending', 'Approval Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Confirmed', 'Confirmed')], db_index=True, default='Generated', max_length=50),
        ),
    ]
