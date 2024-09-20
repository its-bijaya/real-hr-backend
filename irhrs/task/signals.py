from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from irhrs.core.constants.common import TASK_APPROVAL_NOTIFICATION, TASK_ACKNOWLEDGE_NOTIFICATION
from irhrs.core.utils.common import DummyObject
from irhrs.notification.utils import add_notification, notify_organization
from irhrs.permission.constants.permissions import TASK_PERMISSION, TASK_APPROVALS_PERMISSION
from irhrs.task.api.v1.serializers.association import TaskAssociationSerializer
from irhrs.task.constants import (RESPONSIBLE_PERSON, ACKNOWLEDGE_PENDING, FORWARDED_TO_HR,
                                  APPROVED_BY_HR,
                                  ACKNOWLEDGED, NOT_ACKNOWLEDGED, SCORE_NOT_PROVIDED)
from irhrs.task.models import Task
from irhrs.task.models.task import (TaskActivity, TaskComment, TaskAttachment,
                                    TaskAssociation, MAX_LIMIT_OF_TASK_SCORING_CYCLE,
                                    TaskVerificationScore)


def create_activity(task,
                    key,
                    description,
                    previous_value=None,
                    previous_value_display=None,
                    present_value=None,
                    present_value_display=None,
                    created_by=None):
    TaskActivity.objects.create(
        task=task,
        key=key,
        description=description,
        previous_value=previous_value,
        previous_value_display=previous_value_display,
        present_value=present_value,
        present_value_display=present_value_display,
        created_by=created_by
    )


@receiver(post_save, sender=Task)
def create_sub_task_activity(sender, instance, created, **kwargs):
    if created:
        if instance.parent:
            create_activity(
                task=instance.parent,
                key='sub_task',
                description=f'Created Sub-task {instance.title}',
                previous_value=None,
                previous_value_display=None,
                present_value=instance,
                present_value_display=instance,
            )
    else:
        if instance.parent:
            if instance.approved:
                create_activity(
                    task=instance.parent,
                    key='approved',
                    description=f'{instance.title} has been Approved',
                    previous_value=None,
                    previous_value_display=None,
                    present_value=instance,
                    present_value_display=instance,
                )


@receiver(post_save, sender=TaskComment)
def create_comment_activity(sender, instance, created, **kwargs):
    if created:
        create_activity(
            task=instance.task,
            key='comment',
            description=f'Added comment as {instance.comment}',
            previous_value=None,
            previous_value_display=None,
            present_value=instance.comment,
            present_value_display=instance.comment,
        )
        # do not send notification if the task is recurring template
        if not instance.task.is_recurring:
            text = f'has added a comment on Task "{instance.task.title}" '
            # add every possible recipients , add_notification will ignore
            # if actor=recipient
            recipients = [instance.task.created_by] + [
                assoc.user for assoc in instance.task.task_associations.all()
            ]
            add_notification(
                text,
                recipients,
                instance,
                url=f'/user/task/my/{instance.task.id}/detail',
                actor=instance.created_by
            )


@receiver(pre_delete, sender=TaskComment)
def delete_comment_activity(sender, instance, using, **kwargs):
    create_activity(
        task=instance.task,
        key='comment',
        description=f'Removed a comment',
        previous_value=None,
        previous_value_display=None,
        present_value='Removed a comment',
        present_value_display='Removed a Comment',
    )
    # do not send notification if the task is recurring template
    if not instance.task.is_recurring:
        text = f'has removed a comment on  Task "{instance.task.title}" '

        # add every possible recipients , add_notification will ignore
        # if actor=recipient
        recipients = [instance.task.created_by] + [
            assoc.user for assoc in instance.task.task_associations.all()
        ]
        add_notification(
            text,
            recipients,
            instance,
            url=f'/user/task/my/{instance.task.id}/detail',
            actor=instance.created_by
        )


@receiver(post_save, sender=TaskAttachment)
def create_attachment_activity(sender, instance, created, **kwargs):
    if created:
        create_activity(
            task=instance.task,
            key='attachment',
            description=f'Added Attachment {instance.caption}',
            previous_value=None,
            previous_value_display=None,
            present_value=instance.attachment,
            present_value_display=instance.caption,
        )


@receiver(pre_delete, sender=TaskAttachment)
def delete_attachment_activity(sender, instance, using, **kwargs):
    create_activity(
        task=instance.task,
        key='attachment',
        description=f'Removed Attachment {instance.caption}',
        previous_value=None,
        previous_value_display=None,
        present_value=instance.caption,
        present_value_display=f'Removed Attachment {instance.caption}',
    )


@receiver(post_save, sender=TaskAssociation)
def create_association_activity(sender, instance, created, **kwargs):
    if created:
        assoc = 'Responsible Person' if instance.association == RESPONSIBLE_PERSON else "Observer"
        description = "Added {} as {}".format(instance.user.full_name, assoc)
        create_activity(
            task=instance.task,
            key='association',
            description=description,
            previous_value=None,
            previous_value_display=None,
            present_value=instance.user,
            present_value_display=instance.user.full_name,
            created_by=instance.task.created_by
        )
        # Do not send notification if the task is recurring
        if not instance.task.is_recurring:
            text = f'{instance.task.title} has been assigned to you' if \
                instance.association == RESPONSIBLE_PERSON else \
                f'You have been added as Observer to Task {instance.task.title}'
            add_notification(
                text,
                instance.user,
                instance,
                url=f'/user/task/my/{instance.task.id}/detail',
                actor=instance.created_by
            )


@receiver(pre_delete, sender=TaskAssociation)
def delete_association_activity(sender, instance, using, **kwargs):
    assoc = 'Responsible Person' if instance.association == RESPONSIBLE_PERSON else "Observer"
    description = "Removed {} from {}".format(instance.user.full_name, assoc)
    create_activity(
        task=instance.task,
        key='association',
        description=description,
        previous_value=None,
        previous_value_display=None,
        present_value=instance.user,
        present_value_display=instance.user.full_name,
    )
    add_notification(
        f'You have been removed from Task {instance.task.title} ',
        instance.user,
        instance,
        actor=instance.created_by
    ) if not instance.task.is_recurring else None


def verification_score_notification(instance, text, acknowledge=False, decline=False, **kwargs):
    recipient = kwargs.get('recipient', None)
    actor = kwargs.get('actor', True)

    _as = kwargs.get(
        '_as',
        'assigner' if acknowledge else 'responsible'
    )
    user = instance.association.user
    recipient, actor = recipient if recipient else user, instance.created_by if actor else None

    if acknowledge and actor:
        # if acknowledged then swap actor and recipient
        recipient, actor = actor, recipient

    if not acknowledge:
        is_interactive = True
    elif acknowledge and decline:
        is_interactive = True
    else:
        is_interactive = False

    if instance.association.cycle_status == FORWARDED_TO_HR:
        is_interactive = False
        text += ' and forwarded to HR.'

    def _get_interactive_notification_kwargs():
        interactive_data = {
            'user_data': TaskAssociationSerializer(
                instance.association,
                context={
                  'request': DummyObject(method='get')
                }
            ).data,
            'max_score_cycle': MAX_LIMIT_OF_TASK_SCORING_CYCLE
        } if not acknowledge else {'user_id': user.id}
        return dict(
            is_interactive=is_interactive,
            interactive_type=TASK_ACKNOWLEDGE_NOTIFICATION if not acknowledge else TASK_APPROVAL_NOTIFICATION,
            interactive_data={
                'task_approval_id': instance.association.task.id,
                **interactive_data
            }
        )

    add_notification(
        text,
        recipient,
        instance,
        url=f'/user/task/approvals?as={_as}',
        actor=actor,
        **_get_interactive_notification_kwargs()
    )


@receiver(post_save, sender=TaskVerificationScore)
def add_cycle_status(sender, instance, created, **kwargs):
    total_cycle = instance.association.taskverificationscore_set.count()
    task_associations = instance.association.task.task_associations.exclude(
        id=instance.association.id
    ).filter(association=RESPONSIBLE_PERSON)
    for task_association in task_associations:
        if task_association.cycle_status not in [ACKNOWLEDGE_PENDING,
                                                 FORWARDED_TO_HR,
                                                 APPROVED_BY_HR,
                                                 ACKNOWLEDGED,
                                                 NOT_ACKNOWLEDGED]:
            TaskAssociation.objects.filter(id=task_association.id).update(
                cycle_status=SCORE_NOT_PROVIDED)
    if instance.association.taskverificationscore_set.filter(
            ack__isnull=True).exists():
        instance.association.cycle_status = ACKNOWLEDGE_PENDING
    elif instance.association.taskverificationscore_set.filter(ack=True).exists() and \
            total_cycle <= MAX_LIMIT_OF_TASK_SCORING_CYCLE:
        instance.association.cycle_status = ACKNOWLEDGED
    elif total_cycle == MAX_LIMIT_OF_TASK_SCORING_CYCLE:
        instance.association.cycle_status = FORWARDED_TO_HR

        def send_forwarded_to_hr_notification():
            task = instance.association.task
            _assigned_by = task.created_by
            _assigned_for = instance.association.user
            text = f"Task '{task.title}' assigned by {_assigned_by} to {_assigned_for} is" \
                   f" forwarded to HR."

            _assigner_organization = _assigned_by.detail.organization
            _assignee_organization = _assigned_for.detail.organization

            targeted_organizations = (
                [_assigner_organization, _assignee_organization],
                [_assigner_organization]
            )[_assigner_organization == _assignee_organization]

            for organization in targeted_organizations:
                notify_organization(
                    text=text,
                    action=_assigned_by,
                    organization=organization,
                    permissions=[
                        TASK_PERMISSION,
                        TASK_APPROVALS_PERMISSION
                    ],
                    url=f'/admin/{organization.slug}/task/approvals'
                )

        send_forwarded_to_hr_notification()
    elif total_cycle > MAX_LIMIT_OF_TASK_SCORING_CYCLE:
        instance.association.cycle_status = APPROVED_BY_HR
    else:
        instance.association.cycle_status = NOT_ACKNOWLEDGED

    instance.association.save()
    if instance.score and instance.ack is None:
        text = f'Score has been provided by {instance.created_by} ' \
               f'for task `{instance.association.task.title}`'
        verification_score_notification(instance, text)

    if instance.score and instance.ack is not None:
        if instance.association.cycle_status == APPROVED_BY_HR:
            send_task_acknowledge_by_hr_notification(instance)
        else:
            text = 'Provided score for task `{}` has been {}'.format(
                instance.association.task.title,
                'acknowledged' if instance.ack else f'declined'
            )
            # if acknowledged, declined = False
            verification_score_notification(
                instance, text, acknowledge=True, decline=not bool(instance.ack)
            )


def send_task_acknowledge_by_hr_notification(instance):
    # notification for task creator
    text = 'Task `{}` assigned by you has been approved by HR.'.format(
        instance.association.task.title
    )
    kwargs = {
        'instance': instance,
        'text': text,
        'acknowledge': True,
        'decline': not bool(instance.ack),
        'recipient': instance.association.created_by,
        'actor': False,
        '_as': True
    }
    verification_score_notification(**kwargs)

    # notification for responsible person
    kwargs.update({
        'text': text.replace('assigned by', 'assigned to'),
        'recipient': instance.association.user

    })
    verification_score_notification(**kwargs)
