# Generated by Django 2.2.11 on 2022-07-27 09:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0027_auto_20220419_1125'),
        ('payroll', '0040_rebatesetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='uservoluntaryrebate',
            name='rebate',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='voluntary_rebates', to='payroll.RebateSetting'),
        ),
        migrations.AlterField(
            model_name='rebatesetting',
            name='amount',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='rebatesetting',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rebate_settings', to='organization.Organization'),
        ),
        migrations.AlterField(
            model_name='uservoluntaryrebate',
            name='type',
            field=models.CharField(blank=True, choices=[('Health Insurance', 'Health Insurance'), ('Life Insurance', 'Life Insurance'), ('Donation', 'Donation'), ('CIT', 'CIT')], max_length=120, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='rebatesetting',
            unique_together={('title', 'organization')},
        ),
        migrations.RemoveField(
            model_name='rebatesetting',
            name='deleted_at',
        ),
    ]
