from django.urls import reverse
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.users.models import User


class UserDetailTestCase(RHRSTestCaseWithExperience):
    users = [
        ("userone@aayu.com", "aayulogic", "male", "admin"),
        ("usertwo@aayulogic.com", "aayubank", "female", "hr"),
    ]

    organization_name = "aayubank"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    #  test for username validation only
    def test_update_username(self):
        url = (
            reverse(
                "api_v1:users:users-detail",
                kwargs={"user_id": self.created_users[1].id},
            )
            + "?as=hr"
        )
        payload = {"user": {"username": "manoj"}}
        first_user_email = self.created_users[0].email
        second_user = User.objects.get(email="usertwo@aayulogic.com")
        self.assertEqual(second_user.username, "usertwo@aayulogic.com")

        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, 200)

        second_user = User.objects.get(email="usertwo@aayulogic.com")
        self.assertEqual(second_user.username, "manoj")

        bad_payload = {"user": {"username": first_user_email}}
        User.objects.filter(email="userone@aayu.com").update(username="admin")
        response = self.client.patch(url, bad_payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json().get("user").get("username")[0],
            "User with this email already exists",
        )
