import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from irhrs.attendance.api.v1.tests.factory import(
    IndividualAttendanceSettingFactory, IndividualUserShiftFactory, WorkShiftFactory
)
from irhrs.attendance.models.travel_attendance import TravelAttendanceRequest, TravelAttendanceSetting
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.constants.payroll import SUPERVISOR
from irhrs.attendance.constants import APPROVED
from irhrs.reimbursement.api.v1.tests.factory import(
    ExpenseApprovalSettingFactory, ReimbursementSettingFactory,
    AdvanceExpenseRequestFactory
)
from irhrs.reimbursement.models.reimbursement import(
    AdvanceExpenseRequestApproval, TravelRequestFromAdvanceRequest, TravelRequestFromAdvanceRequest
) 
from irhrs.users.models.supervisor_authority import UserSupervisor
from datetime import datetime
from rest_framework import status
from irhrs.reimbursement.utils.helper import convert_to_iso_format
from irhrs.common.api.tests.common import FileHelpers

User = get_user_model()


class TestTravelRequestMergeWithExpenseRequest(RHRSTestCaseWithExperience):
    organization_name = "Aayulogic"

    users = [
        ("admin@gmail.com", "admin", "Male", "Hr"),
        ("supervisorone@gmail.com", "one", "Male", "Developer"),
        ("supervisortwo@gmail.com", "two", "Male", "Developer"),
        ("user@gmail.com", "user", "Male", "Trainee"),
        ("normal@gmail.com", "normal", "Male", "Trainee")
    ]

    def setUp(self):
        super().setUp()
        self.users = User.objects.filter(detail__organization=self.organization)
        ReimbursementSettingFactory(organization=self.organization)
        for user in self.users[2:]:

            UserSupervisor.objects.create(
                user=user,
                supervisor=self.created_users[2],
                authority_order=1
            )
            individual_setting = IndividualAttendanceSettingFactory(
                user=user
            )
            IndividualUserShiftFactory(
                individual_setting=individual_setting,
                shift=WorkShiftFactory(organization=self.organization)
            )

        TravelAttendanceSetting.objects.create(
            organization=self.organization,
            can_apply_in_offday=True,
            can_apply_in_holiday=True
        )
        
        user = self.created_users[2]
        user.signature.save('signature_u.jpg', FileHelpers.get_image())
        user.save()

    def expense_with_travel_payload(self, start, end):
     return {
            "reason": "Travel",
            "type": "Travel",
            "detail": [{
                "detail_type": "Per diem",
                "departure_time": datetime.now(),
                "departure_place": "Kathmandu",
                "arrival_time": datetime.now(),
                "arrival_place": "pokhara",
                "rate_per_day": "500",
                "day": "1"
            }],
            "send_travel_request": "true",
            "travel_request[start]": start,
            "travel_request[start_time]": "17:00",
            "travel_request[end]": end,
            "travel_request[end_time]": "18:00"
        }

    @property
    def advance_expense_request_url(self):
        return reverse(
            f'api_v1:reimbursement:advance-expense-request-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) +'?expense_type=travel'

    def create_supervisor_approval_setting(self):
        ExpenseApprovalSettingFactory(
            organization=self.organization,
            approve_by=SUPERVISOR,
            supervisor_level="First",
            approval_level=1
        )
    
    # Test for advance request with travel request where two users requesting same request for same date.
    def test_advance_expense_request_and_travel_request(self):
        self.client.force_login(self.created_users[3])
        self.create_supervisor_approval_setting()

        response = self.client.post(
            self.advance_expense_request_url,
            self.expense_with_travel_payload("2023-03-01", "2023-03-03"),
            format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.json()['status'], 'Requested'
        )
        self.assertEqual(
            response.json()['employee']['full_name'], 'user user'
        )
        self.client.logout()

        self.client.force_login(self.created_users[4])
        response = self.client.post(
            self.advance_expense_request_url,
            self.expense_with_travel_payload("2023-03-01", "2023-03-03"),
            format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.json()['status'], 'Requested'
        )
        self.assertEqual(
            response.json()['employee']['full_name'], 'normal normal'
        )
        
    def test_invalid_travel_request_with_advance_expense_request(self):
        self.client.force_login(self.created_users[3])
        self.create_supervisor_approval_setting()
        
        response = self.client.post(
            self.advance_expense_request_url,
            self.expense_with_travel_payload("2023-03-08", "2023-03-06"),
            format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.json()['start'], ['Start Date must be smaller than End Date.']
        )

    def test_same_travel_request(self):
        self.client.force_login(self.created_users[3])
        self.create_supervisor_approval_setting()
        advance_detail = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['detail']
        data = json.dumps(advance_detail, default=convert_to_iso_format)

        advance_request = AdvanceExpenseRequestFactory(
            employee = self.created_users[3],
            detail = data
        )
    
        # Requesting travel request for date 2023-03-01 to 2023-03-03
        travel_request = TravelRequestFromAdvanceRequest.objects.create(
            advance_expense_request = advance_request,
            start = "2023-03-01",
            start_time = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['travel_request[start_time]'],
            end = "2023-03-03",
            end_time = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['travel_request[end_time]']
        )

        same_advance_request = AdvanceExpenseRequestFactory(
            employee = self.created_users[3],
            detail = data
        )
        # Requesting travel request for date 2023-03-02 which is already in requested state.
        same_travel_request = TravelRequestFromAdvanceRequest.objects.create(
            advance_expense_request = same_advance_request,
            start = "2023-03-02",
            start_time = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['travel_request[start_time]'],
            end = "2023-03-02",
            end_time = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['travel_request[end_time]']
        )

        response = self.client.post(
            self.advance_expense_request_url,
            self.expense_with_travel_payload("2023-03-02", "2023-03-02"),
            format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            response.json()['non_field_errors'],
            ['There is Requested travel request on this range.']
        )
   
    def test_approve_expense_request(self):
        self.client.force_login(self.created_users[2])
        self.create_supervisor_approval_setting()
        advance_detail = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['detail']
        data = json.dumps(advance_detail, default=convert_to_iso_format)

        advance_request = AdvanceExpenseRequestFactory(
            employee = self.created_users[3],
            detail = data,
            add_signature = True
        )
        advance_request.recipient.add(self.created_users[2])

        AdvanceExpenseRequestApproval.objects.create(
            expense = advance_request,
            add_signature= True,
            acted_by = self.created_users[2],
            level = 1,
            status = "Pending"
        )
        TravelRequestFromAdvanceRequest.objects.create(
            advance_expense_request = advance_request,
            start = "2023-03-01",
            start_time = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['travel_request[start_time]'],
            end = "2023-03-03",
            end_time = self.expense_with_travel_payload("2023-03-01", "2023-03-03")['travel_request[end_time]'],
        )
       
        url = reverse(
            'api_v1:reimbursement:advance-expense-request-approve',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': advance_request.id
            }
        ) +'?as=approver'

        payload = {
            "add_signature": "true",
            "remarks": "approve"
        }
        response = self.client.post(
            url,
            payload,
            format="json"
        )
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.json()
        )

        self.assertEqual(
            response.json()['message'], 'Approved Advance Expense Request.'
        )
        self.assertEqual(
           TravelAttendanceRequest.objects.values_list('status', flat=True)[0],
            'Approved'
        )
        self.assertEqual(
           TravelAttendanceRequest.objects.values_list('balance', flat=True)[0],
           3
        )
    
    def test_advance_expense_request_without_travel_request(self):
        self.client.force_login(self.created_users[4])
        self.create_supervisor_approval_setting()

        payload = {
            "reason": "Travel",
            "type": "Travel",
            "detail": [{
                "detail_type": "Per diem",
                "departure_time": datetime.now(),
                "departure_place": "Kathmandu",
                "arrival_time": datetime.now(),
                "arrival_place": "pokhara",
                "rate_per_day": "500",
                "day": "1"
            }],
        }
        response = self.client.post(
            self.advance_expense_request_url,
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED
        )
        self.assertEqual(
            response.json()['status'], 'Requested'
        )
        self.assertEqual(
            response.json()['employee']['full_name'], 'normal normal'
        )
        self.assertEqual(
            response.json()['travel_request'], {}
        )

    def test_travel_attendance_request(self):
        self.client.force_login(self.created_users[4])
        self.create_supervisor_approval_setting()

        TravelAttendanceRequest.objects.create(
            start = "2023-03-01",
            end = "2023-03-03",
            start_time = "10:00",
            end_time = "5:00",
            balance = 3,
            user = self.created_users[4],
            status = APPROVED,
            recipient = self.created_users[1]
        )

        response = self.client.post(
            self.advance_expense_request_url,
            self.expense_with_travel_payload("2023-03-01", "2023-03-03"),
            format="json"
        )

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json()['non_field_errors'],
            ['There is travel attendance request on this range.']
        )
