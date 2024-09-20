from django.urls import reverse

from irhrs.common.api.tests.common import RHRSAPITestCase


class TestOvertimeSetting(RHRSAPITestCase):
    organization_name = 'Overtime Applicable Org'
    users = [
            ('emailBoy@email.com', 'password', 'gender'),
        ]

    @property
    def setting_url(self):
        return reverse(
            'api_v1:attendance:overtime-settings-list',
            kwargs={
                'organization_slug': self.organization.slug
            }
        )

    def test_overtime_setting_creation(self):
        # payload
        for selection in (True, False):
            name = self.organization_name + 'a' if selection else 'b'
            admin = self.created_users[0]
            payload = {
                'name': name,
                'rates': [],
                'actual_ot_if_actual_gt_approved_ot': selection
            }
            self.client.force_login(admin)
            response = self.client.post(
                self.setting_url,
                data=payload,
                format='json'
            )
            self.assertEqual(
                response.status_code,
                self.status.HTTP_201_CREATED,
                response.json()
            )
            actual_ot_if_actual_gt_approved_ot = self.organization.overtime_settings.filter(
                name=name
            ).values_list('actual_ot_if_actual_gt_approved_ot', flat=True).get()
            self.assertEqual(
                actual_ot_if_actual_gt_approved_ot,
                selection
            )
