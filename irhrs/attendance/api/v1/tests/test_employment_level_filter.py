from django.urls import reverse
from irhrs.attendance.api.v1.tests.factory import IndividualAttendanceSettingFactory
from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.organization.api.v1.tests.factory import EmploymentLevelFactory


class TestEmploymentLevelFilter(RHRSTestCaseWithExperience):
    organization_name = "Aayu-bank"
    users = [
        ("admin@gmail.com", "admin", "Male", "hr"),
        ("user@gmail.com", "user", "Female", "intern")
    ]

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

        # -------------------------------------------------#
        self.employment_level1 = EmploymentLevelFactory(
            title="Assistant",
            organization=self.organization
        )
        self.setting1 = IndividualAttendanceSettingFactory(
            user=self.admin
        )
        detail1 = self.admin.detail
        detail1.employment_level = self.employment_level1
        detail1.save()
        # -------------------------------------------------#
        
        # -------------------------------------------------#
        self.user2 = self.created_users[1]
        self.employment_level2 = EmploymentLevelFactory(
            title="Intern",
            organization=self.organization
        )
        self.setting2 = IndividualAttendanceSettingFactory(
            user=self.created_users[1]
        )                
        detail2 = self.user2.detail
        detail2.employment_level = self.employment_level2
        detail2.save()
        # -------------------------------------------------#
               
    def test_employment_level_filter(self):
        # positive test case for user one
        url = reverse(
            "api_v1:attendance:individual-settings-list",
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + f"?employment_level={self.employment_level1.slug}"
        
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200, response.data)

        self.assertEqual(response.json().get('count'), 1)
        result = response.json()['results'][0]
        self.assertEquals(result["id"], self.setting1.id)

        # positive test case for user two
        url = reverse(
            "api_v1:attendance:individual-settings-list",
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + f"?employment_level={self.employment_level2.slug}"
        
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200, response.data)

        self.assertEqual(response.json().get('count'), 1)
        result = response.json()['results'][0]
        self.assertEquals(result["id"], self.setting2.id)
       
        # negative test case
        bad_url = reverse(
            "api_v1:attendance:individual-settings-list",
            kwargs={
                'organization_slug': self.organization.slug
            }
        ) + "?employment_level=trainee"

        response = self.client.get(bad_url, format='json')
        self.assertEqual(response.status_code, 200, response.data)

        self.assertEqual(response.json().get('count'), 0)
