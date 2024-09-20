from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core import mail
from django.utils import timezone

# from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.common.api.tests.common import BaseTestCase
from irhrs.core.utils.common import get_today
from irhrs.hris.tasks.user_experience import notify_contract_expiring
from irhrs.organization.api.v1.tests.factory import (ContractSettingsFactory, HolidayFactory,
                                                     OrganizationFactory)
from irhrs.organization.models import EmploymentJobTitle, Organization
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.models.hrs_permisssion import OrganizationGroup, HRSPermission
from irhrs.users.api.v1.tests.factory import (
    UserExperienceFactory,
    UserOrganizationFactory,
    UserFactory,
)

from irhrs.permission.constants.permissions import (
    HRIS_PERMISSION,
)

class SendContractStatusEmailNotificationTest(BaseTestCase):
    required_permissions_for_test = [
        HRIS_PERMISSION,
    ]
    def setUp(self) -> None:
        super().setUp()
        contract_settings = ContractSettingsFactory(critical_days=15)
        self.organization = contract_settings.organization
        self.user = UserFactory(_organization=self.organization)
        UserOrganizationFactory(user=self.user, organization=self.organization)
        latest_exp = self.user.user_experiences.latest('start_date')
        # set contract expiry to tomorrow
        self.tomorrow = timezone.now().date() + timedelta(days=1)
        latest_exp.employment_status.is_contract = True
        latest_exp.employment_status.save()
        latest_exp.end_date = self.tomorrow
        latest_exp.save()
        self.setup_permission()


    def setup_permission(self):
        admin_group, _ = Group.objects.update_or_create(name=ADMIN)
        self.user.groups.add(admin_group)
        og = OrganizationGroup.objects.create(
            organization=self.user.detail.organization,
            group=admin_group
        )
        for perm in self.required_permissions_for_test:
            permission, _ = HRSPermission.objects.update_or_create(**perm)
            og.permissions.add(permission)

    def test_send_contract_expire_email(self):
        def can_send_email(user, email_type, organization):
            if user == self.user:
                return True
            else:
                return False

        with patch('irhrs.core.utils.email.can_send_email', can_send_email):
            notify_contract_expiring()
            # Test that one message has been sent.
            self.assertEqual(len(mail.outbox), 1)
            mail_instance = mail.outbox[0]

            self.assertEqual(mail_instance.to, [self.user.email])
            email_subject = "Contract Expiry for some users is in critical state."
            notification_text = (
                f"The following contracts are in a critical state:<br>"
                f"1. {self.user.full_name}(Expires tomorrow)."
            )
            self.assertEqual(
                mail_instance.body,
                notification_text
            )
