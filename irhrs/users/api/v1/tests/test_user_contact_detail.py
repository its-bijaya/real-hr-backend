from django.urls.base import reverse
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.users.models.change_request import ChangeRequestDetails
from irhrs.users.models.contact_and_address import UserContactDetail


class TestUserContactDetail(RHRSAPITestCase):
    users = [("admin@email.com", "hello", "Male"), ("user@email.com", "hello", "Male")]
    organization_name = "Organization"

    @property
    def payload(self):
        return {
            "name": "Rakesh Thapa",
            "contact_of": "Father",
            "address": "Basundhara",
            "number": 3123123,
            "is_dependent": False,
            "number_type": "Mobile",
        }

    @property
    def get_url(self):
        kwargs = {"user_id": self.user.id}
        return reverse("api_v1:users:user-contact-details-list", kwargs=kwargs)

    def setUp(self):
        super().setUp()
        self.user = self.created_users[0]

    def test_user_creates_contact_detail(self):
        self.client.force_login(self.user)
        self.assertFalse(ChangeRequestDetails.objects.exists())
        response = self.client.post(self.get_url, self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ChangeRequestDetails.objects.exists())

    def test_admin_creates_contact_detail(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.get_url + "?as=hr", self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(UserContactDetail.objects.filter(**self.payload).exists())

    def test_user_creates_dependent_contact_detail_without_information(self):
        self.client.force_login(self.user)
        payload = self.payload
        payload["is_dependent"] = True
        response = self.client.post(self.get_url, payload)
        error = {"non_field_errors": ["Provide both document type and document number."]}
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), error)

    def test_admin_creates_dependent_contact_detail_with_information(self):
        self.client.force_login(self.admin)
        payload = self.payload
        payload["is_dependent"] = True
        payload["dependent_id_type"] = 1
        payload["dependent_id_number"] = 12345
        response = self.client.post(self.get_url + "?as=hr", payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            UserContactDetail.objects.filter(
                dependent_id_type=payload["dependent_id_type"],
                dependent_id_number=payload["dependent_id_number"],
            ).exists()
        )

    def test_get_contact_details(self):
        UserContactDetail.objects.create(user=self.user, **self.payload)
        self.client.force_login(self.user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        contact = response.json()['results'][0]
        self.assertEqual(contact['name'], "Rakesh Thapa")
        self.assertEqual(contact['contact_of'], "Father")
        
    def test_user_fills_dependent_id_type_without_enabling_is_dependent(self):
        self.client.force_login(self.user)
        payload = self.payload
        payload["is_dependent"] = False
        payload["dependent_id_type"] = 1
        payload["dependent_id_number"] = 12345

        response = self.client.post(self.get_url, payload)
        error = {"non_field_errors": ["Cannot set id number or type when dependent is false."]}
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), error)


