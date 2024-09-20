ONSITE = 'onsite'
OFFSITE = 'offsite'

TRAINING_NATURE = (
    (ONSITE, 'OnSite'),
    (OFFSITE, 'OffSite'),
)

REQUEST = 'request'
ASSESSMENT = 'assessment'
PERFORMANCE_APPRAISAL = 'performance-appraisal'
TASK_EFFICIENCY = 'task-efficiency'
OTHERS = 'others'

TRAINING_NEED_CHOICES = (
    (REQUEST, 'User Requested'),
    (ASSESSMENT, 'Assessment'),
    (PERFORMANCE_APPRAISAL, 'Performance Appraisal'),
    (TASK_EFFICIENCY, 'Task Efficiency'),
    (OTHERS, 'Others'),
)

REQUESTED = 'requested'
APPROVED = 'approved'
DECLINED = 'declined'
EXPIRED = 'expired'
STATUS_CHOICES = (
    (REQUESTED, 'Requested'),
    (APPROVED, 'Approved'),
    (DECLINED, 'Declined'),
    (EXPIRED, 'Expired'),
)

PENDING = 'pending'
IN_PROGRESS = 'in_progress'
COMPLETED = 'completed'
CANCELLED = 'cancelled'

TRAINING_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (IN_PROGRESS, 'In Progress'),
    (COMPLETED, 'Completed'),
    (CANCELLED, 'Cancelled'),
)

PUBLIC = 'public'
PRIVATE = 'private'
TRAINING_VISIBILITY_CHOICES = (
    (PUBLIC, 'Public'),
    (PRIVATE, 'Private')
)

MEMBER = 'member'
TRAINER = 'trainer'

TRAINING_MEMBER_POSITION = (
    (MEMBER, 'Member'),
    (TRAINER, 'Trainer')
)
