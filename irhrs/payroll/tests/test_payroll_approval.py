from django.urls import reverse
from django.utils import timezone

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today, DummyObject
from irhrs.payroll.api.v1.serializers import PayrollSerializer
from irhrs.payroll.models import PayrollApprovalSetting, Payroll, APPROVAL_PENDING, \
    PayrollApproval, PENDING, APPROVED, REJECTED, CONFIRMED, GENERATED


class PayrollApprovalTest(RHRSAPITestCase):
    users = [
        ('admin@gmail.com', 'password', 'Male'),
        ('normal@gmail.com', 'password', 'Male'),
        ('approverone@gmail.com', 'password', 'Male'),
        ('approvertwo@gmail.com', 'password', 'Male'),
    ]
    organization_name = "Organization"

    payroll_url_name = 'api_v1:payroll:payrolls-detail'
    payroll_approval_url_name = 'api_v1:payroll:approval'

    def get_payroll_url(self, instance, mode="hr"):
        return "{}?as={}&organization__slug={}".format(
            reverse(self.payroll_url_name, kwargs={'pk': instance.id}),
            mode,
            self.organization.slug
        )

    def get_approval_url(self, instance, action):
        return reverse(
            f'{self.payroll_approval_url_name}-{action}',
            kwargs={'pk': instance.id}
        )

    def create_approval_settings(self):
        approvals = [
            PayrollApprovalSetting(
                organization=self.organization,
                approval_level=index,
                user=user
            )
            for index, user in enumerate(self.created_users[2:])
        ]
        PayrollApprovalSetting.objects.bulk_create(approvals)

    def create_payroll(self):
        return Payroll.objects.create(
            organization=self.organization,
            from_date=get_today() - timezone.timedelta(days=30),
            to_date=get_today(),
            extra_data={}
        )

    def create_payroll_approvals(self, payroll):
        payroll.status = APPROVAL_PENDING
        serializer = PayrollSerializer(instance=payroll, context={
            'request': DummyObject(
                method='PUT',
                user=self.admin
            )
        })
        serializer.create_approvals(payroll)

    def check_status(
        self,
        payroll,
        status,
        approval_pending,
        first_approval_status,
        second_approval_status
    ):
        payroll.refresh_from_db()

        first_approval_user = self.created_users[2]
        second_approval_user = self.created_users[3]
        self.assertEqual(payroll.approval_pending, approval_pending)
        self.assertEqual(payroll.status, status)

        self.assertTrue(
            PayrollApproval.objects.filter(
                payroll=payroll,
                user=first_approval_user,
                status=first_approval_status,
                approval_level=0
            ).exists()
        )

        self.assertTrue(
            PayrollApproval.objects.filter(
                payroll=payroll,
                user=second_approval_user,
                status=second_approval_status,
                approval_level=1
            ).exists()
        )

    def setUp(self):
        super().setUp()
        self.create_approval_settings()

    def test_approval_send_for_approval(self):
        payroll = self.create_payroll()

        self.client.force_login(self.admin)
        url = self.get_payroll_url(payroll)

        response = self.client.put(url, {'status': APPROVAL_PENDING})
        self.assertEqual(response.status_code, 200)

        self.check_status(
            payroll=payroll,
            status=APPROVAL_PENDING,
            approval_pending=self.created_users[2],
            first_approval_status=PENDING,
            second_approval_status=PENDING
        )

    def test_approve(self):
        payroll = self.create_payroll()
        self.create_payroll_approvals(payroll)

        self.client.force_login(self.created_users[2])
        url = self.get_approval_url(payroll, "approve")
        response = self.client.post(url, {'remarks': 'Approved'})
        self.assertEqual(response.status_code, 200)

        self.check_status(
            payroll=payroll,
            status=APPROVAL_PENDING,
            approval_pending=self.created_users[3],
            first_approval_status=APPROVED,
            second_approval_status=PENDING
        )

        # now approve by other user to move status to approved
        self.client.force_login(self.created_users[3])
        url = self.get_approval_url(payroll, "approve")
        response = self.client.post(url, {'remarks': 'Final Approved'})
        self.assertEqual(response.status_code, 200)

        self.check_status(
            payroll=payroll,
            status=APPROVED,
            approval_pending=None,
            first_approval_status=APPROVED,
            second_approval_status=APPROVED
        )

    def test_reject(self):
        payroll = self.create_payroll()
        self.create_payroll_approvals(payroll)

        self.client.force_login(self.created_users[2])
        url = self.get_approval_url(payroll, "reject")
        response = self.client.post(url, {'remarks': 'Rejected'})
        self.assertEqual(response.status_code, 200)

        payroll.refresh_from_db()

        self.check_status(
            payroll=payroll,
            status=REJECTED,
            approval_pending=self.created_users[2],
            first_approval_status=REJECTED,
            second_approval_status=PENDING
        )

    def test_approve_by_normal_user(self):
        payroll = self.create_payroll()
        self.create_payroll_approvals(payroll)

        self.client.force_login(self.created_users[1])
        url = self.get_approval_url(payroll, "approve")
        response = self.client.post(url, {'remarks': 'Approved'})
        self.assertEqual(response.status_code, 404)

    def test_approve_by_second_level_while_in_first_level(self):
        payroll = self.create_payroll()
        self.create_payroll_approvals(payroll)

        self.client.force_login(self.created_users[3])
        url = self.get_approval_url(payroll, "approve")
        response = self.client.post(url, {'remarks': 'Approved'})
        self.assertEqual(response.status_code, 404)

    def test_valid_confirm_by_hr(self):
        payroll = self.create_payroll()
        self.create_payroll_approvals(payroll)

        payroll.status = APPROVED
        payroll.save()

        self.client.force_login(self.admin)
        url = self.get_payroll_url(payroll)

        response = self.client.put(url, {'status': CONFIRMED})
        self.assertEqual(response.status_code, 200)

        payroll.refresh_from_db()
        self.assertEqual(payroll.status, CONFIRMED)

    def test_invalid_confirms_by_hr(self):
        payroll = self.create_payroll()
        self.create_payroll_approvals(payroll)
        url = self.get_payroll_url(payroll)
        self.client.force_login(self.admin)

        # --------- from generated ---------------------------
        payroll.status = GENERATED
        payroll.save()

        response = self.client.put(url, {'status': CONFIRMED})
        self.assertEqual(response.status_code, 400)

        # --------- from approval pending --------------------
        payroll.status = APPROVAL_PENDING
        payroll.save()

        response = self.client.put(url, {'status': CONFIRMED})
        self.assertEqual(response.status_code, 400)

        # --------- from approval rejected -------------------
        payroll.status = REJECTED
        payroll.save()

        response = self.client.put(url, {'status': CONFIRMED})
        self.assertEqual(response.status_code, 400)






