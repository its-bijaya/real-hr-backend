# Generated by Django 2.2.11 on 2021-02-11 10:29

import cuser.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('task', '0001_initial'),
        ('event', '0001_initial'),
        ('organization', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='meetingnotification',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingnotification_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingnotification',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='event.Meeting'),
        ),
        migrations.AddField(
            model_name='meetingnotification',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingnotification_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingdocument',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingdocument_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingdocument',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='event.Meeting'),
        ),
        migrations.AddField(
            model_name='meetingdocument',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingdocument_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingattendance',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingattendance_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingattendance',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meeting_attendances', to='event.Meeting'),
        ),
        migrations.AddField(
            model_name='meetingattendance',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='present_members', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingattendance',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingattendance_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingagenda',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingagenda_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingagenda',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meeting_agendas', to='event.Meeting'),
        ),
        migrations.AddField(
            model_name='meetingagenda',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingagenda_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingacknowledgerecord',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingacknowledgerecord_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingacknowledgerecord',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acknowledge_records', to='event.Meeting'),
        ),
        migrations.AddField(
            model_name='meetingacknowledgerecord',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acknowledge_meeting', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meetingacknowledgerecord',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meetingacknowledgerecord_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meeting',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meeting_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meeting',
            name='event',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='event.Event'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='minuter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='minuters', to='event.EventMembers'),
        ),
        migrations.AddField(
            model_name='meeting',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_meeting_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='meeting',
            name='time_keeper',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='time_keepers', to='event.EventMembers'),
        ),
        migrations.AddField(
            model_name='eventmembers',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_eventmembers_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='eventmembers',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_members', to='event.Event'),
        ),
        migrations.AddField(
            model_name='eventmembers',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_eventmembers_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='eventmembers',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_event_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='generated_from',
            field=models.ForeignKey(blank=True, db_column='parent', help_text='Parent events for the recurring events', null=True, on_delete=django.db.models.deletion.CASCADE, to='event.Event'),
        ),
        migrations.AddField(
            model_name='event',
            name='members',
            field=models.ManyToManyField(blank=True, related_name='_event_members_+', through='event.EventMembers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_event_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='event',
            name='room',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event', to='organization.MeetingRoomStatus'),
        ),
        migrations.AddField(
            model_name='agendatask',
            name='agenda',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agenda_tasks', to='event.MeetingAgenda'),
        ),
        migrations.AddField(
            model_name='agendatask',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_agendatask_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='agendatask',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_agendatask_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='agendatask',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agenda_tasks', to='task.Task'),
        ),
        migrations.AddField(
            model_name='agendacomment',
            name='agenda',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='event.MeetingAgenda'),
        ),
        migrations.AddField(
            model_name='agendacomment',
            name='commented_by',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='agenda_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='agendacomment',
            name='created_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_agendacomment_created', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='agendacomment',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_agendacomment_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='meetingattendance',
            unique_together={('member', 'meeting')},
        ),
        migrations.AlterUniqueTogether(
            name='eventmembers',
            unique_together={('event', 'user')},
        ),
    ]
