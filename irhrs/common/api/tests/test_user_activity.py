from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.core.constants.common import NOTICEBOARD
from irhrs.core.utils.user_activity import create_user_activity
from irhrs.users.models import UserDetail


class TestUserActivity(RHRSAPITestCase):
    users = [('admin@gmail.com', 'hellonepalsecret', 'Male')]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.category = NOTICEBOARD
        self.message_string = "Admin has posted in Noticeboard"
        self.user = UserDetail.objects.get(user__email=self.users[0][0]).user

        create_user_activity(actor=self.user,
                             message_string=self.message_string,
                             category=self.category)

    def test_list(self):
        url = reverse('api_v1:commons:recent-activity-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('count'), 1)
        activity = response.data.get("results")[0]

        self.assertEqual(activity.get("message"), self.message_string)
        self.assertEqual(activity.get("category"), self.category)
        self.assertEqual(activity.get("actor").get("id"),
                         self.user.id)
