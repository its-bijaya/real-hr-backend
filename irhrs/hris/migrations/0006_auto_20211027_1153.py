# Generated by Django 2.2.11 on 2021-10-27 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hris', '0005_merge_20210510_2021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lettertemplate',
            name='type',
            field=models.CharField(choices=[('offer', 'Offer Letter'), ('custom', 'Custom'), ('on', 'On Boarding'), ('off', 'Off Boarding'), ('change', 'Change Type')], max_length=10),
        ),
    ]
