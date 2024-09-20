# Generated by Django 2.2.11 on 2021-02-11 10:29

from django.db import migrations, models
import irhrs.core.validators
import irhrs.noticeboard.utils.file_path
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CommentLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('liked', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='CommentReply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('reply', models.TextField(max_length=1000)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HRNoticeAcknowledgement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('acknowledged', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NoticeBoardSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('allow_to_post', models.BooleanField(default=True)),
                ('need_approval', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('post_content', models.TextField(blank=True, max_length=10000)),
                ('category', models.CharField(choices=[('HR Notice', 'HR Notice'), ('Division Notice', 'Division Notice'), ('Normal Post', 'Normal Post'), ('Auto Generated', 'Auto Generated'), ('Organization Notice', 'Organization Notice')], default='Normal Post', max_length=50)),
                ('disable_comment', models.BooleanField(default=False)),
                ('pinned', models.BooleanField(default=False)),
                ('pinned_on', models.DateTimeField(null=True)),
                ('visible_until', models.DateTimeField(null=True)),
                ('scheduled_for', models.DateTimeField(null=True, validators=[irhrs.core.validators.validate_future_datetime])),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Denied', 'Denied')], default='Approved', max_length=50)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PostAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('image', sorl.thumbnail.fields.ImageField(upload_to=irhrs.noticeboard.utils.file_path.get_post_attachment_path, validators=[irhrs.core.validators.validate_image_file_extension])),
                ('caption', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'ordering': ('created_at',),
            },
        ),
        migrations.CreateModel(
            name='PostComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('content', models.TextField(blank=True, max_length=1000)),
                ('image', models.ImageField(blank=True, null=True, upload_to=irhrs.noticeboard.utils.file_path.get_comment_attachment_path, validators=[irhrs.core.validators.validate_image_file_extension])),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('liked', models.BooleanField(default=True)),
            ],
        ),
    ]
