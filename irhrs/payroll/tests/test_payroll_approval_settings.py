from django.contrib.auth import get_user_model
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.payroll.models import PayrollApprovalSetting

User = get_user_model()


class PayrollApprovalSettingTest(RHRSTestCaseWithExperience):
    users = [
        ('admin@gmail.com', 'password', 'Male', "HR Admin"),
        ('normalone@gmail.com', 'password', 'Male', "Clerk"),
        ('normaltwo@gmail.com', 'password', 'Male', "Clerk"),
        ('normalthree@gmail.com', 'password', 'Male', "Clerk"),
    ]
    organization_name = "Organization"
    base_url_name = 'api_v1:payroll:payroll-approval-settings'

    def get_list_url(self):
        return reverse(
            f"{self.base_url_name}-list",
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def test_valid_create(self):
        data = {'approvals': [user.id for user in self.created_users]}
        self.client.force_login(self.admin)

        url = self.get_list_url()

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            PayrollApprovalSetting.objects.filter(
                user_id__in=data["approvals"],
                organization=self.organization
            ).count(),
            len(data["approvals"])
        )

    def test_adding_same_user_twice(self):
        users = [user.id for user in self.created_users]
        users += users[:1]

        data = {'approvals': users}

        self.client.force_login(self.admin)

        url = self.get_list_url()

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['approvals'], ['Duplicate users found.'])

    def test_permission(self):
        self.client.force_login(User.objects.get(email=self.users[1][0]))
        data = {'approvals': [user.id for user in self.created_users]}

        url = self.get_list_url()
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

    def test_updating(self):
        self.client.force_login(self.admin)

        all_users = [user for user in self.created_users]
        old_users = set(all_users[:3])
        new_users = set(all_users[1:])
        deleted_users = old_users - new_users
        data = {
            'approvals': [user.id for user in new_users]
        }

        for index, user in enumerate(old_users):
            PayrollApprovalSetting.objects.create(
                user=user,
                organization=self.organization,
                approval_level=index
            )

        url = self.get_list_url()
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 201)
        self.assertFalse(PayrollApprovalSetting.objects.filter(
                user__in=deleted_users,
                organization=self.organization
            ).exists()
        )
        self.assertEqual(
            PayrollApprovalSetting.objects.filter(
                user_id__in=data["approvals"],
                organization=self.organization
            ).count(),
            len(data["approvals"])
        )
