from argparse import RawTextHelpFormatter
from collections import OrderedDict
from datetime import time, date

from django.core.management import BaseCommand
from django.utils import timezone
from django_q.models import Schedule

from irhrs.core.utils.common import combine_aware
from irhrs.organization.models import FiscalYear, Organization

CGREEN = '\33[32m'
CRED = '\33[31m'
CBOLD = '\33[1m'
CEND = '\33[0m'
MINUTES = 'I'

fiscal = [
    f for f in [
        FiscalYear.objects.current(org) for org in Organization.objects.all()
    ] if f]

if fiscal:
    dstart = min([fis.applicable_from for fis in fiscal if fiscal])
    dend = max([fis.applicable_to for fis in fiscal if fiscal])
else:
    year = timezone.now().year
    dstart = date(year, 1, 1)
    dend = date(year + 1, 1, 1) - timezone.timedelta(days=1)

MIDNIGHT_TODAY = combine_aware(
    timezone.now().date() + timezone.timedelta(days=1),
    time(0, 0)
)


class Command(BaseCommand):
    SCHEDULES_DATA_PER_MODULE = {
        'organization': [
            OrderedDict(
                [
                    ('name', 'Holiday Notification'),
                    ('func', 'irhrs.organization.tasks.send_holiday_email_notification'),
                    ('schedule_type', 'D')
                ]
            )
        ],
        'attendance': [
            OrderedDict(
                [
                    ('name', 'Absent notification'),
                    ('func',
                     'irhrs.attendance.utils.helpers.send_absent_notification'),
                    ('schedule_type', 'H'),
                    ('minutes', 1),
                ]),

            OrderedDict(
                [
                    ('name', 'Attendance Pull'),
                    ('func',
                     'irhrs.attendance.tasks.timesheets.sync_attendance'),
                    ('schedule_type', MINUTES),
                    ('minutes', 15),
                ]),

            OrderedDict(
                [
                    ('name', 'Daily TimeSheet Generation'),
                    ('func',
                     'irhrs.attendance.tasks.timesheets.populate_timesheets'),
                    ('schedule_type', 'D'),
                ]),

            OrderedDict(
                [
                    ('name', 'Generate Daily Overtime'),
                    ('func',
                     'irhrs.attendance.tasks.overtime.generate_daily_overtime'),
                    ('schedule_type', 'D'),
                ]),
            OrderedDict(
                [
                    ('name', 'Expire OT'),
                    ('func', 'irhrs.attendance.tasks.overtime.expire_claims'),
                    ('schedule_type', 'D'),

                ]),
        ],
        'leave': [
            OrderedDict(
                [
                    ('name', 'Leave Add Reduce'),
                    ('func', 'irhrs.leave.tasks.add_reduce_leaves'),
                    ('schedule_type', 'D'),
                ]
            ),
            OrderedDict([
                ('name', 'Expire Master Setting'),
                ('func', 'irhrs.leave.tasks.expire_master_settings'),
                ('schedule_type', 'D'),
            ])
        ],
        'task': [
            OrderedDict(
                [
                    ('name', 'Task Reminders'),
                    ('func', 'irhrs.task.tasks.reminder.task_reminder'),
                    ('schedule_type', MINUTES),
                    ('minutes', 5),

                ]),
            OrderedDict(
                [
                    ('name', 'Recurring task'),
                    (
                        'func',
                        'irhrs.task.tasks.recurring.create_recurring_task'),
                    ('schedule_type', 'D'),
                ]
            ),
            OrderedDict(
                [
                    ('name', 'Notify On Boarding Task'),
                    (
                        'func',
                        'irhrs.task.utils.task.notify_on_boarding_task'),
                    ('schedule_type', MINUTES),
                    ('minutes', 5)
                ]
            ),
        ],
        'hris': [
            OrderedDict(
                [
                    #TODO @Ravi: Review
                    ('name', 'Expire Offer Letters'),
                    ('func', 'irhrs.users.utils.auto_expire_offer_letters'),
                    ('schedule_type', 'D'),
                ]),
            OrderedDict(
                [
                    ('name', 'Release Offboarding users.'),
                    ('func', 'irhrs.hris.utils.apply_separation',),
                    ('schedule_type', 'D'),
                ]),
            OrderedDict(
                [
                    ('name', 'Apply Change Type'),
                    ('func', 'irhrs.hris.utils.apply_change_type'),
                    ('schedule_type', 'D'),
                ]),
            OrderedDict(
                [
                    ('name', 'Auto Step Increment'),
                    ('func', 'irhrs.users.utils.apply_auto_increment'),
                    ('schedule_type', 'D'),
                ]),
            OrderedDict(
                [
                    ('name', 'Contract Expiry Notification'),
                    ('func', 'irhrs.hris.tasks.user_experience.notify_contract_expiring'),
                    ('schedule_type', 'D'),
                ]),
            OrderedDict(
                [
                    ('name', 'Pending resignation requests reminder email'),
                    ('func', 'irhrs.hris.tasks.resignation.send_resignation_no_action_taken_email'),
                    ('schedule_type', 'D'),
                ]
            ),
        ],
        'noticeboard': [
            OrderedDict(
                [
                    ('name', 'Birthday And Anniversary Card Generator'),
                    ('func',
                     'irhrs.noticeboard.tasks.generate_gift_card'),
                    ('schedule_type', 'D')
                ]),
        ],
        'event': [
            OrderedDict(
                [
                    ('name', 'Notification About Meeting'),
                    ('func', 'irhrs.event.tasks.send_meeting_notification'),
                    ('schedule_type', MINUTES),
                    ('minutes', 5)
                ]
            )
        ],
        'forms': [
            OrderedDict(
                [
                    ('name', 'Notification about form deadline.'),
                    ('func', 'irhrs.forms.tasks.notification.send_deadline_exceeded_notification'),
                    ('schedule_type', MINUTES),
                    ('minutes', 2),
                ]
            )
        ],
        'training': [
            OrderedDict(
                [
                    ('name', 'Training Status And Notification'),
                    (
                        'func',
                        'irhrs.training.tasks.change_status.check_status_and_send_notification'
                    ),
                    ('schedule_type', MINUTES),
                    ('minutes', 5)
                ]
            )
        ],
        'users': [
            OrderedDict(
                [
                    ('name', 'Insurance Expiration Notification'),
                    (
                        'func',
                        'irhrs.users.utils.notification.notify_expiring_insurance'
                    ),
                    ('schedule_type', 'D')
                ]
            ),
            OrderedDict(
                [
                    ('name', 'Probation completion'),
                    (
                        'func',
                        'irhrs.users.utils.notification.probation_completion_notification'
                    ),
                    ('schedule_type', 'D')
                ]
            )
        ],
        'payroll': [
            OrderedDict([
                ('name', 'Update package on payroll increment'),
                (
                    'func',
                    'irhrs.payroll.tasks.update_package_salary'
                ),
                ('schedule_type', 'D'),
            ])
        ]
    }

    def handle(self, *args, **options):
        installs = self.SCHEDULES_DATA_PER_MODULE.keys()
        last = 0
        for module in installs:
            data = self.SCHEDULES_DATA_PER_MODULE.get(module)
            for index, datum in enumerate(data):
                obj, created = Schedule.objects.get_or_create(
                    **datum
                )
                if not created:
                    self.stdout.write(self.style.ERROR(
                        f"{obj.name} already exists and was ignored"
                    ))
                    continue
                obj.next_run = combine_aware(
                    timezone.now().date() + timezone.timedelta(days=1),
                    time(*divmod(last, 60))
                )
                if (obj.func ==
                        'irhrs.attendance.tasks.overtime.generate_daily_overtime'):
                    dt = timezone.now().date().replace(day=1, month=1).isoformat()
                    obj.args = f"'{dt}',"
                last += 5
                obj.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Created {obj.name} with next run "
                    f"{obj.next_run.astimezone()}"
                ))

    def create_parser(self, *args, **kwargs):
        parser = super().create_parser(*args, **kwargs)
        parser.formatter_class = RawTextHelpFormatter
        return parser


Command.help = f"""{CGREEN} {CBOLD}
Schedule Task According to the Arguments provided
Please Use the following options:
attendance:
   * Daily Time Sheet Generation
   * Absent Notification
   * Overtime Generation
   * Attendance Pull from Device
leave:
    * Leave Accrual/Renewal
task:
    * Task Remainders
{CEND}
"""
