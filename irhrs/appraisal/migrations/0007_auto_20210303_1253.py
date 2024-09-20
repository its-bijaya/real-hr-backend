# Generated by Django 2.2.11 on 2021-03-03 07:08

from django.db import migrations, models
import irhrs.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('appraisal', '0006_appraisal_total_score'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appraisal',
            name='final_score',
            field=models.FloatField(blank=True, null=True, validators=[irhrs.core.validators.MinMaxValueValidator(0, 100)]),
        ),
    ]
