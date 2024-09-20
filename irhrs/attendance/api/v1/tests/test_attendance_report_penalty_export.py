from dateutil import parser
from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.export.models import Export


class TestBreakoutPenalty(RHRSAPITestCase):
    organization_name = 'organization'
    users = [
        ('admin@email.com', 'admin', 'Female'),
        ('supervisor@email.com', 'supervisor', 'Female'),
        ('user@email.com', 'user', 'Female')
    ]

    @property
    def url(self):
        return reverse(
            "api_v1:attendance:timesheet-penalty-report-export",
            kwargs={"organization_slug": self.organization.slug}
        )

    def setUp(self):
        super().setUp()
        self.supervisor = self.created_users[1]
        self.user = self.created_users[2]

    def check_other_modes_get_request(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_detail = {
            'message': "Previous Export file couldn't be found.",
            'url': ''
        }
        self.assertEqual(response.json(), response_detail)

    def check_get_request(self, url, export):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        export_modified_date = parser.parse(response.json()["created_on"])
        self.assertEqual(
            export_modified_date,
            export.modified_at
        )

    def check_post_request(self, url, exported_as):
        self.assertFalse(Export.objects.exists())
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Export.objects.exists())
        self.assertTrue(Export.objects.filter(exported_as=exported_as))

    def test_breakout_penalty_report_file_for_user(self):
        """
        1. Check user is able to send post export request.
        2. Check user doesn't get exports requested as supervisor.
        3. Check user gets only his exports.
        """
        self.client.force_login(self.user)

        self.check_post_request(self.url, exported_as="User")

        export = Export.objects.first()

        # Users shouldn't see supervisor's export.
        self.check_other_modes_get_request(f"{self.url}?as=supervisor")
        self.client.force_login(self.supervisor)
        self.check_other_modes_get_request(self.url)
        self.check_other_modes_get_request(f"{self.url}?as=supervisor")
        self.client.force_login(self.user)

        # User should be able to see his exports
        self.check_get_request(self.url, export=export)

    def test_breakout_penalty_report_file_for_supervisor(self):
        """
        1. Check supervisor is able to send post export request.
        2. Check supervisor doesn't get exports requested as user.
        3. Check supervisor gets only exports requested as supervisor.
        """

        self.client.force_login(self.supervisor)

        self.check_post_request(
            f"{self.url}?as=supervisor",
            exported_as="Supervisor"
        )
        export = Export.objects.get()

        # Supervisor shouldn't see his user export.
        # Also, other user shouldn't be able to view the particular export

        self.check_other_modes_get_request(self.url)
        self.client.force_login(self.user)
        self.check_other_modes_get_request(self.url)
        self.check_other_modes_get_request(f"{self.url}?as=supervisor")
        self.client.force_login(self.supervisor)

        # Supervisor should be able to see exported as supervisor.
        self.check_get_request(
            f"{self.url}?as=supervisor",
            export=export
        )

