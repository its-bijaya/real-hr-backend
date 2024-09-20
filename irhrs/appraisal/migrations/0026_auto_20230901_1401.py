# Generated by Django 3.2.12 on 2023-09-01 08:16

import cuser.fields
from django.conf import settings
import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0026_alter_taskverificationscore_ack'),
        ('users', '0032_alter_useremailunsubscribe_email_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appraisal', '0025_auto_20230620_1757'),
    ]

    operations = [
        migrations.CreateModel(
            name='KAARAppraiserConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('appraiser_type', models.CharField(choices=[('Self Appraisal', 'Self Appraisal'), ('Subordinate Appraisal', 'Subordinate Appraisal'), ('Peer To Peer Feedback', 'Peer To Peer Feedback'), ('Supervisor Appraisal', 'Supervisor Appraisal'), ('Reviewer Evaluation', 'Reviewer Evaluation')], db_index=True, default='Self Appraisal', max_length=32)),
                ('question_status', models.CharField(choices=[('not_generated', 'Not Generated'), ('generated', 'Generated'), ('Received', 'Received'), ('Saved', 'Saved'), ('Submitted', 'Submitted')], default='not_generated', max_length=15)),
                ('total_score', models.JSONField(null=True)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('deadline', models.DateTimeField(blank=True, null=True)),
                ('appraiser', models.ForeignKey(help_text='Person who gives review for appraisee', on_delete=django.db.models.deletion.CASCADE, related_name='appraiser_configs', to=settings.AUTH_USER_MODEL)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarappraiserconfig_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KAARQuestionSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(blank=True, max_length=1000)),
                ('is_archived', models.BooleanField(default=False)),
                ('question_type', models.CharField(choices=[('ksa', 'KSA'), ('kra', 'KRA'), ('kpi', 'KPI'), ('PA Question Set', 'PA Question Set')], max_length=15)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarquestionset_created', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KPIQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('description', models.TextField(blank=True)),
                ('is_mandatory', models.BooleanField(default=False)),
                ('remarks_required', models.BooleanField(default=False)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kpiquestion_created', to=settings.AUTH_USER_MODEL)),
                ('extended_individual_kpi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kpi_questions', to='appraisal.extendedindividualkpi')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kpiquestion_modified', to=settings.AUTH_USER_MODEL)),
                ('question_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kpi_questions', to='appraisal.kaarquestionset')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KRAQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('description', models.TextField(blank=True)),
                ('is_mandatory', models.BooleanField(default=False)),
                ('remarks_required', models.BooleanField(default=False)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kraquestion_created', to=settings.AUTH_USER_MODEL)),
                ('kra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kra_questions', to='task.userresultarea')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kraquestion_modified', to=settings.AUTH_USER_MODEL)),
                ('question_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kra_questions', to='appraisal.kaarquestionset')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KSAOQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('description', models.TextField(blank=True)),
                ('is_mandatory', models.BooleanField(default=False)),
                ('remarks_required', models.BooleanField(default=False)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_ksaoquestion_created', to=settings.AUTH_USER_MODEL)),
                ('ksao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ksao_questions', to='users.userksao')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_ksaoquestion_modified', to=settings.AUTH_USER_MODEL)),
                ('question_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ksao_questions', to='appraisal.kaarquestionset')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='performanceappraisalformdesign',
            name='caption_for_kpi',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='performanceappraisalformdesign',
            name='include_kpi',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='performanceappraisalyear',
            name='performance_appraisal_type',
            field=models.CharField(choices=[('Three Sixty Performance Appraisal', 'Three Sixty Performance Appraisal'), ('Key Achievements And Rating', 'Key Achievements And Rating')], default='Three Sixty Performance Appraisal', max_length=40),
        ),
        migrations.AlterField(
            model_name='appraisal',
            name='appraisal_type',
            field=models.CharField(choices=[('Self Appraisal', 'Self Appraisal'), ('Subordinate Appraisal', 'Subordinate Appraisal'), ('Peer To Peer Feedback', 'Peer To Peer Feedback'), ('Supervisor Appraisal', 'Supervisor Appraisal'), ('Reviewer Evaluation', 'Reviewer Evaluation')], db_index=True, default='Self Appraisal', max_length=25),
        ),
        migrations.AlterField(
            model_name='exceptionalappraiseefiltersetting',
            name='appraisal_type',
            field=models.CharField(choices=[('Self Appraisal', 'Self Appraisal'), ('Subordinate Appraisal', 'Subordinate Appraisal'), ('Peer To Peer Feedback', 'Peer To Peer Feedback'), ('Supervisor Appraisal', 'Supervisor Appraisal'), ('Reviewer Evaluation', 'Reviewer Evaluation')], db_index=True, default='Self Appraisal', max_length=24),
        ),
        migrations.AlterField(
            model_name='formreviewsetting',
            name='viewable_appraisal_submitted_form_type',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('Self Appraisal', 'Self Appraisal'), ('Subordinate Appraisal', 'Subordinate Appraisal'), ('Peer To Peer Feedback', 'Peer To Peer Feedback'), ('Supervisor Appraisal', 'Supervisor Appraisal'), ('Reviewer Evaluation', 'Reviewer Evaluation')], db_index=True, default='Self Appraisal', max_length=25), size=4),
        ),
        migrations.AlterField(
            model_name='performanceappraisalanswertype',
            name='question_type',
            field=models.CharField(choices=[('ksa', 'KSA'), ('kra', 'KRA'), ('kpi', 'KPI')], db_index=True, default='kra', max_length=3),
        ),
        migrations.AlterField(
            model_name='performanceappraisalformdesign',
            name='appraisal_type',
            field=models.CharField(choices=[('Self Appraisal', 'Self Appraisal'), ('Subordinate Appraisal', 'Subordinate Appraisal'), ('Peer To Peer Feedback', 'Peer To Peer Feedback'), ('Supervisor Appraisal', 'Supervisor Appraisal'), ('Reviewer Evaluation', 'Reviewer Evaluation')], db_index=True, default='Self Appraisal', max_length=32),
        ),
        migrations.AlterField(
            model_name='performanceappraisalformdesign',
            name='generic_question_set',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='form_designs', to='appraisal.performanceappraisalquestionset'),
        ),
        migrations.AlterField(
            model_name='subperformanceappraisalslotmode',
            name='appraisal_type',
            field=models.CharField(choices=[('Self Appraisal', 'Self Appraisal'), ('Subordinate Appraisal', 'Subordinate Appraisal'), ('Peer To Peer Feedback', 'Peer To Peer Feedback'), ('Supervisor Appraisal', 'Supervisor Appraisal'), ('Reviewer Evaluation', 'Reviewer Evaluation')], db_index=True, default='Self Appraisal', max_length=125),
        ),
        migrations.CreateModel(
            name='SupervisorEvaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('comment', models.TextField(blank=True)),
                ('remarks', models.TextField(blank=True)),
                ('set_default_rating', models.BooleanField(default=True)),
                ('appraiser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='supervisor_evaluation', to='appraisal.kaarappraiserconfig')),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_supervisorevaluation_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_supervisorevaluation_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScoreAndScalingConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=100)),
                ('scale_type', models.CharField(choices=[('default', 'default'), ('grade', 'grade'), ('range', 'range')], default='default', max_length=20)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_scoreandscalingconfig_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_scoreandscalingconfig_modified', to=settings.AUTH_USER_MODEL)),
                ('sub_performance_appraisal_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='score_and_scaling_configs', to='appraisal.subperformanceappraisalslot')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReviewerEvaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('comment', models.TextField(blank=True)),
                ('remarks', models.TextField(blank=True)),
                ('agree_with_appraiser', models.BooleanField(default=False)),
                ('appraiser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='reviewer_evaluation', to='appraisal.kaarappraiserconfig')),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_reviewerevaluation_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_reviewerevaluation_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RangeScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('start_range', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('end_range', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_rangescore_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_rangescore_modified', to=settings.AUTH_USER_MODEL)),
                ('score_config', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='range_score', to='appraisal.scoreandscalingconfig')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PerformanceAppraisalQuestionScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('data', models.JSONField()),
                ('appraiser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pa_question_scores', to='appraisal.kaarappraiserconfig')),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_performanceappraisalquestionscore_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_performanceappraisalquestionscore_modified', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_scores', to='appraisal.performanceappraisalquestion')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KSAOQuestionScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('score', models.FloatField(blank=True, null=True)),
                ('grade_score', models.CharField(blank=True, max_length=255, null=True)),
                ('remarks', models.CharField(blank=True, max_length=225, null=True)),
                ('appraiser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ksao_scores', to='appraisal.kaarappraiserconfig')),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_ksaoquestionscore_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_ksaoquestionscore_modified', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ksao_scores', to='appraisal.ksaoquestion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KRAQuestionScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('score', models.FloatField(blank=True, null=True)),
                ('grade_score', models.CharField(blank=True, max_length=255, null=True)),
                ('remarks', models.CharField(blank=True, max_length=225, null=True)),
                ('appraiser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kra_scores', to='appraisal.kaarappraiserconfig')),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kraquestionscore_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kraquestionscore_modified', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kra_scores', to='appraisal.kraquestion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KPIQuestionScore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('score', models.FloatField(blank=True, null=True)),
                ('grade_score', models.CharField(blank=True, max_length=255, null=True)),
                ('remarks', models.CharField(blank=True, max_length=225, null=True)),
                ('key_achievements', models.TextField(blank=True, null=True)),
                ('appraiser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kpi_scores', to='appraisal.kaarappraiserconfig')),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kpiquestionscore_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kpiquestionscore_modified', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kpi_scores', to='appraisal.kpiquestion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KeyAchievementAndRatingAppraisal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('total_score', models.JSONField(null=True)),
                ('overall_rating', models.JSONField(null=True)),
                ('status', models.CharField(choices=[('Idle', 'Idle'), ('Active', 'Active'), ('Completed', 'Completed')], default='Idle', max_length=20)),
                ('display_to_appraisee', models.BooleanField(default=False)),
                ('is_appraisee_satisfied', models.BooleanField(blank=True, null=True)),
                ('appraisee', models.ForeignKey(help_text='Person for whom performance appraisal is being conducted', on_delete=django.db.models.deletion.CASCADE, related_name='as_kaar_appraisees', to=settings.AUTH_USER_MODEL)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_keyachievementandratingappraisal_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_keyachievementandratingappraisal_modified', to=settings.AUTH_USER_MODEL)),
                ('resend', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='kaar_appraisals', to='appraisal.resendpaform')),
                ('sub_performance_appraisal_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kaar_appraisals', to='appraisal.subperformanceappraisalslot')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='KAARScaleAndScoreSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarscaleandscoresetting_created', to=settings.AUTH_USER_MODEL)),
                ('kpi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kpi_score_setting', to='appraisal.scoreandscalingconfig')),
                ('ksao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kaso_score_setting', to='appraisal.scoreandscalingconfig')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarscaleandscoresetting_modified', to=settings.AUTH_USER_MODEL)),
                ('question_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_set_score_setting', to='appraisal.scoreandscalingconfig')),
                ('sub_performance_appraisal_slot', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='kaar_score_setting', to='appraisal.subperformanceappraisalslot')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='kaarquestionset',
            name='kaar_appraisal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_set', to='appraisal.keyachievementandratingappraisal'),
        ),
        migrations.AddField(
            model_name='kaarquestionset',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarquestionset_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='KAARFormDesign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('instruction_for_evaluator', models.CharField(blank=True, max_length=10000)),
                ('include_kra', models.BooleanField(default=False)),
                ('caption_for_kra', models.CharField(blank=True, max_length=255)),
                ('include_ksa', models.BooleanField(default=False)),
                ('caption_for_ksa', models.CharField(blank=True, max_length=255)),
                ('include_kpi', models.BooleanField(default=False)),
                ('caption_for_kpi', models.CharField(blank=True, max_length=255)),
                ('add_feedback', models.BooleanField(default=False)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarformdesign_created', to=settings.AUTH_USER_MODEL)),
                ('generic_question_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kaar_form_designs', to='appraisal.performanceappraisalquestionset')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarformdesign_modified', to=settings.AUTH_USER_MODEL)),
                ('sub_performance_appraisal_slot', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='kaar_form_design', to='appraisal.subperformanceappraisalslot')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='kaarappraiserconfig',
            name='kaar_appraisal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appraiser_configs', to='appraisal.keyachievementandratingappraisal'),
        ),
        migrations.AddField(
            model_name='kaarappraiserconfig',
            name='modified_by',
            field=cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaarappraiserconfig_modified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='KAARAnswerType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('question_type', models.CharField(choices=[('ksa', 'KSA'), ('kra', 'KRA'), ('kpi', 'KPI')], db_index=True, default='kra', max_length=3)),
                ('answer_type', models.CharField(choices=[('multiple-mcq', 'Checkbox'), ('single-mcq', 'Radio Button'), ('linear-scale', 'Linear Scale'), ('short-text', 'Short Answer'), ('long-text', 'Long Answer'), ('rating-scale', 'Rating Scale'), ('date', 'Date'), ('time', 'Time'), ('date-time', 'Date time'), ('duration', 'Duration'), ('date-without-year', 'Date without year'), ('date-time-without-year', 'Datetime without year'), ('file-upload', 'File Upload'), ('multiple-choice-grid', 'Multiple Choice Grid'), ('checkbox-grid', 'Checkbox grid')], db_index=True, default='long-text', max_length=22)),
                ('description', models.CharField(blank=True, max_length=600)),
                ('is_mandatory', models.BooleanField(default=True)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaaranswertype_created', to=settings.AUTH_USER_MODEL)),
                ('form_design', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kaar_answer_types', to='appraisal.kaarformdesign')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_kaaranswertype_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GradeAndDefaultScaling',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('score', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_gradeanddefaultscaling_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_gradeanddefaultscaling_modified', to=settings.AUTH_USER_MODEL)),
                ('score_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grade_and_default_scales', to='appraisal.scoreandscalingconfig')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GenericQuestionSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_genericquestionset_created', to=settings.AUTH_USER_MODEL)),
                ('generic_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generic_questions', to='appraisal.performanceappraisalquestion')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_genericquestionset_modified', to=settings.AUTH_USER_MODEL)),
                ('question_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generic_questions', to='appraisal.kaarquestionset')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DefaultScoreSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('question_type', models.CharField(choices=[('ksa', 'KSA'), ('kra', 'KRA'), ('kpi', 'KPI'), ('PA Question Set', 'PA Question Set')], max_length=20)),
                ('score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('grade_score', models.CharField(blank=True, max_length=255, null=True)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_defaultscoresetting_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_defaultscoresetting_modified', to=settings.AUTH_USER_MODEL)),
                ('sub_performance_appraisal_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='default_scores', to='appraisal.subperformanceappraisalslot')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AnnualRatingOnCompetencies',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('final_score', models.CharField(max_length=255)),
                ('created_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_annualratingoncompetencies_created', to=settings.AUTH_USER_MODEL)),
                ('kaar_appraisal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annual_rating', to='appraisal.keyachievementandratingappraisal')),
                ('modified_by', cuser.fields.CurrentUserField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='appraisal_annualratingoncompetencies_modified', to=settings.AUTH_USER_MODEL)),
                ('question_set', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='annual_rating', to='appraisal.kaarquestionset')),
            ],
            options={
                'ordering': ('-created_at', '-modified_at'),
                'abstract': False,
            },
        ),
    ]
