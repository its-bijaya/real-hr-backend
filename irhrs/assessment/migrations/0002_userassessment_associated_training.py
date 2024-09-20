# Generated by Django 2.2.11 on 2021-02-11 10:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('training', '0001_initial'),
        ('assessment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userassessment',
            name='associated_training',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='training.Training'),
        ),
    ]
