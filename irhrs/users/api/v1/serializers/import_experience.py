from openpyxl import load_workbook
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from irhrs.core.utils.common import get_today
from irhrs.core.utils.excel import ExcelList
from irhrs.core.validators import ExcelFileValidator
from irhrs.export.constants import ADMIN, FAILED
from irhrs.export.models.export import Export
from irhrs.export.utils.helpers import save_virtual_workbook
from irhrs.hris.models import ChangeType
from irhrs.notification.utils import notify_organization
from irhrs.organization.models import (
    OrganizationDivision,
    EmploymentLevel,
    EmploymentStatus,
    EmploymentJobTitle, OrganizationBranch,
)
from irhrs.permission.constants.permissions import HRIS_IMPORT_EMPLOYEE_PERMISSION, HRIS_PERMISSION

USER = get_user_model()


class UserExperienceImportSerializer(serializers.Serializer):
    excel_file = serializers.FileField(
        max_length=100,
        validators=[
            FileExtensionValidator(allowed_extensions=["xlsx", "xlsm", "xltx", "xltm"]),
            ExcelFileValidator()
        ],
        write_only=True,
    )

    @property
    def organization(self):
        return self.context["organization"]

    @property
    def request(self):
        return self.context["request"]

    def validate(self, attrs):
        excel_file = attrs["excel_file"]
        workbook = load_workbook(excel_file)
        excel_list = ExcelList(workbook)
        error_exists = False
        user_experiences = excel_list[1:]
        headers = excel_list[0]
        employees= set()
        allowed_fields = [
            "user",
            "start_date",
            "end_date",
            "job_title",
            "division",
            "branch",
            "employment_type",
            "employment_level",
            "employment_step",
            "change_type",
        ]

        if len(headers) > len(allowed_fields):
            raise ValidationError("Duplicate headings in excel file.")

        if len(headers) < len(allowed_fields):
            raise ValidationError("Missing headings in excel file. Please pass all required fields.")

        for header in headers:
            if not header in allowed_fields:
                raise ValidationError(f"{header} not in {allowed_fields}.")

        for index, user_experience_record in enumerate(user_experiences, 1):
            errors = {}
            user = user_experience_record[0]
            start_date = user_experience_record[1]
            job_title = user_experience_record[3]
            employment_type = user_experience_record[5]
            employment_level = user_experience_record[6]
            change_type = user_experience_record[8]

            def check_empty_field(check_field, field_name, error_msg):
                if not check_field:
                    errors[field_name] = error_msg

            check_empty_field(start_date, "Start Date", "Start Date is required.")
            check_empty_field(job_title, "Job Title", "Job Title is required.")
            check_empty_field(employment_type, "Employement Type", "Employement Type is required.")
            check_empty_field(employment_level, "Employement Level", "Employement Level is required.")
            check_empty_field(change_type, "Title Changed", "Title Changed is required.")

            if user in employees:
                errors["user"] = "Duplicate user"

            employees.add(user)
            # turning our excel record into dictionary and only taking those
            # fields whose value exists, ("-" is also considered null)
            experience_data = dict(zip(headers[:], user_experience_record[:]))
            experience_serializer_data = {
                key: value
                for key, value in experience_data.items()
                if value is not None and value != "-"
            }
            serializer = ExcelExperienceSerializer(
                data=experience_serializer_data, organization=self.organization
            )
            # turning serializer error into more readable format for user
            if not serializer.is_valid():
                serializer_errors = {
                    field: str(detail[0]) if isinstance(detail, list) else str(detail)
                    for field, detail in serializer.errors.items()
                }
                errors = {**errors, **serializer_errors}

            if errors:
                error_exists = True
                excel_list[index].append(str(errors))

        if error_exists:
            excel_list[0].append("Errors")
            error_wb = excel_list.generate_workbook()

            export = Export.objects.filter(export_type="UserExperienceImport").first()

            # only create a new
            if not export:
                export = Export.objects.create(
                    user=self.request.user,
                    name="User Experience Import",
                    exported_as=ADMIN,
                    export_type="UserExperienceImport",
                    organization=self.organization,
                    status=FAILED,
                    remarks="User Experience Import failed.",
                )

            export.export_file.save(
                "user_experience_import.xlsx",
                ContentFile(save_virtual_workbook(error_wb)),
            )
            export.save()
            url = settings.BACKEND_URL + export.export_file.url
            notify_organization(
                text=('User Experience Import Failed.'),
                action=self.organization,
                organization=self.organization,
                url=f'/admin/{self.organization.slug}/hris/employees/import',
                permissions=[
                    HRIS_PERMISSION,
                    HRIS_IMPORT_EMPLOYEE_PERMISSION
                ]
            )
            raise ValidationError({"error_file": url})
        return attrs


class ExcelExperienceSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        assert "organization" in kwargs
        organization = kwargs.pop("organization")
        super().__init__(*args, **kwargs)
        self.organization = organization

    user = serializers.CharField(max_length=255)
    # start_date and end_date are directly converted into datetime instance
    # by openpyxl so using datetime, later only the date will be retrieved
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False, allow_null=True)

    job_title = serializers.CharField(max_length=255, required=False)
    division = serializers.CharField(max_length=255, required=False)
    branch = serializers.CharField(max_length=255, required=False)
    employment_level = serializers.CharField(max_length=255, required=False)
    employment_type = serializers.CharField(max_length=255, required=False)
    change_type = serializers.CharField(max_length=255, required=False)
    employment_step = serializers.IntegerField(required=False)

    def validate_user(self, value):
        user = USER.objects.filter(Q(email=value.strip()) | Q(username=value.strip())).first()
        if not user:
            raise ValidationError(f"User with email/username '{value}' not found")

        latest_user_experience = user.user_experiences.first()
        if not latest_user_experience:
            raise ValidationError(f"User has no user experience to create from.")
        return value

    def validate_job_title(self, value):
        if not EmploymentJobTitle.objects.filter(
            organization=self.organization, slug=value.strip()
        ).exists():
            raise ValidationError(f"Job title with title, '{value}' not found.")
        return value

    def validate_division(self, value):
        if not OrganizationDivision.objects.filter(
            organization=self.organization, slug=value.strip()
        ).exists():
            raise ValidationError(
                f"Organization Division with name, '{value}' not found."
            )
        return value

    def validate_branch(self, value):
        if not OrganizationBranch.objects.filter(
            organization=self.organization, slug=value.strip()
        ).exists():
            raise ValidationError(
                f"Organization Branch with name, '{value}' not found."
            )

    def validate_employment_type(self, value):
        employment_status = EmploymentStatus.objects.filter(
            organization=self.organization, slug=value.strip()
        ).first()
        if not employment_status:
            raise ValidationError(f"Employment status with title, '{value}' not found.")
        if employment_status.is_contract and not self.initial_data.get("end_date"):
            raise ValidationError(
                f"Experience end date for contracted employees is required."
            )
        return value

    def validate_employment_level(self, value):
        if not EmploymentLevel.objects.filter(
            organization=self.organization, slug=value.strip()
        ).exists():
            raise ValidationError(f"Employment level with title, '{value}' not found.")
        return value

    def validate_change_type(self, value):
        if not ChangeType.objects.filter(
            organization=self.organization, slug=value.strip()
        ).exists():
            raise ValidationError(f"Change type with title, '{value}' not found.")
        return value

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        start_date = start.date() if start else None
        end_date = end.date() if end else None
        if start_date and end_date and start_date >= end_date:
            raise ValidationError({"date": "End date must be greater that start date."})
        if start_date and start_date > get_today():
            raise ValidationError({"date": "Start date cannot be greater than today in bulk import."})

        user = attrs.get("user").strip()
        user =  USER.objects.filter(Q(email=user) | Q(username=user)).first()
        current_xp = user.user_experiences.first()

        if start_date and start_date <= current_xp.start_date:
            raise ValidationError(
                {"start_date": "Start date should be greater than current experience start date."}
            )
        return attrs
