from irhrs.common.api.tests.common import BaseTestCase
from irhrs.core.utils import subordinates
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.users.models import UserSupervisor


class GetNextLevelSupervisorTest(BaseTestCase):
    def setUp(self):
        self.user = UserFactory()
        self.supervisor1 = UserFactory()
        self.supervisor2 = UserFactory()
        self.supervisor3 = UserFactory()

    def assign_supervisors(self):
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=self.user,
                    supervisor=self.supervisor1,
                    approve=True,
                    deny=True,
                    forward=True,
                    authority_order=1
                ),
                UserSupervisor(
                    user=self.user,
                    supervisor=self.supervisor2,
                    approve=True,
                    deny=True,
                    forward=True,
                    authority_order=2
                ),
                UserSupervisor(
                    user=self.user,
                    supervisor=self.supervisor3,
                    approve=True,
                    deny=True,
                    forward=False,
                    authority_order=3
                )
            ]
        )

    def test_get_next_level_supervisor(self):
        self.assign_supervisors()

        level2 = subordinates.get_next_level_supervisor(
            self.user,
            self.supervisor1
        )
        self.assertEqual(level2, self.supervisor2)

        level3 = subordinates.get_next_level_supervisor(
            self.user,
            self.supervisor2
        )
        self.assertEqual(level3, self.supervisor3)
