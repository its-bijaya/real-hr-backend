from django.contrib.auth import get_user_model

from irhrs.common.models import ReligionAndEthnicity
from irhrs.organization.models import Organization, OrganizationBranch, \
    OrganizationDivision, EmploymentJobTitle, EmploymentLevel, EmploymentStatus
from irhrs.task.models.task import Task, TaskAssociation, TaskComment, \
    TaskAttachment, TaskCheckList
from irhrs.task.models.project import TaskProject
from irhrs.users.models import UserDetail

VALID_MODEL_FIELDS = dict()

VALID_MODEL_FIELDS[Task] = dict(
    valid_direct_fields=(
        'id', 'title', 'status', 'priority', 'deadline', 'approved',
        'approved_at', 'starts_at', 'start', 'finish', 'description'
    ),
    valid_related_fields=(
        'created_by',
        'project',
        'task_associations',
        'task_comments',
        'task_attachments',
        'task_checklists'
    )
)
VALID_MODEL_FIELDS[TaskAssociation] = dict(
    valid_direct_fields=(
        'id', 'association', 'score', 'remarks', 'read_only',
        'efficiency', 'ack', 'ack_remarks'
    ),
    valid_related_fields=(
        'task',
        'user',
        'core_tasks'
    )
)

VALID_MODEL_FIELDS[TaskCheckList] = dict(
    valid_direct_fields=(
        'id', 'title', 'completed_on'
    ),
    valid_related_fields=(
        'task',
        'completed_by',
    )
)

VALID_MODEL_FIELDS[TaskAttachment] = dict(
    valid_direct_fields=(
        'id', 'caption', 'attachment'),
    valid_related_fields=(
        'task',
    )
)

VALID_MODEL_FIELDS[TaskComment] = dict(
    valid_direct_fields=(
        'id', 'comment',
    ),
    valid_related_fields=(
        'task',
    )
)

VALID_MODEL_FIELDS[TaskProject] = dict(
    valid_direct_field=(
        'id', 'name', 'description'
    ),
    valid_related_fields=(
        'created_by',
        'members',
    )
)

VALID_MODEL_FIELDS[get_user_model()] = dict(
    valid_direct_fields=(
        'id', 'first_name', 'middle_name', 'last_name',
        'is_active', 'is_blocked', 'email'
    ),
    valid_related_fields=(
        'task_task_created',
        'taskassociation',
        'detail',
    )
)
VALID_MODEL_FIELDS[UserDetail] = dict(
    valid_direct_fields=(
        'code', 'gender', 'date_of_birth', 'nationality',
        'marital_status', 'marriage_anniversary',
        'extension_number', 'joined_date', 'resigned_date',
        'last_working_date', 'parting_reason',
    ),
    valid_related_fields=(
        'user', 'religion', 'ethnicity', 'organization',
        'branch', 'division', 'job_title', 'employment_level',
        'employment_status',

    )
)

VALID_MODEL_FIELDS[ReligionAndEthnicity] = dict(
    valid_direct_fields=(
        'name', 'category',
    ),
    valid_related_fields=(

    )
)

VALID_MODEL_FIELDS[Organization] = dict(
    valid_direct_fields=(
        'name', 'abbreviation', 'about', 'ownership', 'size',
        'website', 'established_on', 'email', 'registration_number',
        'vat_pan_number'
    ),
    valid_related_fields=(
        'organization_head', 'administrators', 'branches'
    )
)

VALID_MODEL_FIELDS[OrganizationBranch] = dict(
    valid_direct_fields=(
        'name', 'description', 'email', 'code',
        'mailing_address', 'is_archived'
    ),
    valid_related_fields=(
        'organization', 'branch_manager'
    )
)

VALID_MODEL_FIELDS[OrganizationDivision] = dict(
    valid_direct_fields=(
        'name', 'description', 'extension_number', 'strategies',
        'action_plans', 'email', 'is_archived'
    ),
    valid_related_fields=(
        'organization', 'head'
    )
)

VALID_MODEL_FIELDS[EmploymentJobTitle] = dict(
    valid_direct_fields=(
        'title', 'description',
    ),
    valid_related_fields=(
        'organization',
    )
)

VALID_MODEL_FIELDS[EmploymentLevel] = dict(
    valid_direct_fields=(
        'title', 'description', 'code', 'is_archived'
    ),
    valid_related_fields=(
        'organization',
    )
)

VALID_MODEL_FIELDS[EmploymentStatus] = dict(
    valid_direct_fields = (
        'title','description','is_contract','is_archived',
    ),
    valid_related_fields = (
        'organization',
    )
)
