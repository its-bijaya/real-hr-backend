from copy import deepcopy
from datetime import timedelta
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Q
import openpyxl
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from irhrs.core.mixins.viewset_mixins import (
    OrganizationCommonsMixin,
    OrganizationMixin,
)
from irhrs.core.utils.common import get_today
from irhrs.core.utils.excel import ExcelDict
from irhrs.hris.models.onboarding_offboarding import ChangeType
from irhrs.notification.utils import notify_organization
from irhrs.organization.models.branch_and_division import OrganizationDivision, OrganizationBranch
from irhrs.organization.models.employment import (
    EmploymentJobTitle,
    EmploymentLevel,
    EmploymentStatus,
)
from irhrs.permission.constants.permissions import HRIS_IMPORT_EMPLOYEE_PERMISSION, HRIS_PERMISSION
from irhrs.users.api.v1.permissions import UserExperienceImportPermission
from irhrs.users.api.v1.serializers.import_experience import (
    UserExperienceImportSerializer,
)
from irhrs.users.api.v1.utils import UserImportBase

USER = get_user_model()


class UserExperienceImportViewSet(OrganizationMixin, OrganizationCommonsMixin, ViewSet):
    permission_classes = [UserExperienceImportPermission]
    fields = [
        "user",
        "start_date",
        "end_date",
        "job_title",
        "branch",
        "division",
        "employment_type",
        "employment_level",
        "employment_step",
        "change_type",
    ]
    values = [
        "example@email.com",
        "YYYY-MM-DD",
        None,
        "department-head",
        "ktm-branch",
        "tech-department",
        "part-time",
        "support-staffs",
        3,
        "promotion-2",
    ]

    def create(self, request, *args, **kwargs):
        context = {"request": request, "organization": self.get_organization()}
        serializer = UserExperienceImportSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        excel_update_file = serializer.validated_data["excel_file"]
        workbook = openpyxl.load_workbook(excel_update_file)
        excel_dict = ExcelDict(workbook)
        for user, fields in excel_dict.items():
            self.save_user_experience(user, fields)
        notify_organization(
            text=('User Experience Import Sucessfully.'),
            action=self.organization,
            organization=self.organization,
            url=f'/admin/{self.organization.slug}/hris/employees/import',
            permissions=[
                HRIS_PERMISSION,
                HRIS_IMPORT_EMPLOYEE_PERMISSION
            ]
        )
        return Response("Successfully uploaded user experience")

    @staticmethod
    def get_date(dt):
        return dt and dt.date()

    def save_user_experience(self, user, data):
        # directly using get here, because the data has
        # already been validated prior to this.

        user = USER.objects.filter(Q(email=user.strip()) | Q(username=user.strip())).first()
        current_experience = user.user_experiences.first()
        current_experience.is_current = False
        new_experience = deepcopy(current_experience)
        new_experience.id = None
        new_experience.is_current = True
        new_experience.start_date = self.get_date(data.get("start_date")) or get_today()
        current_experience.end_date = new_experience.start_date - timedelta(days=1)
        new_experience.end_date = self.get_date(data.get("end_date"))
        user_detail = user.detail
        organization = self.organization
        employment_step = data.get("employment_step")
        if employment_step:
            new_experience.current_step = employment_step

        job_title = data.get("job_title")
        if job_title:
            new_job_title = EmploymentJobTitle.objects.get(
                organization=organization, slug=job_title.strip()
            )
            new_experience.job_title = new_job_title
            user_detail.job_title = new_job_title

        division = data.get("division")
        if division:
            new_division = OrganizationDivision.objects.get(
                organization=organization, slug=division.strip()
            )
            new_experience.division = new_division
            user_detail.division = new_division

        employment_status = data.get("employment_type")

        branch = data.get("branch")
        if branch:
            new_branch = OrganizationBranch.objects.get(
                organization=organization, slug=branch.strip()
            )
            new_experience.branch = new_branch
            user_detail.branch = new_branch

        if employment_status:
            new_employment_status = EmploymentStatus.objects.get(
                organization=organization, slug=employment_status.strip()
            )
            new_experience.employment_status = new_employment_status
            user_detail.employment_status = new_employment_status

        employment_level = data.get("employment_level")
        if employment_level:
            new_employment_level = EmploymentLevel.objects.get(
                organization=organization, slug=employment_level.strip()
            )
            new_experience.employee_level = new_employment_level
            user_detail.employment_level = new_employment_level

        change_type = data.get("change_type")
        if change_type:
            new_experience.change_type = ChangeType.objects.get(
                organization=organization, slug=change_type.strip()
            )
        current_experience.save()
        new_experience.save()
        user_detail.save()

    @action(methods=["get"], detail=False, url_path="sample")
    def get_sample(self, request, *args, **kwargs):
        workbook = openpyxl.Workbook()
        ws = workbook.active
        ws.append(self.fields)
        ws.append(self.values)
        self.add_validators(ws, workbook=workbook)
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = "attachment; filename=sample.xlsx"
        workbook.save(response)
        return response

    def add_validators(self, ws, workbook):
        key_qs = {
            'job_title': EmploymentJobTitle.objects.filter(
                organization=self.organization),
            'division': OrganizationDivision.objects.filter(is_archived=False,
                                                                 organization=self.organization),
            'branch': OrganizationBranch.objects.filter(is_archived=False,
                                                            organization=self.organization),
            'employment_type': EmploymentStatus.objects.filter(is_archived=False,
                                                                    organization=self.organization),
            'employment_level': EmploymentLevel.objects.filter(is_archived=False,
                                                                    organization=self.organization),
            'change_type':
                ChangeType.objects.filter(organization=self.organization),
        }
        for key in key_qs:
            ws.add_data_validation(self.get_dv(key, key_qs, workbook))

        return ws

    def get_dv(self, fieldname, key_qs, workbook):
        qs = key_qs[fieldname]
        index = UserImportBase.get_index(fieldname, self.fields)
        return UserImportBase.get_dv_for_qs(qs, index, fieldname, workbook)
