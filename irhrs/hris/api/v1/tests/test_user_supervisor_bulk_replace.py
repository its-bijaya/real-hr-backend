from django.urls.base import reverse
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.users.models.supervisor_authority import UserSupervisor


class TestUserSupervisorReplace(RHRSTestCaseWithExperience):

    organization_name = "Google"
    users = [
        ("rajesh@example.com", "hr", "Male", "hr"),
        ("anish@example.com", "first", "Male", "supervisor"),
        ("bigyan@example.com", "second", "Male", "supervisor"),
        ("user@example.com", "user", "Male", "intern"),
        ("newsupervisor@example.com", "new", "Female", "supervisor"),
    ]

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.url = (
            (reverse("api_v1:hris:user-supervisor-assign-bulk-replace"))
            + f"?organization_slug={self.organization.slug}"
            + "&as=hr"
        )

        self.payload = {
            "existing_supervisor": self.created_users[1].id,
            "new_supervisor": self.created_users[2].id,
        }
        
    def test_user_supervisor_bulk_replace(self):

        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=self.created_users[i],
                    supervisor=self.created_users[1],
                    authority_order=1,
                    approve=True,
                    deny=True,
                    forward=False,
                )
                for i in [3, 4]
            ]
        )
        
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            UserSupervisor.objects.filter(
                supervisor=self.created_users[2]
            ).count(), 2
        )
        self.assertEqual(response.json(), "Supervisor replaced sucessfully.")

    def test_invalid_user_supervisor_bulk_replace(self):
        self.payload["new_supervisor"] = ""
        payload = self.payload
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            response.json()["new_supervisor"],
            ['This field may not be null.']
        )

        self.payload["existing_supervisor"] = ""
        payload = self.payload
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            response.json()["existing_supervisor"],
            ['This field may not be null.']
        )

    def test_replace_existing_supervisor_as_new_supervisor(self):
        self.payload["new_supervisor"] = self.created_users[1].id
        payload = self.payload
        response = self.client.post(self.url, payload, format="json")
        
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(
            response.json()["new_supervisor"], 
            ['Cannot replace exiting supervisor as new supervisor.']
        )
    
    def test_past_employees_as_supervisor(self):
       
        payload = self.payload
        
        user_experience = self.created_users[2].current_experience
        
        user_experience.is_current = False
        user_experience.save()
        
        response = self.client.post(self.url, payload, format="json")
       
        self.assertEqual(response.status_code, 400, response.data)

        self.assertEqual(
            response.json()['new_supervisor'], ['Cannot replace past employee.']
        )
    
    def test_user_as_supervisor_of_self(self):
        user = self.created_users[3].id
        self.payload['new_supervisor'] = user
        payload = self.payload
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200, response.data)

        self.assertEqual(
            UserSupervisor.objects.filter(
                supervisor=self.created_users[3]
            ).count(), 0
        )
        self.assertEqual(
            response.json(), "Supervisor replaced sucessfully."
        )

    def test_same_user_supervisor_at_different_level(self):
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=self.created_users[4],
                    supervisor=self.created_users[i],
                    authority_order=i,
                    approve=True,
                    deny=True,
                    forward=False
                )
                for i in range(1, 4)
            ]
        )
        
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, 200, response.data)
        user_supervisors = UserSupervisor.objects.filter(
            user=self.created_users[4]
        )
        self.assertEqual(
            user_supervisors.count(), 2
        )
        self.assertTrue(
            user_supervisors.filter(
                supervisor=self.created_users[2], authority_order=1
            ).exists()
        )

        self.assertTrue(
            user_supervisors.filter(
                supervisor=self.created_users[3], authority_order=2
            ).exists()
        )
    
    def test_replace_supervisor_after_deleting_user_as_supervisor(self):
        NO_OF_SUPERVISOR = 2
        UserSupervisor.objects.bulk_create(
            [
                UserSupervisor(
                    user=self.created_users[3],
                    supervisor=self.created_users[i],
                    authority_order=1,
                    approve=True,
                    deny=True,
                    forward=False if i == 2 else True
                )
                for i in range(0, NO_OF_SUPERVISOR)
            ]
        )
        payload = {
            "existing_supervisor": self.created_users[1].id,
            "new_supervisor": self.created_users[3].id,
        }
        self.assertEqual(
            UserSupervisor.objects.count(), NO_OF_SUPERVISOR
        )
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserSupervisor.objects.count(), NO_OF_SUPERVISOR - 1
        )
        EXPECTED_AUTHORITY_ORDER = {
            1: [],
            2: [1],
            3: [1, 2]
        }[NO_OF_SUPERVISOR]
        
        self.assertEqual(
            list(UserSupervisor.objects.order_by("authority_order").values_list(
                "authority_order", flat=True
            )), EXPECTED_AUTHORITY_ORDER
        )
