import copy
from django.db.models import Q, Case, When, F, DateField, FilteredRelation
from irhrs.core.utils.common import get_tomorrow, get_yesterday
from irhrs.forms.constants import (
    PENDING as FORM_PENDING,
    IN_PROGRESS as FORM_IN_PROGRESS,
    APPROVED as FORM_APPROVED,
    DENIED as FORM_DENIED,
    DRAFT as FORM_DRAFT,
)

def get_form_approval_stats(queryset, fields=None, exclude_fields=None):
    approved_count = queryset.filter(final_status=FORM_APPROVED).count()
    denied_count = queryset.filter(final_status=FORM_DENIED).count()
    pending_count = queryset.filter(final_status=FORM_PENDING).count()
    draft_count = queryset.filter(final_status=FORM_DRAFT, form__is_archived=False).count()
    in_progress_count = queryset.filter(final_status=FORM_IN_PROGRESS).count()
    archived_draft_count = queryset.filter(
        final_status=FORM_DRAFT,
        form__is_archived=True
    ).count()
    total = queryset.count() - archived_draft_count
    stats = {
        "total": total,
        f"{FORM_APPROVED}": approved_count,
        f"{FORM_DENIED}": denied_count,
        f"{FORM_PENDING}": pending_count,
        f"{FORM_IN_PROGRESS}": in_progress_count,
        f"{FORM_DRAFT}": draft_count,
    }
    stats_copy = copy.deepcopy(stats)
    if fields:
        for key in stats_copy:
            if key not in fields:
                stats.pop(key, None)
    if exclude_fields:
        for key in stats_copy:
            if key in exclude_fields:
                stats.pop(key, None)
    return stats


def annotate_last_experience_userform_qs(queryset):
    return queryset.annotate(
        current_experiences=FilteredRelation(
            'user__user_experiences',
            condition=Q(user__user_experiences__is_current=True)
        )
    ).annotate(
        __end_date=Case(
            When(
                # DON'T REMOVE THIS LINE,
                # current_experiences__end_date__isnull is true for current_experiences__isnull
                current_experiences__is_current=True,
                current_experiences__end_date__isnull=False,
                then=F('current_experiences__end_date')
            ),
            When(
                # DON'T REMOVE THIS LINE,
                # current_experiences__end_date__isnull is true for current_experiences__isnull
                current_experiences__is_current=True,
                current_experiences__end_date__isnull=True,
                then=get_tomorrow()
            ),
            default=get_yesterday(),
            output_field=DateField(null=True)
        )
    )
