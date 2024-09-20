# Generated by Django 2.2.11 on 2022-06-03 06:34

import cuser.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def migrate_prior_approval_rule_fields(apps, schema_editor):
    LeaveRule = apps.get_model('leave', 'LeaveRule')
    PriorApprovalRule = apps.get_model('leave', 'PriorApprovalRule')

    rules = LeaveRule.objects.filter(require_prior_approval=True)

    for rule in rules:
        PriorApprovalRule.objects.create(
            prior_approval_request_for = 1,
            prior_approval = rule.prior_approval,
            prior_approval_unit = rule.prior_approval_unit,
            rule = rule
        )

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('leave', '0014_auto_20211126_1113'),
    ]

    operations = [
        migrations.CreateModel(
            name='PriorApprovalRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('prior_approval_request_for', models.IntegerField(null=True)),
                ('prior_approval', models.IntegerField(null=True)),
                ('prior_approval_unit', models.CharField(blank=True, choices=[('Days', 'Days'), ('Hours', 'Hours'), ('Minutes', 'Minutes')], max_length=20)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leave_priorapprovalrule_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leave_priorapprovalrule_modified', to=settings.AUTH_USER_MODEL)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prior_approval_rules', to='leave.LeaveRule')),
            ],
            options={
                'ordering': ('created_at', 'modified_at'),
            },
        ),
        migrations.RunPython(migrate_prior_approval_rule_fields),
        migrations.RemoveField(
            model_name='leaverule',
            name='prior_approval',
        ),
        migrations.RemoveField(
            model_name='leaverule',
            name='prior_approval_unit',
        ),
    ]
