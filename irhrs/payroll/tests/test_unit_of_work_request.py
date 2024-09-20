from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase, FileHelpers
from irhrs.core.constants.payroll import REQUESTED, APPROVED, CONFIRMED, FORWARDED, DENIED
from irhrs.payroll.models import UnitOfWorkRequest
from irhrs.payroll.models.unit_of_work_settings import UserOperationRate
from irhrs.payroll.tests.factory import OperationFactory, OperationCodeFactory, \
    OperationRateFactory

USER = get_user_model()


class UnitOfWorkRequestTest(FileHelpers, RHRSAPITestCase):
    users = (
        ('hr@email.com', 'password', 'Female'),
        ('supervisorone@email.com', 'password', 'Female'),
        ('supervisortwo@email.com', 'password', 'Female'),
        ('normal@email.com', 'password', 'Female'),
    )
    organization_name = "Organization"

    def setUp(self):
        super().setUp()
        self.supervisor1 = USER.objects.get(email='supervisorone@email.com')
        self.supervisor2 = USER.objects.get(email='supervisortwo@email.com')
        self.normal = USER.objects.get(email='normal@email.com')
        operation = OperationFactory(organization=self.organization)
        operation_code = OperationCodeFactory(organization=self.organization)
        self.rate = OperationRateFactory(
            operation=operation,
            operation_code=operation_code
        )

        # Assigning user to unit of work
        UserOperationRate.objects.create(
            user=self.normal,
            rate=self.rate
        )

        self.list_url = reverse(
            'api_v1:payroll:unit-of-work-request-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def get_action_url(self, pk, action):
        return reverse(
            'api_v1:payroll:unit-of-work-request-perform-action',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': pk,
                'action_performed': action
            }
        )

    def get_request(self, status=REQUESTED):
        return UnitOfWorkRequest.objects.create(
            rate=self.rate,
            recipient=self.supervisor1,
            user=self.normal,
            quantity=3,
            status=status
        )

    def get_request_data_for_normal_user(self):
        return {
            "rate": self.rate.id,
            "quantity": 2,
            "attachment": self.get_image(),
            "remarks": "Remarks Here"
        }

    def get_request_data_for_supervisor(self, status=APPROVED):
        return {
            "rate": self.rate.id,
            "quantity": 2,
            "attachment": self.get_image(),
            "remarks": "Remarks Here",
            "status": status,
            "user": self.normal.id
        }

    def get_request_data_for_hr(self):
        return self.get_request_data_for_supervisor(status=CONFIRMED)

    def test_request_by_normal_user(self):
        self.client.force_login(self.normal)

        with patch('irhrs.users.models.user.User.'
                   'first_level_supervisor_including_bot',
                   self.supervisor1):
            data = self.get_request_data_for_normal_user()
            response = self.client.post(self.list_url, data)
            self.assertEqual(response.status_code, 201)
            pk = response.data.get('id')

            instance = UnitOfWorkRequest.objects.get(pk=pk)
            self.assertEqual(instance.rate.id, data["rate"])
            self.assertEqual(instance.quantity, data["quantity"])
            self.assertIsNotNone(instance.attachment)
            self.assertEqual(instance.remarks, data['remarks'])
            self.assertEqual(instance.recipient, self.supervisor1)
            self.assertEqual(instance.status, REQUESTED)

    def test_request_by_supervisor(self):
        data = self.get_request_data_for_supervisor()
        self.client.force_login(self.supervisor1)

        with patch(
            'irhrs.users.models.user.User.'
            'first_level_supervisor_including_bot',
            self.supervisor1
        ), patch(
            'irhrs.core.utils.subordinates.authority_exists',
            return_value=True
        ):
            response = self.client.post(self.list_url+"?as=supervisor", data)
            self.assertEqual(response.status_code, 201)

            pk = response.data.get('id')
            instance = UnitOfWorkRequest.objects.get(pk=pk)

            self.assertEqual(instance.recipient, self.supervisor1)
            self.assertEqual(instance.status, APPROVED)
            self.assertEqual(instance.rate.id, data["rate"])
            self.assertEqual(instance.remarks, data['remarks'])
            self.assertEqual(instance.quantity, data["quantity"])
            self.assertIsNotNone(instance.attachment)

    def test_request_by_supervisor_without_authority_to_approve(self):
        data = self.get_request_data_for_supervisor()
        self.client.force_login(self.supervisor1)

        with patch(
            'irhrs.users.models.user.User.'
            'first_level_supervisor_including_bot',
            self.supervisor1
        ), patch(
            'irhrs.core.utils.subordinates.authority_exists',
            return_value=False
        ):
            response = self.client.post(self.list_url+"?as=supervisor", data)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.data.get('non_field_errors'),
                ['You are not allowed to approve the request.']
            )

    def test_request_by_second_level_supervisor(self):
        data = self.get_request_data_for_supervisor()
        self.client.force_login(self.supervisor2)

        # second level supervisor can not request
        with patch(
            'irhrs.users.models.user.User.'
            'first_level_supervisor_including_bot',
            self.supervisor1
        ), patch(
            'irhrs.core.utils.subordinates.authority_exists',
            return_value=True
        ):
            response = self.client.post(self.list_url+"?as=supervisor", data)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(
                response.data.get('user'),
                ['User is not immediate subordinate.']
            )

    def test_request_by_hr(self):
        data = self.get_request_data_for_hr()

        self.client.force_login(self.admin)
        with patch(
            'irhrs.users.models.user.User.'
            'first_level_supervisor_including_bot',
            self.supervisor1
        ):
            response = self.client.post(self.list_url + "?as=hr", data)

        self.assertEqual(response.status_code, 201)

        pk = response.data.get('id')
        instance = UnitOfWorkRequest.objects.get(pk=pk)

        self.assertEqual(instance.recipient, self.supervisor1)
        self.assertEqual(instance.status, CONFIRMED)
        self.assertEqual(instance.rate.id, data["rate"])
        self.assertEqual(instance.remarks, data['remarks'])
        self.assertEqual(instance.quantity, data["quantity"])
        self.assertIsNotNone(instance.attachment)

    def test_request_approve_deny_by_supervisor(self):
        # valid conditions
        for action in ['approve', 'deny']:
            for status in [REQUESTED, FORWARDED]:
                request = self.get_request(status=status)
                url = self.get_action_url(request.id, action)
                self.client.force_login(self.supervisor1)
                with patch(
                    'irhrs.core.utils.subordinates.authority_exists',
                    return_value=True
                ):
                    response = self.client.post(
                        url+"?as=supervisor",
                        data={"remarks": action}
                    )
                    self.assertEqual(
                        response.status_code,
                        200,
                        msg=f"Should be allowed to {action} from {status}")

                    request.refresh_from_db()
                    self.assertEqual(
                        request.status,
                        {"approve": APPROVED, "deny": DENIED}[action]
                    )

    def test_request_approve_by_supervisor_without_authority(self):
        request = self.get_request()
        url = self.get_action_url(request.id, 'approve')
        self.client.force_login(self.supervisor1)
        with patch(
            'irhrs.core.utils.subordinates.authority_exists',
            return_value=False
        ):
            response = self.client.post(
                url + "?as=supervisor",
                data={"remarks": "approved"}
            )
            self.assertEqual(response.status_code, 403)

    def test_approve_deny_by_supervisor_from_denied_approved_confirmed(self):
        # not allowed conditions
        for action in ['approve', 'deny', 'confirm']:
            for status in [APPROVED, DENIED, CONFIRMED]:
                request = self.get_request(status=status)
                url = self.get_action_url(request.id, 'approve')
                self.client.force_login(self.supervisor1)
                with patch(
                    'irhrs.core.utils.subordinates.authority_exists',
                    return_value=True
                ):
                    response = self.client.post(
                        url+"?as=supervisor",
                        data={"remarks": action}
                    )
                    self.assertEqual(
                        response.status_code,
                        403,
                        msg=f"Should not be allowed to {action} from {status}")

    def test_forward(self):
        action = 'forward'
        for status in [REQUESTED, FORWARDED]:
            request = self.get_request(status=status)
            url = self.get_action_url(request.id, action)
            self.client.force_login(self.supervisor1)
            with patch(
                'irhrs.core.utils.subordinates.authority_exists',
                return_value=True
            ), patch(
                'irhrs.core.utils.subordinates.get_next_level_supervisor',
                return_value=self.supervisor2
            ):
                response = self.client.post(
                    url + "?as=supervisor",
                    data={"remarks": action}
                )
                self.assertEqual(
                    response.status_code,
                    200,
                    msg=f"Should be allowed to {action} from {status}"
                )

                request.refresh_from_db()
                self.assertEqual(
                    request.status,
                    FORWARDED
                )
                self.assertEqual(
                    request.recipient,
                    self.supervisor2
                )

    def test_forward_with_no_forwarded_to(self):
        action = 'forward'
        for status in [REQUESTED, FORWARDED]:
            request = self.get_request(status=status)
            url = self.get_action_url(request.id, action)
            self.client.force_login(self.supervisor1)
            with patch(
                'irhrs.core.utils.subordinates.authority_exists',
                return_value=True
            ), patch(
                'irhrs.core.utils.subordinates.get_next_level_supervisor',
                return_value=None
            ):
                response = self.client.post(
                    url + "?as=supervisor",
                    data={"remarks": action}
                )
                self.assertEqual(
                    response.status_code,
                    400,
                )

    def test_forward_by_hr(self):
        request = self.get_request(status=REQUESTED)
        url = self.get_action_url(request.id, 'forward')
        self.client.force_login(self.admin)
        with patch(
            'irhrs.core.utils.subordinates.authority_exists',
            return_value=True
        ), patch(
            'irhrs.core.utils.subordinates.get_next_level_supervisor',
            return_value=None
        ):
            response = self.client.post(
                url + "?as=hr",
                data={"remarks": 'Forwarded'}
            )
            self.assertEqual(
                response.status_code,
                403,
            )

    def test_valid_actions_by_hr(self):
        action_valid_status_map = {
            "approve": [REQUESTED, FORWARDED],
            "deny": [REQUESTED, FORWARDED, APPROVED],
            "confirm": [REQUESTED, FORWARDED, APPROVED]
        }

        self.client.force_login(self.admin)
        for action, allowed_status in action_valid_status_map.items():
            for status in allowed_status:
                request = self.get_request(status=status)
                url = self.get_action_url(request.id, action)

                response = self.client.post(
                    url+"?as=hr",
                    data={"remarks": action}
                )
                self.assertEqual(
                    response.status_code,
                    200,
                    msg=f"Should be allowed to {action} from {status}")

                request.refresh_from_db()
                self.assertEqual(
                    request.status,
                    {
                        "approve": APPROVED,
                        "deny": DENIED,
                        'confirm': CONFIRMED
                    }[action]
                )

    def test_invalid_actions_by_hr(self):
        action_invalid_status_map = {
            "approve": [DENIED, CONFIRMED, APPROVED],
            "deny": [DENIED, CONFIRMED],
            "confirm": [DENIED]
        }
        for action, invalid_status_list in action_invalid_status_map.items():
            for status in invalid_status_list:
                request = self.get_request(status=status)
                url = self.get_action_url(request.id, action)
                self.client.force_login(self.admin)
                response = self.client.post(
                    url + "?as=hr",
                    data={"remarks": action}
                )
                self.assertEqual(
                    response.status_code,
                    403,
                    msg=f"Should not be allowed to {action} from {status}"
                )
