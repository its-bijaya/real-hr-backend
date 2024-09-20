from rest_framework.exceptions import ValidationError
from django.db import models
from django.db.models import (
    OuterRef, Value,
    Expression, Q, When, Case,
    Exists, Count
)

from irhrs.forms.constants import (
    DENIED,
    APPROVED,
    REQUESTED,
    IN_PROGRESS,
    PENDING,
    DRAFT
)
from irhrs.core.utils import get_system_admin
from irhrs.forms.models import (
    FormAnswerSheetApproval,
    AnswerSheetStatus,
    UserFormAnswerSheet
)
from irhrs.core.constants.payroll import (
    FIRST, SECOND, THIRD,
    ALL, SUPERVISOR,
)
from irhrs.users.models import UserSupervisor


def get_next_applicable_approval_for_sheet(answer_sheet, sheet_approvals_to_check):
    for approval in sheet_approvals_to_check:
        has_approver_approved_previously = AnswerSheetStatus.objects.filter(
            approver__in=approval.employees.all(),
            answer_sheet=answer_sheet
        ).filter(
            ~Q(action=REQUESTED)
        )
        if has_approver_approved_previously:
            continue
        if answer_sheet.user in approval.employees.all():
            continue
        system_admin = get_system_admin()
        # if Do not assign supervisor is checked in supervisor assign page,
        # system admin is assigned as the supervisor
        approvers = approval.employees.filter(~Q(id=system_admin.id))
        if approvers.exists():
            return approval
    return None

def get_next_approval_level(answer_sheet):
    ordered_approval_sheet_settings = FormAnswerSheetApproval.objects.filter(
        answer_sheet=answer_sheet
    ).order_by('approval_level')
    denied_actions = AnswerSheetStatus.objects.filter(
        answer_sheet=answer_sheet,
        action=DENIED
    )
    if denied_actions.exists():
        # if there is a denied action, approval chain has ended
        return None
    # select all answer sheet action except the one where it was created
    latest_actions = AnswerSheetStatus.objects.filter(
        answer_sheet=answer_sheet
    ).exclude(
        action=REQUESTED
    ).order_by('approval_level__approval_level')

    if not latest_actions:
        latest_action_approval_order = 0
    else:
        latest_action = latest_actions.last()
        latest_action_approval_order = latest_action.approval_level.approval_level

    sheet_approvals_to_check = ordered_approval_sheet_settings.filter(
        approval_level__gt=latest_action_approval_order,
        answer_sheet=answer_sheet
    ).order_by('approval_level')

    next_approval = get_next_applicable_approval_for_sheet(
        answer_sheet=answer_sheet,
        sheet_approvals_to_check=sheet_approvals_to_check
    )
    return next_approval


def get_next_approvers(answer_sheet):
    """ Returns list of next approvers. """

    next_approval = get_next_approval_level(answer_sheet)
    if next_approval:
        return next_approval.employees.all()
    return []


def validate_approval_level(answer_sheet, approver):
    setting_exists = answer_sheet.form_answer_sheet_approvals.exists()
    if not setting_exists:
        raise ValidationError({"error": "Approval levels are not set for this submission."})
    next_approval_level = get_next_approval_level(answer_sheet)
    if not next_approval_level:
        raise ValidationError(
            {"error": "Submission is already in final state and no action is needed.."}
        )

    is_approver_valid = approver in next_approval_level.employees.all()
    if not is_approver_valid:
        raise ValidationError({
            "error": "Current user is not the next approver in the approval chain."
        })
    elif next_approval_level.approve_by == SUPERVISOR:
        required_supervisor_approval_level = next_approval_level.supervisor_level
        supervisors = UserSupervisor.objects.filter(
            user=answer_sheet.user
        )
        is_approver_in_supervisors = supervisors.filter(
            supervisor=approver
        ).exists()
        if not is_approver_in_supervisors:
            raise ValidationError({"error": "Current user is not a supervisor of submitter."})
        if required_supervisor_approval_level != ALL:
            numbers_map = {
                FIRST: 1,
                SECOND: 2,
                THIRD: 3,
            }
            # convert FIRST to 1, SECOND to 2 etc
            supervisor_level_in_number = numbers_map[required_supervisor_approval_level]
            approver = supervisors.filter(
                supervisor=approver, authority_order=supervisor_level_in_number
            ).exists()
            if not approver:
                raise ValidationError(
                    {"error": "Current user is not a supervisor of required authority level."}
                )




def get_answer_sheets_with_annotation(current_user, filters=None, exclude=None):
    """
    Returns AnswerSheet with the following annotations:

    * is_current_user_approver
    -> Whether the current is an approver of the form within any approval level

    * is_current_user_next_approver
    Stores inside the annotation whether the user passed to this function
    is the next approver of form

    * final_status
    Dynamic status of the form. The states are:

    PEDNING for all users if:
        - The form is sent but has not been approved/denied even once.
    PEDNING for current user if:
        - current user is the next approver in the chain
    IN PROGRESS for current user if:
        - current user in the approval chain or is submitter but is not the next approver
    APPROVED
        - If form is approved
    DENIED
        - If form is denied

    """

    queryset = UserFormAnswerSheet.objects.all()
    if filters:
        queryset = queryset.filter(**filters)

    if exclude:
        queryset = queryset.exclude(**exclude)

    annotated_queryset = queryset.annotate(
        sheet_actions=Count('status')
    ).annotate(
        is_current_user_next_approver=Exists(
            FormAnswerSheetApproval.objects.filter(
                answer_sheet=OuterRef('id'),
                approval_level=OuterRef('next_approval_level'),
                employees__in=[current_user]
            )
        )
    ).annotate(
        is_current_user_low_level_approver=Exists(
            FormAnswerSheetApproval.objects.filter(
                employees__in=[current_user],
                answer_sheet=OuterRef('id'),
                approval_level__lte=OuterRef('next_approval_level')
            )
        )
    ).annotate(
        is_approval_setting_present=Exists(
            FormAnswerSheetApproval.objects.filter(
                answer_sheet=OuterRef('id')
            )
        )
    ).annotate(
        is_denied=Exists(
            AnswerSheetStatus.objects.filter(
                answer_sheet=OuterRef('id'),
                action=DENIED
            )
        )
    ).annotate(
        final_status=Case(
            When(is_draft=True, then=Value(DRAFT)),
            When(is_approved=True, then=Value(APPROVED)),
            When(is_denied=True, then=Value(DENIED)),
            When(is_approval_setting_present=False, then=Value(APPROVED)),
            When(sheet_actions=1, is_draft=False,
                 user=current_user,
                 then=Value(PENDING)),
            When(is_draft=False,
                 is_current_user_next_approver=True,
                 then=Value(PENDING)),
            default=Value(IN_PROGRESS),
            output_field=models.CharField()
        )
    ).order_by('final_status').distinct()
    return annotated_queryset
