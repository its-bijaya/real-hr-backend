# Generated by Django 2.2.11 on 2021-03-16 09:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20210316_1406'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='usercontactdetail',
            unique_together=set(),
        ),
    ]
