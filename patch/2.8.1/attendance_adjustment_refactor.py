from django.db import transaction
from django.db.models import Q, F, Count
from django.db.models.functions import Coalesce
from django.db.models.signals import post_save
from django.utils import timezone

from irhrs.attendance.models import AttendanceAdjustment, AttendanceAdjustmentHistory, TimeSheet
from irhrs.attendance.signals import create_attendance_adjustment_notification, \
    create_overtime_recalibration_notification
from django.db.models.signals import post_save
from django.dispatch import Signal


Signal.disconnect(
    post_save,
    receiver=create_attendance_adjustment_notification,
    sender=AttendanceAdjustmentHistory
)
Signal.disconnect(
    post_save,
    receiver=create_overtime_recalibration_notification,
    sender=AttendanceAdjustmentHistory
)


@transaction.atomic
def find_solo_attendance_adjustments_to_fix(queryset):
    simple_queryset = queryset
    simple_queryset.update(
        timestamp=Coalesce(
            F('new_punch_in'), F('new_punch_out')
        )
    )
    simple_queryset.update(
        new_punch_in=None,
        new_punch_out=None
    )
    # find adjacent timesheet_entry
    # add_timesheet_entry_to_adjustments(simple_queryset)


def find_multiple_attendance_adjustments_to_fix(complex_queryset):

    for adjustment in complex_queryset:
        timestamp = adjustment.new_punch_out
        adjustment.new_punch_out = None
        adjustment.save()
        existing_histories = list(adjustment.adjustment_histories.order_by('id'))
        adjustment.id = None
        adjustment.new_punch_in = None
        adjustment.timestamp = timestamp
        adjustment.save()
        for history in existing_histories:
            history.id = None
            history.adjustment_id = adjustment.id
            history.save()


def add_timesheet_entry_to_adjustments(simple_queryset):
    for adjustment in simple_queryset:
        timesheet_entry = adjustment.timesheet.timesheet_entries.filter(
            timestamp=adjustment.timestamp
        ).first()
        adjustment.timesheet_entry = timesheet_entry
        adjustment.save()


GLOBAL_FILTER = {'timestamp__isnull': True}


@transaction.atomic
def run():
    # create new adjustment from punch out
    complex_queryset = AttendanceAdjustment.objects.filter(
        new_punch_in__isnull=False,
        new_punch_out__isnull=False
    ).filter(
        **GLOBAL_FILTER
    )
    find_multiple_attendance_adjustments_to_fix(complex_queryset)
    # transfer punch in to timestamp
    simple_queryset = AttendanceAdjustment.objects.filter(
        Q(new_punch_in__isnull=True) | Q(new_punch_out__isnull=True)
    ).exclude(
        new_punch_in__isnull=True,
        new_punch_out__isnull=True
    ).filter(
        **GLOBAL_FILTER
    )
    find_solo_attendance_adjustments_to_fix(simple_queryset)
    # find and add equivalent timesheet entry to adjustment
    add_timesheet_entry_to_adjustments(
        AttendanceAdjustment.objects.all().filter(
            **GLOBAL_FILTER
        )
    )


run()
# post_save.connect(create_attendance_adjustment_notification)
# post_save.connect(create_overtime_recalibration_notification)

"""
# Verification script (Run Before and After)
allx = AttendanceAdjustment.objects.all().order_by('timesheet')
for adj in allx:
    pi = adj.new_punch_in.astimezone().time() if adj.new_punch_in else 'X PunIn'
    po = adj.new_punch_out.astimezone().time() if adj.new_punch_out else 'X PunOut'
    print(
        *map(
            lambda z: str(z).ljust(10)[:10],[
                adj.id,
                adj.timesheet.id,
                pi,
                po,
                adj.timestamp.astimezone().time() if adj.timestamp else 'X Timestamp',
                adj.category or '-',
                *itertools.chain.from_iterable(
                    adj.adjustment_histories.order_by(
                        'id'
                    ).values_list(
                        'action_performed',
                        'action_performed_by'
                    )
                )
            ]
        )
    )
"""


basx = TimeSheet.objects.filter(
    adjustment_requests__isnull=False
).annotate(
    adjustments=Count('adjustment_requests')
)
for parent_timesheet_of_duplicate_adjustments in basx:
    oldest = parent_timesheet_of_duplicate_adjustments.adjustment_requests.order_by(
        'created_at'
    ).first()
    if not oldest:
        continue
    oldest = oldest.created_at.astimezone().isoformat()
    AttendanceAdjustment.objects.filter(
        timesheet=parent_timesheet_of_duplicate_adjustments
    ).filter(
        created_at__date=timezone.now().date()
    ).update(
        created_at=oldest,
        modified_at=oldest
    )

#  git remote add 68 irhrs@192.168.99.68:~/backend.git
