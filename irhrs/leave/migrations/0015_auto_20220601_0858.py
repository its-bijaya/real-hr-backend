# Generated by Django 2.2.11 on 2022-06-01 03:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leave', '0014_auto_20211126_1113'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compensatoryleave',
            name='rule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compensatory_rules', to='leave.LeaveRule'),
        ),
    ]
