from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.payroll import REQUESTED, PENDING, FIRST, EMPLOYEE, SUPERVISOR, SECOND
from irhrs.core.utils.common import get_today
from irhrs.hris.models import UserResignation, UserResignationApproval
from irhrs.users.models import UserSupervisor


class TestUserResignationViewSet(RHRSAPITestCase):
    users = (
        ('admin@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
        ('supervisor@email.com', 'password', 'Male'),
        ('supervisortwo@email.com', 'password', 'Male'),
        ('supervisorthree@email.com', 'password', 'Male'),
    )
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.resignation = UserResignation.objects.create(
            employee=self.created_users[1],
            recipient=self.created_users[2],
            release_date=get_today(),
            remarks="Resignation",
            reason="Terminated",
            status=REQUESTED
        )
        UserResignationApproval.objects.create(
            resignation=self.resignation,
            user=self.created_users[0],
            level=1,
            status=PENDING
        )
        supervisors = [
            UserSupervisor(
                user=self.created_users[1],
                supervisor=self.created_users[2],
                authority_order=1,
                approve=True, deny=True, forward=False
            ),
            UserSupervisor(
                user=self.created_users[1],
                supervisor=self.created_users[3],
                authority_order=2,
                approve=True, deny=True, forward=False
            ),
            UserSupervisor(
                user=self.created_users[1],
                supervisor=self.created_users[4],
                authority_order=3,
                approve=True, deny=True, forward=False
            )
        ]
        UserSupervisor.objects.bulk_create(supervisors)

    @property
    def url(self):
        return reverse(
            'api_v1:hris:user-resignation-approve',
            kwargs={
                'organization_slug': self.organization.slug,
                'pk': self.resignation.id
            }
        ) + '?as=approver'

    @property
    def payload(self):
        return {
            "remarks": "Approve resignation",
            "add_signature": False
        }

    def test_user_resignation_approve(self):
        self.client.force_login(self.created_users[2])
        response = self.client.post(
            self.url,
            data=self.payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('message'),
            "Approved Request."
        )

    @property
    def setting_payload(self):
        return{
            "approvals":
                [
                    {
                        "approve_by": SUPERVISOR,
                        "supervisor_level": SECOND,
                        "employee": None,
                        "approval_level": 2,
                        "organization": self.organization.id
                    },
                    {
                        "approve_by": EMPLOYEE,
                        "supervisor_level": FIRST,
                        "employee": self.created_users[2].id
                    }
                ]
        }

    @property
    def setting_payload1(self):
        return {
            "approvals": [
                {
                    "approve_by": SUPERVISOR,
                    "supervisor_level": SECOND,
                    "employee": None,
                    "approval_level": 2,
                    "organization": self.organization.id
                },
                {
                    "approve_by": EMPLOYEE,
                    "supervisor_level": FIRST,
                    "employee": self.created_users[1].id
                }
            ]
        }

    @property
    def setting_url(self):
        return reverse(
            'api_v1:hris:resignation-setting-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    @property
    def setting_get_url(self):
        return reverse(
            'api_v1:hris:resignation-setting-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def test_user_resignation_settings(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.setting_url,
            self.setting_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            len(response.json().get('approvals')),
            2
        )
        response = self.client.post(
            self.setting_url,
            self.setting_payload1,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            len(response.json().get('approvals')),
            2
        )
        response = self.client.get(
            self.setting_get_url,
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            response.json().get('count'),
            2
        )
