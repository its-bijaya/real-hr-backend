# Generated by Django 2.2.11 on 2022-04-19 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0026_auto_20220406_0958'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationaddress',
            name='postal_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='organizationbranch',
            name='postal_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
