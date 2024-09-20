import json
import os

from django.conf import settings

from irhrs.payroll.models import EmployeePayrollComment, EmployeePayroll


def create_dump_of_employee_comment():
    with open(os.path.join(settings.PROJECT_DIR, 'comment.json')) as f:
        comments = json.load(f)
        EmployeePayrollComment.objects.bulk_create([
            EmployeePayrollComment(
                employee_payroll_id=item.get('id'),
                commented_by_id=item.get('employee'),
                remarks=item.get('acknowledge_remarks')
            ) for item in comments]
        )
    EmployeePayroll.objects.filter(
        acknowledgement_status="Acknowledged with Remarks"
    ).update(acknowledgement_status="Acknowledged")
    os.remove(os.path.join(settings.PROJECT_DIR, 'comment.json'))
