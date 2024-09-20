from irhrs.organization.api.v1.tests.setup import OrganizationSetUp


class TestOrganization(OrganizationSetUp):
    def setUp(self):
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()


