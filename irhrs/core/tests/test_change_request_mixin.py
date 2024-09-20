from irhrs.common.api.tests.common import BaseTestCase as TestCase, RHRSAPITestCase

from django.contrib.auth.models import Group
from faker import Faker

from irhrs.common.models import Disability, ReligionAndEthnicity
from irhrs.core.mixins.change_request import ChangeRequestMixin
from irhrs.core.utils import nested_get
from irhrs.core.utils.change_request import get_changes
from irhrs.core.utils.common import DummyObject
from irhrs.organization.models import UserOrganization
from irhrs.permission.constants.groups import ADMIN
from irhrs.permission.constants.permissions import USER_PROFILE_PERMISSION
from irhrs.permission.models import HRSPermission
from irhrs.users.api.v1.tests.factory import UserFactory, UserMedicalInfoFactory
from irhrs.users.models import ChangeRequest


class TestChangeRequestMixin(TestCase):
    """
    Change Request Mixin Logic will be test here.
    """
    change_request_class = ChangeRequestMixin
    fake = Faker()

    def test_send_change_request(self):

        HRSPermission.objects.update_or_create(**USER_PROFILE_PERMISSION)
        admin, normal_user = UserFactory(), UserFactory()
        UserOrganization.objects.create(
            user=admin, organization=admin.detail.organization, can_switch=True
        )
        admin.groups.add(Group.objects.get_or_create(name=ADMIN)[0])
        normal_user.groups.clear()

        mixin = ChangeRequestMixin()
        mixin.request = DummyObject(user=admin, query_params={
            'as': 'hr'
        })
        mixin.kwargs = {'user_id': admin.id}
        self.assertFalse(
            mixin.send_change_request,
            "Admin Should not create change request"
        )

        mixin = ChangeRequestMixin()
        mixin.request = DummyObject(user=normal_user)
        mixin.kwargs = {'user_id': normal_user.id}
        self.assertTrue(
            mixin.send_change_request,
            "Normal User Should create change request"
        )

    def test_changes(self):
        user_object = UserFactory()
        changes = get_changes(
            new_data=dict((
                ('first_name',) * 2,
                ('middle_name',) * 2,
                ('last_name',) * 2,
                ('email', user_object.email)
            )),
            instance=user_object
        )

        # Direct Values
        self.assertIn('first_name', changes)
        self.assertIn('last_name', changes)
        self.assertIn('middle_name', changes)
        self.assertIn('email', changes)

        # file field
        # file_pointer = default_storage.open(
        #     self.file_path,
        #     'wb'
        # )
        # file_pointer2 = default_storage.open(
        #     self.file_path2,
        #     'wb'
        # )
        # self.document = pisaDocument(
        #     ("DO DO DO " * 3000).encode(),
        #     dest=file_pointer
        # )
        # self.document2 = pisaDocument(
        #     ("DO DO DO " * 3000).encode(),
        #     dest=file_pointer2
        # )
        # file_pointer.close()
        # file_pointer2.close()
        #
        # document_object = UserDocumentFactory(
        #     user=user_object,
        #     file=self.document
        # )
        # changes = get_changes(
        #     {
        #         'file': self.document2
        #     },
        #     document_object
        # )
        # print(
        #     json.dumps(
        #         changes,
        #         indent=4
        #     )
        # )

        # M2M field
        medical_info = UserMedicalInfoFactory(
            user=user_object
        )
        new_disabilities = [
            Disability.objects.create(
                title=self.fake.sentence(),
                description=self.fake.sentence()
            ) for _ in range(5)
        ]
        changes = get_changes(
            {
                'disabilities': new_disabilities
            },
            medical_info
        )
        self.assertEqual(
            list(medical_info.disabilities.values_list('id', flat=True)),
            nested_get(changes, 'disabilities.old_value'),
            "Medical Info Disabilities should be reflected in Old Values."
        )
        self.assertEqual(
            [x.id for x in new_disabilities],
            nested_get(changes, 'disabilities.new_value'),
            "Medical Info Disabilities should be reflected in New Values."
        )


class TestChangeRequest(RHRSAPITestCase):
    organization_name = 'organization'

    users = [
        ('admin@email.com', 'password', 'male'),
        ('user@email.com', 'password', 'female')
    ]

    def setUp(self):
        HRSPermission.objects.update_or_create(**USER_PROFILE_PERMISSION)
        super().setUp()
        ReligionAndEthnicity.objects.create(name="hinduism", slug="hinduism", category="Religion")
        ReligionAndEthnicity.objects.create(name="sillyism", slug="sillyism", category="Religion")
        self.user = self.created_users[1]
        self.client.force_login(self.admin)
        self.data = {
            "user": {
                "first_name": "Anish",
                "middle_name": "list",
                "last_name": "Bihani"
            },
            "date_of_birth": "1995-12-24",
            "gender": "Male",
            "religion": "hinduism",
            "nationality": "Indian",
            "marital_status": "Single"
        }
        url = f"/api/v1/users/{self.user.id}/?as=hr"
        response = self.client.patch(url, data=self.data, format="json")
        self.assertEqual(response.status_code, 200, response.json())

    def test_user_change_requests(self):
        url = f"/api/v1/users/{self.user.id}/?as="
        self.client.force_login(self.user)
        self.data["user"]["middle_name"] = "Kumar"
        response = self.client.patch(url, data=self.data, format="json")
        self.assertEqual(response.status_code, 200, response.json())
        self.assertEqual(ChangeRequest.objects.count(), 1)

    def test_general_change_requests(self):
        url = f"/api/v1/users/{self.user.id}/?as="
        self.client.force_login(self.user)
        self.data["nationality"] = "Afghan"
        self.data["religion"] = "sillyism"
        response = self.client.patch(url, data=self.data, format="json")
        self.assertEqual(response.status_code, 200, response.json())

        self.assertEqual(ChangeRequest.objects.count(), 1)

    def test_user_and_general_change_requests(self):
        url = f"/api/v1/users/{self.user.id}/?as="
        self.client.force_login(self.user)
        self.data["user"]["middle_name"] = "Bahadur"
        self.data["user"]["last_name"] = "Beluki"
        self.data["nationality"] = "Afghan"
        self.data["religion"] = "sillyism"
        response = self.client.patch(url, data=self.data, format="json")
        self.assertEqual(response.status_code, 200, response.json())

        self.assertEqual(ChangeRequest.objects.count(), 2)
