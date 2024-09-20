from irhrs.payroll.constants import LIFE_INSURANCE, YEARLY, MONTHLY, CIT
from irhrs.payroll.models.user_voluntary_rebate_requests import DELETED
from os import path
from django.urls import reverse

from rest_framework import status

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.payroll.models import (
    UserVoluntaryRebate,
    UserVoluntaryRebateAction
)

from irhrs.organization.api.v1.tests.factory import FiscalYearFactory
from irhrs.payroll.tests.factory import RebateSettingFactory


class UserVoluntaryRebateRequestTest(RHRSAPITestCase):
    users = [
        ('hr@user.com', 'password', 'Female'),
        ('approverfirst@user.com', 'password', 'Male')
    ]
    organization_name = 'Google'

    def get_url(self, name, pk=None):
        extra_kwargs = dict()
        if pk:
            extra_kwargs['pk'] = pk

        return reverse(
            name,
            kwargs=dict(
                organization_slug=self.organization.slug,
                **extra_kwargs
            )
        )

    def get_blob(self, filename):
        file_path = path.join(
            path.dirname(
                path.abspath(__file__)
            ),
            'test_files',
            'user_rebate_documents',
            filename
        )

        return open(file_path, 'rb')

    def setUp(self):
        super().setUp()

        self.fiscal_year = FiscalYearFactory(organization=self.organization)

        self.hr_list_url = 'api_v1:payroll:payroll-user-voluntary-rebates-list'
        self.user_list_url = 'api_v1:payroll:payroll-user-voluntary-rebates-by-current-user'

        self.create_request_action_url = 'api_v1:payroll:payroll-user-voluntary-rebates-new-create-request'
        self.created_action_url = 'api_v1:payroll:payroll-user-voluntary-rebates-accept-create-request'

        self.create_rejected_action_url = 'api_v1:payroll:payroll-user-voluntary-rebates-reject-create-request'

        self.delete_request_action_url = 'api_v1:payroll:payroll-user-voluntary-rebates-delete-request'
        self.delete_action_url = 'api_v1:payroll:payroll-user-voluntary-rebates-accept-delete-request',

        self.delete_rejected_action_url = 'api_v1:payroll:payroll-user-voluntary-rebates-reject-delete-request'

        self.rebate_action_history = 'api_v1:payroll:payroll-user-voluntary-rebates-rebate-action-history'

        self.user_rebate_action_history = 'api_v1:payroll:payroll-user-voluntary-rebates-request-user-rebate-action-history'

        self.hr_create_rebate_entry = 'api_v1:payroll:payroll-user-voluntary-rebates-list'

        self.hr_archive_rebate_entry = 'api_v1:payroll:payroll-user-voluntary-rebates-archive-rebate-entry'
        self.rebate = RebateSettingFactory(title=LIFE_INSURANCE, organization=self.organization)

    def get_create_request_data(self):
        return dict(
            title='rebate title',
            description='This is the description',
            fiscal_year=self.fiscal_year.id,
            rebate=self.rebate.id,
            duration_unit=YEARLY,
            amount=20000,
            file_1=self.get_blob('file_name_1.pdf'),
            file_2=self.get_blob('file_name_2.pdf')
        )

    def test_voluntary_rebate_request(self):
        # self.admin is self.created_users[1]
        self.client.force_login(self.admin)

        res = self.client.post(
            self.get_url(self.create_request_action_url),
            data=self.get_create_request_data()
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_list_voluntary_rebate_request(self):
        self.client.force_login(
            self.created_users[1]
        )

        for i in range(3):
            self.client.post(
                self.get_url(self.create_request_action_url),
                data=self.get_create_request_data()
            )

        self.client.force_login(self.admin)

        for i in range(3):
            self.client.post(
                self.get_url(self.create_request_action_url),
                data=self.get_create_request_data()
            )

        hr_list_res = self.client.get(
            # + "?status=Created&status=Deleted"
            self.get_url(self.hr_list_url)
        )

        self.assertEqual(hr_list_res.status_code, status.HTTP_200_OK)

        user_list_res = self.client.get(
            self.get_url(self.user_list_url)
        )

        self.assertEqual(user_list_res.status_code, status.HTTP_200_OK)

    def test_create_approve(self):
        self.client.force_login(self.admin)

        create_req = self.client.post(
            self.get_url(self.create_request_action_url),
            data=self.get_create_request_data()
        )

        approve_req = self.client.post(
            self.get_url(self.created_action_url,
                         pk=create_req.data.get('id')),
            data=dict(
                remarks='This is remark'
            )
        )

        self.assertEqual(approve_req.status_code, status.HTTP_200_OK)

    def test_create_reject(self):
        self.client.force_login(self.admin)

        create_req = self.client.post(
            self.get_url(self.create_request_action_url),
            data=self.get_create_request_data()
        )

        reject_req = self.client.post(
            self.get_url(self.create_rejected_action_url,
                         pk=create_req.data.get('id')),
            data=dict(
                remarks='This is remark'
            )
        )

        self.assertEqual(reject_req.status_code, status.HTTP_200_OK)

    def test_delete_request(self):
        self.client.force_login(self.admin)

        create_req = self.client.post(
            self.get_url(self.create_request_action_url),
            data=self.get_create_request_data()
        )

        delete_req_without_approve = self.client.post(
            self.get_url(self.delete_request_action_url,
                         pk=create_req.data.get('id')),
            data=dict(
                remarks='This is remark'
            )
        )

        self.assertEqual(delete_req_without_approve.status_code,
                         status.HTTP_400_BAD_REQUEST)

        approve_req = self.client.post(
            self.get_url(self.created_action_url,
                         pk=create_req.data.get('id')),
            data=dict(
                remarks='This is remark'
            )
        )

        self.client.force_login(self.created_users[1])

        other_user_delete_request = self.client.post(
            self.get_url(self.delete_request_action_url,
                         pk=create_req.data.get('id')),
            data=dict(
                remarks='This is remark'
            )
        )

        self.assertEqual(other_user_delete_request.status_code,
                         status.HTTP_400_BAD_REQUEST)

        self.client.force_login(self.admin)

        user_own_delete_request = self.client.post(
            self.get_url(self.delete_request_action_url,
                         pk=create_req.data.get('id')),
            data=dict(
                remarks='This is remark'
            )
        )

        self.assertEqual(user_own_delete_request.status_code,
                         status.HTTP_200_OK)

        rebate_action_history_res = self.client.get(
            self.get_url(
                self.rebate_action_history,
                pk=create_req.data.get('id')
            )
        )

        self.assertEqual(
            rebate_action_history_res.status_code,
            status.HTTP_200_OK
        )

        user_rebate_action_history_res = self.client.get(
            self.get_url(
                self.user_rebate_action_history,
                pk=create_req.data.get('id')
            )
        )

        self.assertEqual(
            user_rebate_action_history_res.status_code,
            status.HTTP_200_OK
        )

        self.client.force_login(self.created_users[1])

        user_rebate_action_history_res = self.client.get(
            self.get_url(
                self.user_rebate_action_history,
                pk=create_req.data.get('id')
            )
        )

        self.assertEqual(
            user_rebate_action_history_res.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_create_and_archive_on_user_behalf(self):
        self.client.force_login(self.admin)

        hr_create_res = self.client.post(
            self.get_url(self.hr_create_rebate_entry),
            data=dict(
                title='rebate title',
                user=self.created_users[1].id,
                description='This is the description',
                fiscal_year=self.fiscal_year.id,
                rebate=self.rebate.id,
                duration_unit=YEARLY,
                amount=20000,
                file_1=self.get_blob('file_name_1.pdf'),
                file_2=self.get_blob('file_name_2.pdf'),
                remarks='On behalf of someone'
            )
        )

        remarks = UserVoluntaryRebateAction.objects.filter(
            user_voluntary_rebate_id=hr_create_res.data.get('id')
        )[0].remarks

        self.assertEqual(remarks, 'On behalf of someone')

        hr_delete_res = self.client.post(
            self.get_url(
                self.hr_archive_rebate_entry,
                pk=hr_create_res.data.get('id')
            ),
            data=dict(
                remarks="Deleting it"
            )
        )

        self.assertEqual(
            hr_delete_res.status_code,
            status.HTTP_200_OK
        )

    def test_monthly_rebate_entry_auto_archive(self):
        self.client.force_login(self.admin)

        res = self.client.post(
            self.get_url(self.hr_create_rebate_entry),
            data=dict(
                title='rebate title',
                user=self.created_users[1].id,
                description='This is the description',
                fiscal_year=self.fiscal_year.id,
                rebate=self.rebate.id,
                duration_unit=YEARLY,
                amount=20000,
                file_1=self.get_blob('file_name_1.pdf'),
                file_2=self.get_blob('file_name_2.pdf'),
                remarks='On behalf of someone'
            )
        )

        self.client.post(
            self.get_url(self.hr_create_rebate_entry),
            data=dict(
                title='rebate title',
                user=self.created_users[1].id,
                description='This is the description',
                fiscal_year=self.fiscal_year.id,
                rebate=self.rebate.id,
                duration_unit=YEARLY,
                amount=20000,
                file_1=self.get_blob('file_name_1.pdf'),
                file_2=self.get_blob('file_name_2.pdf'),
                remarks='On behalf of someone'
            )
        )

        all_rebates = UserVoluntaryRebate.objects.prefetch_related('statuses').order_by('-created_at').all()

        should_be_archived_rebate = all_rebates[1]

        should_be_archived_rebate_statuses = should_be_archived_rebate.statuses.order_by('-created_at').all()

        latest_action = should_be_archived_rebate_statuses[0]

        current_status = latest_action.action

        self.assertEqual(current_status, DELETED)

