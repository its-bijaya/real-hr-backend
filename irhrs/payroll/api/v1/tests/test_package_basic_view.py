from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.payroll.models import PackageHeading
from irhrs.payroll.tests.factory import HeadingFactory, PackageFactory


class TestPackageHeading(RHRSTestCaseWithExperience):
    users = [('hr@email.com', 'secret', 'Male', 'Programmer')]
    organization_name = 'Organization'

    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.heading = HeadingFactory(
            is_editable=False, organization=self.organization,
            rules="[{\"rule\":\"0\",\"rule_validator\":{\"numberOnly\":false,"
                 "\"hasRange\":false,\"min\":0,\"max\":0},\"tds_type\":null}]"
        )
        self.package = PackageFactory(organization=self.organization)


    @property
    def package_basic_url(self):
        return reverse(
            'api_v1:payroll:package-basic-view',
            kwargs={
                'pk': self.package.id
            }
        ) + f'?as=hr&organization__slug={self.organization.slug}'

    def test_package_heading_test(self):
        PackageHeading.objects.create(
            package=self.package,
            heading=self.heading,
            order=1,
            rules=dict()
        )
        response = self.client.get(
            self.package_basic_url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            len(response.json()),
            1
        )
        url = self.package_basic_url + '&basic_view=True'
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            len(response.json()),
            0
        )
        heading1 = HeadingFactory(
            is_editable=False, organization=self.organization,
            rules="[{\"rule\":\"0\",\"rule_validator\":{\"numberOnly\":false,"
                  "\"hasRange\":false,\"min\":0,\"max\":0},\"tds_type\":null}]",
            visible_in_package_basic_view=True
        )
        PackageHeading.objects.create(
            package=self.package,
            heading=heading1,
            order=2,
            rules=dict()
        )
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            len(response.json()),
            1
        )
        url = self.package_basic_url + '&basic_view=False'
        response = self.client.get(
            url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            len(response.json()),
            1
        )

        response = self.client.get(
            self.package_basic_url,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            len(response.json()),
            2
        )
