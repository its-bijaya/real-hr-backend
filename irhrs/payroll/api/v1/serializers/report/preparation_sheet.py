import copy
from django.conf import settings

from django.utils.functional import cached_property

from irhrs.core.utils.dependency import get_dependency
from irhrs.payroll.utils.exceptions import CustomValidationError
from datetime import timedelta

class PreparationSheetOverview():
    def __init__(
        self,
        start_date,
        end_date,
        simulated_from,
        organization_slug,
        employee_filter,
        exclude_filter,
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.simulated_from=simulated_from
        self.organization_slug = organization_slug
        self.employee_filter = employee_filter or dict()
        self.exclude_filter = exclude_filter or dict()
        if self.simulated_from:
            self.end_date = self.simulated_from - timedelta(days=1)

    @cached_property
    def get_adjustment_requests_status_summary(self):
        # return {
        #     'pending': 0,
        #     'forwarded': 0,
        #     'approved': 0
        # }
        fn = get_dependency(
            'irhrs.attendance.utils.payroll.get_adjustment_request_status_summary')[0]
        exclude_filter = copy.deepcopy(self.exclude_filter)
        exclude_filter['sender_id__in'] = exclude_filter.pop('id__in', [])

        return fn(
            self.organization_slug,
            self.start_date,
            self.end_date,
            self.employee_filter,
            exclude_filter
        )

    @cached_property
    def get_attendance_aprroval_request_summary(self):
        fn = get_dependency(
            'irhrs.attendance.utils.payroll.get_attendance_aprroval_request_summary')[0]
        exclude_filter = copy.deepcopy(self.exclude_filter)
        exclude_filter['timesheet__timesheet_user_id__in'] = exclude_filter.pop('id__in', [])
        return fn(
            self.organization_slug,
            self.start_date,
            self.end_date,
            self.employee_filter,
            exclude_filter
        )

    @cached_property
    def get_leave_requests_status_summary(self):
        # return {
        #     'pending': 0,
        #     'forwarded': 0,
        #     'approved': 0
        # }
        fn = get_dependency(
            'irhrs.leave.utils.payroll.get_leave_request_status_summary')[0]
        exclude_filter = copy.deepcopy(self.exclude_filter)
        exclude_filter['user_id__in'] = exclude_filter.pop('id__in', [])
        return fn(
            self.organization_slug,
            self.start_date,
            self.end_date,
            self.employee_filter,
            exclude_filter
        )

    @cached_property
    def get_employment_review_detail(self):
        # return {
        #     'promoted': 0,
        #     'demoted': 0,
        #     'transferred': 0,
        #     'terminated': 0
        # }
        fn = get_dependency(
            'irhrs.hris.utils.payroll.get_employment_review_status_summary')[0]
        exclude_filter = copy.deepcopy(self.exclude_filter)
        exclude_filter['employee_id__in'] = exclude_filter.pop('id__in', [])
        return fn(
            self.organization_slug,
            self.start_date,
            self.end_date,
            self.employee_filter,
            self.exclude_filter
        )

    @cached_property
    def get_overtime_request_status_summary(self):
        fn = get_dependency(
            'irhrs.attendance.utils.payroll.get_overtime_request_status_summary')[0]
        exclude_filter = copy.deepcopy(self.exclude_filter)
        exclude_filter['overtime_entry__user_id__in'] = exclude_filter.pop('id__in', [])
        return fn(
            self.organization_slug,
            self.start_date,
            self.end_date,
            self.employee_filter,
            exclude_filter
        )

    def get_valid_employees_with_clean_request(
            self, employees, exclude_not_eligible, exclude_filter):
        # Implement the logic of showing the data
        overtime_request = settings.GENERATE_PAYROLL_EVEN_IF_OVERTIME_EXISTS
        valid = not any(
            [
                self.get_adjustment_requests_status_summary.get('pending'),
                self.get_adjustment_requests_status_summary.get('forwarded'),
                self.get_leave_requests_status_summary.get('pending'),
                self.get_leave_requests_status_summary.get('forwarded'),
                self.get_attendance_aprroval_request_summary.get('pending'),
                self.get_overtime_request_status_summary_using_setting('pending_users') + \
                self.get_overtime_request_status_summary_using_setting('forwarded_users') + \
                self.get_overtime_request_status_summary_using_setting('approved_users')
            ]
        )

        if not valid and exclude_not_eligible:
            not_eligible_users = \
                self.get_adjustment_requests_status_summary.get('pending_users') + \
                self.get_adjustment_requests_status_summary.get('forwarded_users') + \
                self.get_leave_requests_status_summary.get('pending_users') + \
                self.get_leave_requests_status_summary.get('forwarded_users') + \
                self.get_attendance_aprroval_request_summary.get('pending_users') + \
                self.get_overtime_request_status_summary_using_setting('pending_users') + \
                self.get_overtime_request_status_summary_using_setting('forwarded_users') + \
                self.get_overtime_request_status_summary_using_setting('approved_users')
            exclude_filter['id__in'] = [
                emp.get('id') for emp in not_eligible_users]
            employees = employees.exclude(**exclude_filter)
        if not (valid or exclude_not_eligible):
            raise CustomValidationError(error_dict={
                'adjustment_requests_summary': self.get_adjustment_requests_status_summary,
                'leave_requests_summary': self.get_leave_requests_status_summary,
                'employment_review': self.get_employment_review_detail,
                'attendance_request': self.get_attendance_aprroval_request_summary,
                'overtime_request': self.get_overtime_request_status_summary if not overtime_request else None,
            })
        return employees

    def get_overtime_request_status_summary_using_setting(self, status: str):
        overtime_request = settings.GENERATE_PAYROLL_EVEN_IF_OVERTIME_EXISTS
        status_summary = self.get_overtime_request_status_summary.get(status)
        if status_summary and not overtime_request:
            return status_summary
        return []
