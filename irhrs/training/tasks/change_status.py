from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from irhrs.core.utils import get_system_admin
from irhrs.hris.constants import EXPIRED
from irhrs.notification.models import Notification
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import (FULL_TRAINING_PERMISSION,
                                                    TRAINING_CREATE_PERMISSION)
from irhrs.training.models import Training, UserTrainingRequest
from irhrs.training.models.helpers import IN_PROGRESS, COMPLETED, PENDING, REQUESTED


def validate_sent_notification(training, text):
    """
    Validates whether the notification has already been sent to
    ( user/organization ) or not.
    """
    user_notification = org_notification = True
    notification_sent_to_user = Notification.objects.filter(
        text__icontains=text,
        action_content_type=ContentType.objects.get_for_model(Training),
        action_object_id=training.id,
    )

    if notification_sent_to_user.exists():
        user_notification = False

    notification_sent_to_organization = OrganizationNotification.objects.filter(
        text__icontains=text,
        action_content_type=ContentType.objects.get_for_model(Training),
        action_object_id=training.id,
        recipient=training.training_type.organization
    )

    if notification_sent_to_organization.exists():
        org_notification = False

    return user_notification, org_notification


def send_training_notification(trainings, text, url, going_to=False):
    for training in trainings:
        user_notification = org_notification = True
        if going_to:
            user_notification, org_notification = validate_sent_notification(
                training,
                f"Training {training.name} {text} after",
            )

            if not user_notification and not org_notification:
                continue

            duration = training.start - timezone.now()
            duration_minutes = duration.seconds // 60
            new_text = f"Training {training.name} {text} after {duration_minutes} minutes."
        else:
            new_text = f"Training {training.name} {text}."

        if user_notification:
            members = set(map(lambda x: x.user, training.user_trainings.all()))
            add_notification(
                text=new_text,
                actor=None,
                action=training,
                recipient=members,
                url=url
            )

        if org_notification:
            notify_organization(
                text=new_text,
                organization=training.training_type.organization,
                actor=get_system_admin(),
                url=f'/admin/{training.training_type.organization.slug}/training/training-list',
                action=training,
                permissions=[
                    FULL_TRAINING_PERMISSION,
                    TRAINING_CREATE_PERMISSION
                ]
            )


def check_status_and_send_notification():
    _going_to_held = Training.objects.filter(
        status=PENDING,
        start__lte=timezone.now() + timedelta(minutes=15),
        start__gte=timezone.now()
    )

    if _going_to_held:
        send_training_notification(
            trainings=_going_to_held,
            text=f"is going to be held ",
            url='/user/training',
            going_to=True
        )

    _in_progress = Training.objects.filter(
        status=PENDING,
        start__lte=timezone.now(),
        end__gte=timezone.now()
    )

    if _in_progress:
        send_training_notification(
            trainings=_in_progress,
            text=f"is happening",
            url='/user/training'
        )

        UserTrainingRequest.objects.filter(
            training__in=_in_progress,
            status=REQUESTED
        ).update(status=EXPIRED)

        _in_progress.update(status=IN_PROGRESS)

    _completed = Training.objects.filter(
        status=IN_PROGRESS,
        start__lte=timezone.now(),
        end__lte=timezone.now()
    )

    if _completed:
        send_training_notification(
            trainings=_completed,
            text=f"is completed",
            url='/user/training'
        )
        _completed.update(status=COMPLETED)

    # filter out past trainings & change their status to completed
    # as training now supports past dates while creating

    _past_training_to_completed = Training.objects.filter(
            status=PENDING,
            start__lte=timezone.now(),
            end__lte=timezone.now()
    )

    if _past_training_to_completed:
        _past_training_to_completed.update(status=COMPLETED)
