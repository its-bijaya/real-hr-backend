from django_q.tasks import async_task
from django.contrib.auth import get_user_model
from django.db.models import Avg, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from irhrs.attendance.constants import TRAVEL_ATTENDANCE, TRAINING_ATTENDANCE
from irhrs.attendance.models import TimeSheet
from irhrs.core.utils import email, nested_getattr
from irhrs.core.utils.common import get_today, combine_aware
from irhrs.core.utils.email import send_notification_email
from irhrs.core.utils.training import set_training_members
from irhrs.core.constants.organization import (
    TRAINING_ASSIGNED_UNASSIGNED_EMAIL,
    TRAINING_REQUESTED_ACTION_EMAIL
)
from irhrs.notification.utils import add_notification
from irhrs.training.models import TrainingFeedback, TrainingAttendance, UserTraining, Training
from irhrs.training.models.helpers import MEMBER, OTHERS, APPROVED

USER = get_user_model()


def calibrate_average_rating(instance):
    score = TrainingFeedback.objects.filter(
        training=instance.training
    ).aggregate(
        average=Coalesce(Avg('rating'), Value(0))
    )
    instance.training.average_score = score.get('average')
    instance.training.save()


def update_user_request_and_send_notification(self, user_training_requests, **kwargs):
    users_id = kwargs.get('user', [])
    _status = kwargs.get('status')
    action_remarks = kwargs.get('action_remarks')

    user_training_requests.update(
        status=_status,
        action_remarks=action_remarks
    )
    user_request = user_training_requests.first()
    recipient_users = USER.objects.filter(id__in=users_id)
    add_notification(
        text=f"Requested training \'{user_request.training.name}\' has been {_status}",
        recipient=recipient_users,
        action=user_request.training,
        url=f"/user/my-training",
        actor=self.request.user,
    )

    # send email
    email_subject = "Requested training was {_status}."
    email_body = f"Requested training '{user_training_requests.training.name}' has been {_status}."
    email_recipients = []
    for user in recipient_users:
        can_send_mail = email.can_send_email(user, TRAINING_REQUESTED_ACTION_EMAIL)
        if can_send_mail:
            email_recipients.append(user.email)

    if email_recipients:
        send_notification_email(
            recipients=email_recipients,
            subject=email_subject,
            notification_text=email_body
        )


def delete_members_from_training(self, training, members):
    UserTraining.objects.filter(
        training=training,
        user__in=members
    ).delete()

    TrainingAttendance.objects.filter(
        training=training,
        member__in=members
    ).delete()

    recipient_users = USER.objects.filter(id__in=members)
    email_subject = "Removed from training."
    notification_text=(
        f"You have been removed from training "
        f"\'{training.name}\'."
    )
    recipients = []
    #send email
    for user in recipient_users:
        can_send_mail = email.can_send_email(user, TRAINING_ASSIGNED_UNASSIGNED_EMAIL)
        if can_send_mail:
            recipients.append(user.email)
    if recipients:
        async_task(
            send_notification_email,
            recipients=recipients,
            subject=email_subject,
            notification_text=notification_text
        )

    # send notification
    add_notification(
        text=f"You have been removed from training \'{training.name}\'.",
        recipient=recipient_users,
        action=training,
        url=f"/user/training?training={training.id}",
        actor=self.request.user,
    )


def add_or_update_members_of_training(self, training, users, update_member=False):
    existing_training_members = training.user_trainings.filter(
        user_id__in=users
    ).values_list('user__id', flat=True)
    user_training_requests = training.training_requests.filter(user_id__in=users)
    training_request_users = []
    if user_training_requests:
        update_user_request_and_send_notification(
            self,
            user_training_requests=user_training_requests,
            user=users,
            status=APPROVED,
            action_remarks="Your have been added to this training by HR."
        )

        training_request_users = user_training_requests.values_list('user__id', flat=True)
    new_training_members = set(users).difference(set(existing_training_members))

    update_member_in_cache = False
    if update_member:
        deleted_members = training.user_trainings.exclude(
            user_id__in=users
        ).values_list('user_id', flat=True)
        delete_members_from_training(self, training, list(deleted_members))
        set_training_members()

    if new_training_members:
        training_members = []
        training_attendances = []
        users = USER.objects.filter(id__in=new_training_members)
        for user in users:
            training_members.append(
                UserTraining(
                    user=user,
                    training=training,
                    start=timezone.now(),
                    training_need=OTHERS
                )
            )

            training_attendances.append(
                TrainingAttendance(
                    member=user,
                    training=training,
                    position=MEMBER
                )
            )

        if training_members and training_attendances:
            update_member_in_cache = True
            UserTraining.objects.bulk_create(training_members)
            TrainingAttendance.objects.bulk_create(training_attendances)

            # send email
            recipient_users = users.exclude(id__in=training_request_users)
            email_subject = "New training assigned."
            email_body = f"'{training.name}' has been assigned to you."
            email_recipients = []
            for user in recipient_users:
                can_send_mail = email.can_send_email(user, TRAINING_ASSIGNED_UNASSIGNED_EMAIL)
                if can_send_mail:
                    email_recipients.append(user.email)

            if email_recipients:
                async_task(
                    send_notification_email,
                    recipients=email_recipients,
                    subject=email_subject,
                    notification_text=email_body
                )

            # send notification
            add_notification(
                text=f"You have been added to training \'{training.name}\'.",
                recipient=users.exclude(id__in=training_request_users),
                action=training,
                url=f"/user/training?training={training.id}",
                actor=self.request.user,
            )

        if update_member_in_cache:
            set_training_members()


def manage_training_attendances_for_today(date=None):
    date = get_today() if not date else date
    training_qs = Training.objects.filter(
        start__date__lte=date, end__date__gte=date
    )
    user_training_qs = []
    for training in training_qs:
        user_training_qs.extend(list(training.user_trainings.all()))

    for user_training in user_training_qs:
        clocks = []
        timesheets = TimeSheet.objects.filter(
            timesheet_for=date,
            timesheet_user=user_training.user
        )
        user_workshift = nested_getattr(user_training.user, 'attendance_setting.work_shift')
        user_worktime = user_workshift.work_days.filter(
            day=date.weekday()).first()
        if not timesheets and user_worktime:
            clocks.extend(get_timesheet_clocks(date, user_worktime))

        for ts in timesheets:
            if ts.expected_punch_in and ts.expected_punch_out:
                clocks.append(ts.expected_punch_in)
                clocks.append(ts.expected_punch_out)

            elif user_worktime:
                clocks.extend(get_timesheet_clocks(date, user_worktime))

        for timestamp in clocks:
            TimeSheet.objects.clock(
                user=user_training.user,
                date_time=timestamp,
                entry_method=TRAINING_ATTENDANCE
            )


def get_timesheet_clocks(date, user_worktime):
    clocks = []
    clocks.append(
        combine_aware(
            date,
            user_worktime.start_time
        )
    )
    clocks.append(
        combine_aware(
            date,
            user_worktime.end_time
        )
    )
    return clocks
