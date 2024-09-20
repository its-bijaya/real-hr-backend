from django.db.models import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from irhrs.common.models import BaseModel
from irhrs.core.constants.organization import FISCAL_YEAR_CATEGORY
from irhrs.organization.models import Organization


class TimeSheetRegistrationReportSettings(BaseModel):
    """
    Settings to configure presentation of timesheet_registration_report
    """

    DEFAULT_PRIMARY_LEGEND = [
        {
            "letter": "O",
            "color": "#000000",
            "text": "OffDay",
            "name": "offday"
        },
        {
            "letter": "A",
            "color": "#FF0000FF",
            "text": "Absent",
            "name": "absent"
        },
        {
            "letter": "H",
            "color": "#2196F3FF",
            "text": "Holiday",
            "name": "holiday"
        },
        {
            "letter": "8",
            "color": "#F57C00FF",
            "text": "Time Registered",
            "name": "time_registered"
        },
        {
            "letter": "C",
            "color": "#FC766AFF",
            "text": "Credit Hour Consumed",
            "name": "credit_hour_consumed"
        }
    ]

    organization = models.OneToOneField(
        to=Organization,
        on_delete=models.CASCADE,
        related_name='timesheet_registration_report_setting'
    )
    headers = JSONField(help_text="Header field to display name map")
    primary_legend = JSONField(help_text="Primary legend configuration")
    leave_legend = JSONField()
    selected_leave_types = models.ManyToManyField(
        to="leave.LeaveType",
        related_name='selected_timesheet_registration_report_setting'
    )

    approval_required = models.BooleanField(
        default=False,
        help_text="When true, will generate this report on first day of next"
                  " month and send for approval."
    )
    fiscal_year_category = models.CharField(
        choices=FISCAL_YEAR_CATEGORY,
        null=True,
        help_text="When approval required is set, choose fiscal year type to"
                  " use while selecting 1st day of month.",
        max_length=32,  # same as organization.FiscalYear.category,
        db_index=True
    )

    worked_hours_ceil_limit = models.IntegerField(
        default=30,
        help_text="If minutes in worked duration reaches this limit, one will be"
                  " added in worked hours. ",
        validators=[
            MaxValueValidator(limit_value=59), MinValueValidator(limit_value=1)
        ]
    )

    @classmethod
    def get_default_timesheet_registration_report_settings(cls, organization):
        return cls(
            organization=organization,
            headers={
                "report_title": "Timesheet Report",
                "full_name": "Name",
                "employee_code": "SAP Number#",
                "employment_type": "Employment Type",
                "division": "Division",
                "job_title": "Job Title",
                "branch": "Branch",
                "contract_start": "Contract Start",
                "contract_end": "Contract End",
                "bio_user_id": "Bio User Id",
                "proportionate_rate": "Proportionate Rate"
            },
            primary_legend=cls.DEFAULT_PRIMARY_LEGEND,
            leave_legend=[],
            approval_required=False,
            fiscal_year_category='leave'
        )

    @classmethod
    def setting_for_organization(cls, organization):
        setting = cls.objects.filter(organization=organization).first()
        if not setting:
            setting = cls.get_default_timesheet_registration_report_settings(organization)
        return setting
