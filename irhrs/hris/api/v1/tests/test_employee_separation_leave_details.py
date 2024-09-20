import datetime
from unittest.mock import patch

from django.urls import reverse

from config import settings
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.utils.common import get_today
from irhrs.hris.constants import COMPLETED
from irhrs.hris.models import LeaveEncashmentOnSeparation
from irhrs.hris.tests.test_encash_leave_on_separation import LeaveEncashmentOnSeparationTestMixin
from irhrs.leave.api.v1.tests.factory import LeaveTypeFactory, LeaveRuleFactory, \
    LeaveAccountFactory, LeaveRequestFactory
from irhrs.leave.constants.model_constants import TIME_OFF, APPROVED


class EmployeeSeparationLeaveDetailsTestCase(LeaveEncashmentOnSeparationTestMixin,
                                             RHRSAPITestCase):
    users = (
        ('admin@email.com', 'password', 'Male'),
        ('normal@email.com', 'password', 'Male'),
    )
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.set_up_separation_data()

    def test_list(self):
        url = reverse(
            'api_v1:hris:separation-leave-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id
            }
        )
        self.client.force_login(self.admin)
        response1 = self.client.get(url)

        self.assertEqual(response1.status_code, 200, response1.data)
        self.assertEqual(response1.data.get('count'), 1)

        element1 = response1.data.get('results')[0]

        self.assertEqual(element1["id"], self.leave_account.id)
        self.assertEqual(element1["renew_balance"], 365)

        self.assertEqual(element1["proportionate"],
                         self.expected_proportionate)
        self.assertEqual(element1['used_balance'], 5)
        self.assertEqual(element1['carry_forward'], 10)
        self.assertEqual(element1['encashed_balance'],
                         self.expected_proportionate + 10 - 5)
        self.assertEqual(element1['edited'], False)

        # ------------- After Edit -------------------------------------------------- #
        LeaveEncashmentOnSeparation.objects.create(
            separation=self.separation,
            leave_account=self.leave_account,
            encashment_balance=45
        )

        response2 = self.client.get(url)

        self.assertEqual(response2.status_code, 200, response2.data)
        self.assertEqual(response2.data.get('count'), 1)
        element2 = response2.data.get('results')[0]

        self.assertEqual(element2["id"], self.leave_account.id)
        self.assertEqual(element2["renew_balance"], 365)
        self.assertEqual(element2["proportionate"],
                         self.expected_proportionate)
        self.assertEqual(element2['used_balance'], 5)
        self.assertEqual(element2['carry_forward'], 10)
        self.assertEqual(element2['edited'], True)
        self.assertEqual(element2['encashed_balance'], 45)

        self.master_setting.effective_from = get_today() - datetime.timedelta(days=10)
        self.master_setting.effective_till = get_today() - datetime.timedelta(days=1)
        self.master_setting.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response2.data)
        self.assertEqual(response.data.get('count'), 1)
        element = response.data.get('results')[0]

        self.assertEqual(element["id"], self.leave_account.id)
        self.assertEqual(element["renew_balance"], 365)
        self.assertEqual(element["proportionate"], self.expected_proportionate)
        self.assertEqual(element['used_balance'], 5)
        self.assertEqual(element['carry_forward'], 10)
        self.assertEqual(element['edited'], True)
        self.assertEqual(element['encashed_balance'], 45)

    def test_list_with_no_renewal_rule(self):
        self.renewal_rule.delete()
        url = reverse(
            'api_v1:hris:separation-leave-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id
            }
        )
        self.client.force_login(self.admin)
        response1 = self.client.get(url)

        self.assertEqual(response1.status_code, 200, response1.data)
        self.assertEqual(response1.data.get('count'), 1)

        element1 = response1.data.get('results')[0]

        self.assertEqual(element1["id"], self.leave_account.id)
        self.assertIsNone(element1["renew_balance"])

        self.assertEqual(element1["proportionate"],
                         self.leave_account.usable_balance)
        self.assertEqual(element1['used_balance'], 5)
        self.assertEqual(element1['carry_forward'], 10)
        self.assertEqual(element1['encashed_balance'],
                         self.leave_account.usable_balance)
        self.assertEqual(element1['edited'], False)

    def test_list_when_off_boarding_applied(self):
        """
        When off boarding is applied, leave accounts are archived, but they should be displayed
        completed this feature in two parts
        1. create LeaveEncashmentOnSeparation while applying off boarding if not exists already
            (Cases satisfied in tests of util)
        2. Display leave accounts whose LeaveEncashmentOnSeparation exists regardless of their
           account status
           (This case)
        """
        # set leave account status to archive
        self.leave_account.is_archived = True
        self.leave_account.save()

        # Add edit record
        LeaveEncashmentOnSeparation.objects.create(
            separation=self.separation,
            leave_account=self.leave_account,
            encashment_balance=45
        )
        url = reverse(
            'api_v1:hris:separation-leave-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id
            }
        )
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data.get('count'), 1)
        element = response.data.get('results')[0]

        self.assertEqual(element["id"], self.leave_account.id)
        self.assertEqual(element["renew_balance"], 365)
        self.assertEqual(element["proportionate"], self.expected_proportionate)
        self.assertEqual(element['used_balance'], 5)
        self.assertEqual(element['carry_forward'], 10)
        self.assertEqual(element['edited'], True)
        self.assertEqual(element['encashed_balance'], 45)

    def _test_edit(self):
        # TODO: @ravi fix this test
        url = reverse(
            'api_v1:hris:separation-leave-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id,
                'pk': self.leave_account.id
            }
        )
        payload = {
            'encashed_balance': 45,
            'remarks': 'Good'
        }

        with patch('django.utils.timezone.now', return_value=datetime.datetime(
            # make it before release date
            self.fiscal_year.start_at.year, 10, 1, tzinfo=get_today(with_time=True).tzinfo
        )):
            self.client.force_login(self.admin)
            response = self.client.put(url, payload)
        self.assertEqual(response.status_code, 200, response.data)

        edit = self.leave_account.encashment_edits_on_separation.filter(
            separation=self.separation,
        ).first()

        self.assertEqual(edit.encashment_balance, 45)
        old_balance = self.expected_proportionate + 10 - 5
        history = edit.history.filter(
            actor=self.admin,
            previous_balance=old_balance,
            new_balance=45,
            remarks="Good"
        ).first()
        self.assertIsNotNone(history, edit.history.all())

        # test history list api
        history_list_api = reverse(
            'api_v1:hris:separation-leave-history',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id,
                'pk': self.leave_account.id
            }
        )
        history_response = self.client.get(history_list_api)
        self.assertEqual(history_response.status_code,
                         200, history_response.data)

        self.assertEqual(history_response.data.get('count'), 1)
        element = history_response.data.get('results')[0]

        self.assertEqual(
            element["id"],
            history.id
        )
        self.assertEqual(
            element["message"],
            f"{self.admin.full_name} updated balance from {float(old_balance)} "
            f"to 45.0 with remarks 'Good'."
        )

    def test_edit_with_status_completed(self):
        self.separation.status = COMPLETED
        self.separation.save()

        url = reverse(
            'api_v1:hris:separation-leave-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id,
                'pk': self.leave_account.id
            }
        )
        payload = {
            'encashed_balance': 45,
            'remarks': 'Good'
        }

        with patch('django.utils.timezone.now', return_value=datetime.datetime(
            self.fiscal_year.start_at.year, 10, 1, tzinfo=get_today(with_time=True).tzinfo
            # make it before release date
        )):
            self.client.force_login(self.admin)
            response = self.client.put(url, payload)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(response.data['non_field_errors'],
                         ['Can not update encashment balance while Employment Separation '
                          'is in completed state.'], response.data)

    def test_edit_with_past_release_date(self):
        url = reverse(
            'api_v1:hris:separation-leave-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id,
                'pk': self.leave_account.id
            }
        )
        payload = {
            'encashed_balance': 45,
            'remarks': 'Good'
        }

        with patch('django.utils.timezone.now', return_value=datetime.datetime(
            self.fiscal_year.start_at.year, 12, 30, tzinfo=get_today(with_time=True).tzinfo
            # make it after release date
        )):
            self.client.force_login(self.admin)
            response = self.client.put(url, payload)
        if not settings.ROUND_LEAVE_BALANCE:
            self.assertEqual(response.status_code, 400, response.data)
            self.assertEqual(response.data['non_field_errors'],
                             ['Can not update encashment when last working date is in past.'
                              ' Details has been sent to leave encashment for processing.'],
                             response.data)
        else:
            self.assertEqual(response.status_code, 200, response.data)

    def test_used_balance_with_hourly_leave(self):
        hourly_type = LeaveTypeFactory(category=TIME_OFF, master_setting=self.master_setting,
                                       name="Hourly")
        rule = LeaveRuleFactory(leave_type=hourly_type, is_paid=True)
        leave_account = LeaveAccountFactory(rule=rule, user=self.normal)
        now = get_today(with_time=True)

        leave_date = self.fiscal_year.start_at
        start_time = datetime.datetime(
            leave_date.year,
            leave_date.month,
            leave_date.day,
            hour=10,
            tzinfo=now.tzinfo
        )
        end_time = datetime.datetime(
            leave_date.year,
            leave_date.month,
            leave_date.day,
            hour=11,
            tzinfo=now.tzinfo
        )

        leave_request = LeaveRequestFactory(
            start=start_time,
            end=end_time,
            part_of_day='',
            balance=60,
            leave_rule=rule,
            leave_account=leave_account,
            user=self.normal,
            status=APPROVED
        )

        leave_request.sheets.create(
            leave_for=leave_date,
            balance=0,
            balance_minutes=60,
            start=start_time,
            end=end_time
        )

        leave_request.sheets.create(
            leave_for=leave_date + datetime.timedelta(days=1),
            balance=0,
            balance_minutes=60,
            start=start_time,
            end=end_time
        )

        url = reverse(
            'api_v1:hris:separation-leave-detail',
            kwargs={
                'organization_slug': self.organization.slug,
                'separation_id': self.separation.id,
                'pk': leave_account.id
            }
        )
        self.client.force_login(self.admin)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['used_balance'], '02:00:00')
