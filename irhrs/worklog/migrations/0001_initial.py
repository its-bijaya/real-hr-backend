# Generated by Django 2.2.11 on 2021-02-11 10:29

import cuser.fields
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import irhrs.worklog.models.worklog
import irhrs.worklog.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField()),
                ('description', models.TextField()),
                ('score', models.PositiveSmallIntegerField(blank=True, null=True, validators=[irhrs.worklog.models.worklog.validate_score])),
                ('score_remarks', models.TextField(blank=True, null=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='worklog_worklog_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='worklog_worklog_modified', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkLogComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('comment', models.TextField(max_length=1000)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='worklog_worklogcomment_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='worklog_worklogcomment_modified', to=settings.AUTH_USER_MODEL)),
                ('work_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='worklog_comments', to='worklog.WorkLog')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WorkLogAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('attachment', models.FileField(upload_to=irhrs.worklog.utils.get_work_log_attachment_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'tif', 'tiff', 'jif', 'jfif', 'jp2', 'jpx', 'j2k', 'j2c', 'fpx', 'pcd', 'psd', 'rtf', 'gif', 'jpeg', 'jpg', 'png'])])),
                ('description', models.TextField()),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='worklog_worklogattachment_created', to=settings.AUTH_USER_MODEL)),
                ('log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='worklog_attachments', to='worklog.WorkLog')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='worklog_worklogattachment_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
    ]
