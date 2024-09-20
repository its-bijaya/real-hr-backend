from django.db import transaction

from irhrs.payroll.models import Heading, PackageHeading


def fix_advance_salary_deduction_heading():
    """
    Patch to change type of advance salary deduction Type2Cnst and fix ordering
    of the heading
    """

    for heading in Heading.objects.filter(name='Advance Salary Deduction'):
        print("Changing heading Advance Salary Deduction of", heading.organization,
              "of order", heading.order, end=" ")
        heading.type = 'Type2Cnst'
        heading.duration_unit = None
        heading.order = Heading.get_next_heading_order(heading.organization.slug)
        heading.rules = '[{"rule": "0"}]'
        heading.is_hidden = True
        heading.save()
        print("to order", heading.order, ".")

    PackageHeading.is_used_package_heading = False
    for p_heading in PackageHeading.objects.filter(heading__name='Advance Salary Deduction'):
        print("Changing heading Advance Salary Deduction of", p_heading,
              "of order", p_heading.order, end=" ")
        p_heading.type = 'Type2Cnst'
        p_heading.duration_unit = None
        p_heading.rules = '[{"rule": "0"}]'
        p_heading.save()
        print("to order", heading.order, ".")


with transaction.atomic():
    fix_advance_salary_deduction_heading()
