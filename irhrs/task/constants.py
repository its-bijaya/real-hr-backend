MINOR = 'MINOR'
MAJOR = 'MAJOR'
CRITICAL = 'CRITICAL'

TASK_PRIORITIES = [
    (MINOR, 'MINOR'),
    (MAJOR, 'MAJOR'),
    (CRITICAL, 'CRITICAL'),
]
PENDING = 1
IN_PROGRESS = 2
ON_HOLD = 3
COMPLETED = 4
CLOSED = 5

TASK_STATUSES_CHOICES = [
    (PENDING, 'PENDING'),
    (IN_PROGRESS, 'IN PROGRESS'),
    (COMPLETED, 'COMPLETED'),
    (CLOSED, 'CLOSED'),
    (ON_HOLD, 'ON HOLD')
]
RESPONSIBLE_PERSON, OBSERVER = 'R', 'O'
INVOLVEMENT_CHOICES = (
    (RESPONSIBLE_PERSON, 'Responsible Person'),
    (OBSERVER, 'Observer')
)

EMAIL, NOTIFICATION = 'email', 'notification'
REMINDER_NOTIFICATION_METHODS = (
    (EMAIL, 'Email'),
    (NOTIFICATION, 'Notification')
)

WEEK = 'week'
DAY = 'day'
MONTH = 'month'
YEAR = 'year'
REPEAT_TERM_CHOICES = (
    (DAY, 'Day'),
    (WEEK, 'Week'),
    (MONTH, 'Month'),
    (YEAR, 'Year')
)
DAY, DATE = 'day', 'date'
DAY_KEY_CHOICES = (
    (DAY, 'Day'),
    (DATE, 'Date')
)

REMINDER_PENDING = 'pending'
REMINDER_SENT = 'sent'
REMINDER_FAILED = 'failed'
REMINDER_STATUS_CHOICES = (
    (REMINDER_PENDING, 'Pending Reminder'),
    (REMINDER_SENT, 'Reminder Sent'),
    (REMINDER_FAILED, 'Reminder Failed'),
)

# Maximum Task
# Used at:
#   irhrs.task.api.v1.views.attachment.TaskAttachmentViewSet
#   irhrs.task.api.v1.serializers.attachment.TaskAttachmentSerializer#validate_attachment
TASK_ATTACHMENT_MAX_UPLOAD_SIZE = 2 * 1024 * 1024

APPROVAL_PENDING = 'Approval Pending'
SCORE_NOT_PROVIDED = 'Score Not Provided'
ACKNOWLEDGE_PENDING = 'Acknowledge Pending'
FORWARDED_TO_HR = 'Forwarded To HR'
APPROVED_BY_HR = 'Approved By HR'
ACKNOWLEDGED = 'Acknowledged'
NOT_ACKNOWLEDGED = 'Not Acknowledged'

CYCLE_STATUS = (
    (APPROVAL_PENDING, APPROVAL_PENDING),
    (SCORE_NOT_PROVIDED, SCORE_NOT_PROVIDED),
    (ACKNOWLEDGE_PENDING, ACKNOWLEDGE_PENDING),
    (FORWARDED_TO_HR, FORWARDED_TO_HR),
    (APPROVED_BY_HR, APPROVED_BY_HR),
    (ACKNOWLEDGED, ACKNOWLEDGED),
    (NOT_ACKNOWLEDGED, NOT_ACKNOWLEDGED),
)
