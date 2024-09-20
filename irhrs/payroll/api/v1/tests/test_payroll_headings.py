from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.payroll.models import Heading, PackageHeading, Package
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
    def heading_url(self):
        return reverse(
            "api_v1:payroll:heading-list"
        ) + f'?organization__slug={self.organization.slug}&as=hr'

    @property
    def package_creation_url(self):
        return reverse(
            "api_v1:payroll:package-list"
        ) + f'?organization__slug={self.organization.slug}&as=hr'

    @property
    def package_heading_creation_url(self):
        return reverse(
            "api_v1:payroll:packageheading-drag-heading"
        ) + f'?as=hr&package__organization__slug={self.organization.slug}&auto_resolve=false'

    def package_heading_patch_url(self, pk):
        return reverse(
            "api_v1:payroll:packageheading-detail",
            kwargs={
                "pk": pk
            }
        ) + f'?as=hr&package__organization__slug={self.organization.slug}'

    @property
    def heading_payload(self):
        return {
            "order": 0,
            "organization": self.organization.slug,
            "deduct_amount_on_leave": False,
            "pay_when_present_holiday_offday": False,
            "rules": "[{\"rule\":\"0\",\"rule_validator\":{\"numberOnly\":false,"
                     "\"hasRange\":false,\"min\":0,\"max\":0},\"tds_type\":null}]",
            "name": "For UT",
            "payroll_setting_type": "Salary Structure",
            "type": "Type2Cnst",
            "benefit_type": "",
            "absent_days_impact": "",
            "taxable": "",
            "duration_unit": None,
            "is_editable": False
        }

    @property
    def package_payload(self):
        return {
            "name": "Package Creation",
            "organization": self.organization.slug
        }

    @property
    def package_heading_payload(self):
        return {
            "to_obj_order": 1,
            "package_id": self.package.id,
            "heading_id": self.heading.id
        }

    @property
    def package_heading_patch_payload(self):
        return {
            "order": 1,
            "package": self.package.id,
            "heading": self.heading.id,
            "rules": "[{\"rule\":\"0\",\"rule_validator\":{\"numberOnly\":false,"
                     "\"hasRange\":false,\"min\":0,\"max\":0},\"tds_type\":null}]",
            "type": "Type2Cnst",
            "benefit_type": "",
            "absent_days_impact": "",
            "taxable": "",
            "duration_unit": None

        }

    def test_heading_creation(self):
        response = self.client.post(
            self.heading_url,
            data=self.heading_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(Heading.objects.filter(name=self.heading_payload.get('name')).exists())

    def test_package_creation(self):
        response = self.client.post(
            self.package_creation_url,
            data=self.package_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(Package.objects.filter(
            name=self.package_payload.get('name')
        ).exists())

    def test_package_heading_creation(self):
        response = self.client.post(
            self.package_heading_creation_url,
            data=self.package_heading_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(PackageHeading.objects.filter(heading__name=self.heading.name).exists())

        # update PackageHeading with is_editable is False
        package_heading_id = PackageHeading.objects.first().id
        response = self.client.put(
            self.package_heading_patch_url(pk=package_heading_id),
            data=self.package_heading_patch_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.json(),
            ['Cannot update rule when editable rule option is turned off']
        )

        # update PackageHeading while is_editable is True
        Heading.objects.filter(id=self.heading.id).update(is_editable=True)
        response = self.client.put(
            self.package_heading_patch_url(pk=package_heading_id),
            data=self.package_heading_patch_payload,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertTrue(PackageHeading.objects.filter(heading__name=self.heading.name).exists())
