"""@irhrs_docs

DEPENDENCY MAPPING
==================

Mapping of dependencies for inter-app communication

Eg.

.. code-block:: python

    DEPENDENCIES = {
        "name_of_dependency": ("app_name", "path_to_dependency", "return value if not found"
    }

*Note: currently this only support functions.*
"""
DEPENDENCIES = {

    'irhrs.attendance.utils.payroll.get_adjustment_request_status_summary': (
        'irhrs.attendance',
        'irhrs.attendance.utils.payroll.get_adjustment_request_status_summary',
        {
            "pending": 0,
            "forwarded": 0,
            "approved": 0,
        }
    ),

    'irhrs.attendance.utils.payroll.get_attendance_aprroval_request_summary': (
        'irhrs.attendance',
        'irhrs.attendance.utils.payroll.get_attendance_aprroval_request_summary',
        {
            "pending": 0,
            "forwarded": 0,
            "approved": 0,
        }
    ),
    'irhrs.attendance.utils.payroll.get_overtime_request_status_summary': (
        'irhrs.attendance',
        'irhrs.attendance.utils.payroll.get_overtime_request_status_summary',
        {
            "pending": 0,
            "forwarded": 0,
            "approved": 0,
            "confirmed": 0,
        }
    ),

    'irhrs.leave.utils.payroll.get_leave_request_status_summary': (
        'irhrs.leave',
        'irhrs.leave.utils.payroll.get_leave_request_status_summary',
        {
            "pending": 0,
            "forwarded": 0,
            "approved": 0,
        }
    ),

    'irhrs.hris.utils.payroll.get_employment_review_status_summary': (
        'irhrs.hris',
        'irhrs.hris.utils.payroll.get_employment_review_status_summary',
        []
    ),
    'irhrs.payroll.utils.helpers.get_last_payroll_generated_date': (
        'irhrs.payroll',
        'irhrs.payroll.utils.helpers.get_last_payroll_generated_date',
        None
    ),
    'irhrs.payroll.utils.helpers.get_last_payroll_generated_date_excluding_simulated': (
        'irhrs.payroll',
        'irhrs.payroll.utils.helpers.get_last_payroll_generated_date_excluding_simulated',
        None
    ),
    'irhrs.payroll.utils.helpers.get_advance_salary_stats': (
        'irhrs.payroll',
        'irhrs.payroll.utils.helpers.get_advance_salary_stats',
        {}
    ),
    'irhrs.payroll.utils.helpers.get_advance_salary': (
        'irhrs.payroll',
        'irhrs.payroll.utils.helpers.get_advance_salary',
        None
    ),
    'irhrs.reimbursement.utils.helper.get_reimbursement_stats': (
        'irhrs.reimbursement',
        'irhrs.reimbursement.utils.helper.get_reimbursement_stats',
        {}
    ),
    'irhrs.reimbursement.utils.helper.get_reimbursement': (
        'irhrs.reimbursement',
        'irhrs.reimbursement.utils.helper.get_reimbursement',
        None
    ),
    'irhrs.hris.utils.helper.get_exit_interview_stats': (
        'irhrs.hris',
        'irhrs.hris.utils.helper.get_exit_interview_stats',
        {}
    ),
    'irhrs.hris.utils.helper.get_exit_interview': (
        'irhrs.hris',
        'irhrs.hris.utils.helper.get_exit_interview',
        None
    ),
    'irhrs.hris.utils.helper.get_resignation_stats': (
        'irhrs.hris',
        'irhrs.hris.utils.helper.get_resignation_stats',
        {}
    ),
    'irhrs.hris.utils.helper.get_resignation': (
        'irhrs.hris',
        'irhrs.hris.utils.helper.get_resignation',
        None
    ),
    'irhrs.leave.utils.helper.get_leave_request_stats': (
        'irhrs.leave',
        'irhrs.leave.utils.helper.get_leave_request_stats',
        {}
    ),
    'irhrs.leave.utils.helper.get_leave_request': (
        'irhrs.leave',
        'irhrs.leave.utils.helper.get_leave_request',
        None
    )
}
