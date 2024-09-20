from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.core.utils.common import get_today
from irhrs.hris.api.v1.tests.factory import EmployeeSeparationFactory
from irhrs.hris.utils import apply_separation


class TestResignationLogInDate(RHRSTestCaseWithExperience):
    users = [
        ("test@example.com", "secretThingIsHere", "Male", "Manager")
    ]
    organization_name = "Organization"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123

    def setUp(self) -> None:
        super().setUp()
        self.normal = self.created_users[0]
        self.separation = EmployeeSeparationFactory(
            employee=self.normal,
            release_date=get_today()
        )

    def test_send_resignation_request_login_date(self):
        self.client.force_login(self.normal)
        apply_separation()
        self.normal.refresh_from_db()
        self.assertTrue(self.normal.is_active)
        self.assertFalse(self.normal.is_blocked)
