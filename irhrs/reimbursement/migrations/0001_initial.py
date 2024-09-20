# Generated by Django 2.2.11 on 2021-02-11 10:29

import django.contrib.postgres.fields.jsonb
import django.core.validators
from django.db import migrations, models
import irhrs.core.utils.common


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdvanceExpenseRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('advance_code', models.PositiveIntegerField(default=1, help_text='Auto generated TAARF code.', validators=[django.core.validators.MinValueValidator(1)])),
                ('reason', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('Travel', 'Travel'), ('Business', 'Business'), ('Medical', 'Medical'), ('Other', 'Other')], default='Travel', max_length=255)),
                ('description', models.TextField(blank=True, max_length=600)),
                ('remarks', models.TextField(blank=True, max_length=600)),
                ('status', models.CharField(choices=[('Requested', 'Requested'), ('Approved', 'Approved'), ('Denied', 'Denied'), ('Canceled', 'Canceled')], default='Requested', max_length=25)),
                ('total_amount', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('advance_amount', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('currency', models.CharField(choices=[('USD', 'USD'), ('NPR', 'NPR'), ('Other', 'Other')], default='NPR', max_length=6)),
                ('add_signature', models.BooleanField(default=False)),
                ('detail', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AdvanceExpenseRequestApproval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Denied', 'Denied')], max_length=25)),
                ('role', models.CharField(choices=[('Supervisor', 'Supervisor'), ('Employee', 'Employee')], max_length=25)),
                ('level', models.IntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1)])),
                ('remarks', models.TextField(max_length=600)),
                ('add_signature', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('level',),
            },
        ),
        migrations.CreateModel(
            name='AdvanceExpenseRequestDocuments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('attachment', models.FileField(upload_to=irhrs.core.utils.common.get_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'tif', 'tiff', 'jif', 'jfif', 'jp2', 'jpx', 'j2k', 'j2c', 'fpx', 'pcd', 'psd', 'rtf', 'gif', 'jpeg', 'jpg', 'png'])])),
                ('name', models.CharField(default='Unnamed', max_length=255)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AdvanceExpenseRequestHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(max_length=20)),
                ('target', models.CharField(blank=True, max_length=20)),
                ('remarks', models.TextField(blank=True, max_length=600)),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='ExpenseApprovalSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('approve_by', models.CharField(choices=[('Supervisor', 'Supervisor'), ('Employee', 'Employee')], default='Supervisor', max_length=10)),
                ('supervisor_level', models.CharField(blank=True, choices=[('All', 'All'), ('First', '1st Level'), ('Second', '2nd Level'), ('Third', '3rd Level')], max_length=6, null=True)),
                ('approval_level', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseSettlement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('reason', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('Travel', 'Travel'), ('Business', 'Business'), ('Medical', 'Medical'), ('Other', 'Other')], default='Travel', max_length=255)),
                ('description', models.TextField(blank=True, max_length=600)),
                ('remark', models.TextField(blank=True, max_length=600)),
                ('status', models.CharField(choices=[('Requested', 'Requested'), ('Approved', 'Approved'), ('Denied', 'Denied'), ('Canceled', 'Canceled')], default='Requested', max_length=25)),
                ('total_amount', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('advance_amount', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('currency', models.CharField(choices=[('USD', 'USD'), ('NPR', 'NPR'), ('Other', 'Other')], default='NPR', max_length=6)),
                ('add_signature', models.BooleanField(default=False)),
                ('detail', django.contrib.postgres.fields.jsonb.JSONField()),
                ('travel_report', models.FileField(null=True, upload_to=irhrs.core.utils.common.get_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'tif', 'tiff', 'jif', 'jfif', 'jp2', 'jpx', 'j2k', 'j2c', 'fpx', 'pcd', 'psd', 'rtf', 'gif', 'jpeg', 'jpg', 'png'])])),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReimbursementSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('advance_code', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('approve_multiple_times', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SettlementApproval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Denied', 'Denied')], max_length=25)),
                ('role', models.CharField(choices=[('Supervisor', 'Supervisor'), ('Employee', 'Employee')], max_length=25)),
                ('level', models.IntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1)])),
                ('remarks', models.TextField(max_length=600)),
                ('add_signature', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('level',),
            },
        ),
        migrations.CreateModel(
            name='SettlementDocuments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('attachment', models.FileField(upload_to=irhrs.core.utils.common.get_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'tif', 'tiff', 'jif', 'jfif', 'jp2', 'jpx', 'j2k', 'j2c', 'fpx', 'pcd', 'psd', 'rtf', 'gif', 'jpeg', 'jpg', 'png'])])),
                ('name', models.CharField(default='Unnamed', max_length=255)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SettlementHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(max_length=20)),
                ('target', models.CharField(blank=True, max_length=20)),
                ('remarks', models.TextField(blank=True, max_length=600)),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='SettlementOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('settle_with', models.CharField(choices=[('Cash', 'Cash'), ('Cheque', 'Cheque'), ('Transfer', 'Transfer'), ('Deposit', 'Deposit')], default='Cash', max_length=20)),
                ('attachment', models.FileField(upload_to=irhrs.core.utils.common.get_upload_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'tif', 'tiff', 'jif', 'jfif', 'jp2', 'jpx', 'j2k', 'j2c', 'fpx', 'pcd', 'psd', 'rtf', 'gif', 'jpeg', 'jpg', 'png'])])),
                ('remark', models.CharField(max_length=225)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SettlementOptionSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('option', models.CharField(choices=[('Cash', 'Cash'), ('Cheque', 'Cheque'), ('Transfer', 'Transfer'), ('Deposit', 'Deposit')], max_length=20)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
    ]
