# Generated by Django 3.2.12 on 2023-01-31 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0020_auto_20220307_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='credithourrequest',
            name='credit_hour_status',
            field=models.CharField(choices=[('Not Added', 'Not Added'), ('Added', 'Added')], default='Not Added', max_length=30),
        ),
    ]
