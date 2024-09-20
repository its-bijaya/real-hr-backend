from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from irhrs.permission.constants.permissions import (
    FORM_PERMISSION,
    FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS
)
from irhrs.notification.models.notification import OrganizationNotification
from irhrs.notification.models import Notification
from irhrs.organization.models import Organization
from irhrs.notification.utils import notify_organization, add_notification
from irhrs.core.utils.common import get_today
from irhrs.core.utils import get_system_admin
from irhrs.forms.models import Form, UserForm, UserFormAnswerSheet


def send_deadline_exceeded_notification():
    for organization in Organization.objects.all():
        exceeded_forms = Form.objects.filter(
            organization=organization,
            is_archived=False,
            deadline__lte=get_today(with_time=True)
        )
        for form in exceeded_forms:
            if get_today(with_time=True) > form.deadline:
                # text = (
                #     f"Deadline '{form.deadline.date()} {form.deadline.time()}' "
                #     f"for form '{form.name}' has expired."
                # )
                deadline = timezone.localtime(form.deadline)
                text = (
                    f"Form '{form.name}' expired on '{deadline.date()} {deadline.hour}:{deadline.minute}'."
                )
                hr_notification_already_sent = OrganizationNotification.objects.filter(
                    text=text,
                    action_content_type=ContentType.objects.get_for_model(Form),
                    action_object_id=form.id,
                    recipient=organization
                ).exists()
                if not hr_notification_already_sent:
                    notify_organization(
                        text=text,
                        organization=organization,
                        action=form,
                        url=f'/admin/{organization.slug}/form/response',
                        permissions=[
                            FORM_PERMISSION,
                            FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS
                        ]
                    )
                assignments = form.form_assignments.all()
                assigned_users = [assignment.user for assignment in assignments]
                for user in assigned_users:
                    user_notification_already_sent = Notification.objects.filter(
                        text__icontains=text,
                        action_content_type=ContentType.objects.get_for_model(Form),
                        action_object_id=form.id,
                        recipient=user.id
                    )
                    if not user_notification_already_sent:
                        add_notification(
                            text=text,
                            actor=get_system_admin(),
                            action=form,
                            recipient=assigned_users,
                            url='/user/organization/forms'
                        )




def send_notification_if_all_users_submitted(answer_sheet):
    assigned_users = UserForm.objects.filter(
        form=answer_sheet.form
    )
    assigned_user_ids = set([assignment.user.id for assignment in assigned_users])
    answer_sheets = UserFormAnswerSheet.objects.filter(
        form=answer_sheet.form
    )
    answer_sheet_user_ids = set([sheet.user.id for sheet in answer_sheets])
    if assigned_user_ids.issubset(answer_sheet_user_ids):
        text = f"All users have submitted answers for form {answer_sheet.form.name}."
        organization = answer_sheet.user.detail.organization
        notify_organization(
            text=text,
            action=answer_sheet.form,
            actor=get_system_admin(),
            organization=organization,
            url=f'/admin/{organization.slug}/form/response',
            permissions=[
                FORM_PERMISSION,
                FORM_CAN_VIEW_AND_ACT_ON_USER_FORMS
            ]
        )
