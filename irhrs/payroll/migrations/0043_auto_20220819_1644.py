# Generated by Django 3.2.12 on 2022-08-19 10:59

import cuser.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0028_merge_20220516_1058'),
        ('payroll', '0042_merge_20220729_1114'),
    ]

    operations = [
        migrations.AddField(
            model_name='uservoluntaryrebate',
            name='fiscal_months_amount',
            field=models.JSONField(null=True),
        ),
        migrations.CreateModel(
            name='PayslipReportSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('category', models.CharField(choices=[('Earning', 'Earning'), ('Deduction', 'Deduction')], max_length=200)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payroll_payslipreportsetting_created', to=settings.AUTH_USER_MODEL)),
                ('headings', models.ManyToManyField(related_name='payslip_particulars', to='payroll.Heading')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payroll_payslipreportsetting_modified', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payslip_report_settings', to='organization.organization')),
            ],
            options={
                'ordering': ('created_at', 'modified_at'),
            },
        ),
    ]
