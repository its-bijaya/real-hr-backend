from django.db import transaction

from irhrs.payroll.models import UserExperiencePackageSlot
from irhrs.payroll.utils.calculator import create_package_rows
from irhrs.payroll.utils.helpers import InvalidVariableTypeOperation


def create_report_row_experience_package():
    experience_package_slots = UserExperiencePackageSlot.objects.all()

    for slot in experience_package_slots:
        try:
            create_package_rows(slot)
        except InvalidVariableTypeOperation:
            print(f"Invalid Package rule for package id {slot.package.id} name  {slot.package.name}")


with transaction.atomic():
    create_report_row_experience_package()
