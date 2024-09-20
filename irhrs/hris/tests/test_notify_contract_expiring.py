from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.hris.tasks.user_experience import notify_contract_expiring
from irhrs.organization.api.v1.tests.factory import ContractSettingsFactory


class TestNotifyContractExpiring(RHRSTestCaseWithExperience):
    users = [
        ('normal@gmail.com', 'secretThing', 'Male', 'Sales Person')
    ]
    organization_name = "Google"

    def test_contract_settings(self):
        settings = ContractSettingsFactory(organization=self.organization)
        contract_expiring = notify_contract_expiring()
        self.assertEqual(contract_expiring.get('notified_contracts'), 0)
        self.assertEqual(contract_expiring.get('notified_users'), [])
