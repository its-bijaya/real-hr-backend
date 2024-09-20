# Generated by Django 2.2.11 on 2022-04-06 04:13

from django.db import migrations, models
import django.db.models.deletion




class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0007_location_country_ref'),
        ('organization', '0025_auto_20220323_1516'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organizationaddress',
            name='country',
        ),
        migrations.RemoveField(
            model_name='organizationbranch',
            name='country',
        ),
        migrations.AddField(
            model_name='organizationaddress',
            name='country_ref',
            field=models.ForeignKey(blank=True, default=603, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='recruitment.Country'),
        ),
        migrations.AddField(
            model_name='organizationaddress',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='recruitment.District'),
        ),
        migrations.AddField(
            model_name='organizationaddress',
            name='province',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='recruitment.Province'),
        ),
        migrations.AddField(
            model_name='organizationbranch',
            name='district',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='recruitment.District'),
        ),
        migrations.AlterField(
            model_name='organizationbranch',
            name='country_ref',
            field=models.ForeignKey(blank=True, default=603, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='recruitment.Country'),
        ),
        migrations.AlterField(
            model_name='organizationbranch',
            name='province',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='recruitment.Province'),
        ),
    ]
