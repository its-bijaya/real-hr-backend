from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.organization.api.v1.tests.factory import FiscalYearFactory

USER = get_user_model()


class TestFiscalYearViewSet(RHRSTestCaseWithExperience):
    users = [
        ('test@example.com', 'helloSecretWorld', 'Male', 'Programmer'),
    ]
    organization_name = "Google"

    def setUp(self):
        super().setUp()
        self.client.login(
            email=self.users[0][0],
            password=self.users[0][1],
        )

        # FiscalYearFactory(organization=self.organization)

    @property
    def url(self):
        return reverse(
            'api_v1:organization:fiscal-year-list',
            kwargs={'organization_slug': self.organization.slug}
        )

    @staticmethod
    def next_month_payload():
        return [
            {
                "month_index": 1,
                "display_name": "Shrawan",
                "start_at": "2022-07-17",
                "end_at": "2022-08-16"
            },
            {
                "month_index": 2,
                "display_name": "Bhadra",
                "start_at": "2022-08-17",
                "end_at": "2022-09-16"
            },
            {
                "month_index": 3,
                "display_name": "Ashoj",
                "start_at": "2022-09-17",
                "end_at": "2022-10-17"
            },
            {
                "month_index": 4,
                "display_name": "Kartik",
                "start_at": "2022-10-18",
                "end_at": "2022-11-16"
            },
            {
                "month_index": 5,
                "display_name": "Mangsir",
                "start_at": "2022-11-17",
                "end_at": "2022-12-15"
            },
            {
                "month_index": 6,
                "display_name": "Poush",
                "start_at": "2022-12-16",
                "end_at": "2023-01-14"
            },
            {
                "month_index": 7,
                "display_name": "Magh",
                "start_at": "2023-01-15",
                "end_at": "2023-02-12"
            },
            {
                "month_index": 8,
                "display_name": "Falgun",
                "start_at": "2023-02-13",
                "end_at": "2023-03-14"
            },
            {
                "month_index": 9,
                "display_name": "Chaitra",
                "start_at": "2023-03-15",
                "end_at": "2023-04-13"
            },
            {
                "month_index": 10,
                "display_name": "Baishak",
                "start_at": "2023-04-14",
                "end_at": "2023-05-14"
            },
            {
                "month_index": 11,
                "display_name": "Jestha",
                "start_at": "2023-05-15",
                "end_at": "2023-06-15"
            },
            {
                "month_index": 12,
                "display_name": "Ashad",
                "start_at": "2023-06-16",
                "end_at": "2023-07-16"
            }
        ]

    @staticmethod
    def month_payload():
        return [
                {
                    "month_index": 1,
                    "display_name": "Shrawan",
                    "start_at": "2021-07-16",
                    "end_at": "2021-08-16"
                },
                {
                    "month_index": 2,
                    "display_name": "Bhadra",
                    "start_at": "2021-08-17",
                    "end_at": "2021-09-16"
                },
                {
                    "month_index": 3,
                    "display_name": "Ashoj",
                    "start_at": "2021-09-17",
                    "end_at": "2021-10-17"
                },
                {
                    "month_index": 4,
                    "display_name": "Kartik",
                    "start_at": "2021-10-18",
                    "end_at": "2021-11-16"
                },
                {
                    "month_index": 5,
                    "display_name": "Mangsir",
                    "start_at": "2021-11-17",
                    "end_at": "2021-12-15"
                },
                {
                    "month_index": 6,
                    "display_name": "Poush",
                    "start_at": "2021-12-16",
                    "end_at": "2022-01-14"
                },
                {
                    "month_index": 7,
                    "display_name": "Magh",
                    "start_at": "2022-01-15",
                    "end_at": "2022-02-12"
                },
                {
                    "month_index": 8,
                    "display_name": "Falgun",
                    "start_at": "2022-02-13",
                    "end_at": "2022-03-14"
                },
                {
                    "month_index": 9,
                    "display_name": "Chaitra",
                    "start_at": "2022-03-15",
                    "end_at": "2022-04-13"
                },
                {
                    "month_index": 10,
                    "display_name": "Baishak",
                    "start_at": "2022-04-14",
                    "end_at": "2022-05-14"
                },
                {
                    "month_index": 11,
                    "display_name": "Jestha",
                    "start_at": "2022-05-15",
                    "end_at": "2022-06-14"
                },
                {
                    "month_index": 12,
                    "display_name": "Ashad",
                    "start_at": "2022-06-15",
                    "end_at": "2022-07-16"
                }
            ]

    @staticmethod
    def overlap_month_payload():
        return [
                {
                    "month_index": 1,
                    "display_name": "Poush",
                    "start_at": "2020-12-16",
                    "end_at": "2021-01-13"
                },
                {
                    "month_index": 2,
                    "display_name": "Magh",
                    "start_at": "2021-01-14",
                    "end_at": "2021-02-12"
                },
                {
                    "month_index": 3,
                    "display_name": "Falgun",
                    "start_at": "2021-02-13",
                    "end_at": "2021-03-13"
                },
                {
                    "month_index": 4,
                    "display_name": "Chaitra",
                    "start_at": "2021-03-14",
                    "end_at": "2021-04-13"
                },
                {
                    "month_index": 5,
                    "display_name": "Baishak",
                    "start_at": "2021-04-14",
                    "end_at": "2021-05-14"
                },
                {
                    "month_index": 6,
                    "display_name": "Jestha",
                    "start_at": "2021-05-15",
                    "end_at": "2021-06-14"
                },
                {
                    "month_index": 7,
                    "display_name": "Ashad",
                    "start_at": "2021-06-15",
                    "end_at": "2021-07-15"
                },
                {
                    "month_index": 8,
                    "display_name": "Shrawan",
                    "start_at": "2021-07-16",
                    "end_at": "2021-08-16"
                },
                {
                    "month_index": 9,
                    "display_name": "Bhadra",
                    "start_at": "2021-08-17",
                    "end_at": "2021-09-16"
                },
                {
                    "month_index": 10,
                    "display_name": "Ashoj",
                    "start_at": "2021-09-17",
                    "end_at": "2021-10-17"
                },
                {
                    "month_index": 11,
                    "display_name": "Kartik",
                    "start_at": "2021-10-18",
                    "end_at": "2021-11-16"
                },
                {
                    "month_index": 12,
                    "display_name": "Mangsir",
                    "start_at": "2021-11-17",
                    "end_at": "2021-12-15"
                }
            ]

    @staticmethod
    def payload(month, name="79/80", start="2022-07-17",
                end="2023-07-16", app_from="2022-07-17", app_to="2023-07-16"):
        return {
            "id": 70,
            "months": month,
            "description": "test",
            "can_update_or_delete": True,
            "created_at": "2021-01-25T11:07:52.285985+05:45",
            "modified_at": "2021-01-25T14:40:58.883147+05:45",
            "slug": "7879",
            "name": name,
            "start_at": start,
            "end_at": end,
            "applicable_from": app_from,
            "applicable_to": app_to,
            "created_by": 1,
            "modified_by": 1,
            "organization": 17,
            "category": "global"
        }

    # Test cases
    # 1. Should create FY when valid data are provided.
    # 2. Shouldn't create FY if FY name has already been taken for same category.
    # 3. end_date should be greater then start date
    # 4. end_at should be within 1 Year From Start Date (not more than 366 days)
    # 5. applicable_to should be greater than Applicable From Date
    # 6. applicable_from Should be greater than or equals to Start Date
    # 7. applicable_to should be less than or equals to End Date
    # 8. Applicable dates shouldn't overlaps previous FY by new FY
    # 12. FY can overlap to previous FY if category is different.
    # 9. New FY should start exactly after ending of current FY.
    # 10. Start date of Shrawan should be the FY start Date
    # 11. End date of Asar should be the FY end Date

    def test_fy_api(self):

        # 1. Should create FY when valid data are provided.
        pl = self.payload(self.month_payload(), "78/79", "2021-07-16", "2022-07-16", "2021-07-16", "2022-07-16")
        response = self.client.post(
            self.url,
            pl,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            str(response.json())
        )

        # 8. Applicable dates shouldn't overlap previous FY by new FY
        overlap_fy = self.client.post(
            self.url,
            self.payload(
                self.overlap_month_payload(),
                start="2020-12-16",
                end="2021-12-15",
                app_from="2020-12-16",
                app_to="2021-12-15"
            ),
            format='json'
        )

        self.assertEqual(
            overlap_fy.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(overlap_fy.json())
        )
        self.assertEqual(
            overlap_fy.json().get('non_field_errors'),
            ['Applicable dates overlaps 78/79 by 153 days']
        )

        # 12. FY can overlap to previous FY if category is different.
        can_overlap = self.payload(self.overlap_month_payload())

        # Changed category from `global` to `leave`
        can_overlap['category'] = 'leave'
        can_overlap['start_at'] = "2020-12-16"
        can_overlap['end_at'] = "2021-12-15"
        can_overlap['applicable_from'] = "2020-12-16"
        can_overlap['applicable_to'] = "2021-12-15"
        valid_overlap_fy = self.client.post(
            self.url,
            can_overlap,
            format='json'
        )
        self.assertEqual(
            valid_overlap_fy.status_code,
            status.HTTP_201_CREATED,
            str(valid_overlap_fy.json())
        )

        # 2. Shouldn't create FY if FY name has already been taken for same category.
        response = self.client.post(
            self.url,
            pl,
            format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(response.json())
        )
        self.assertEqual(
            response.json().get('name'),
            ['Fiscal Year name has already been taken for this category.']
        )

    def test_new_fy(self):
        # Create new FY with valid data
        # 9. New FY should start exactly after ending of current FY.
        valid_response = self.client.post(
            self.url,
            self.payload(self.next_month_payload()),
            format='json'
        )
        self.assertEqual(
            valid_response.status_code,
            status.HTTP_201_CREATED,
            str(valid_response.json())
        )

        # Fiscal Year applicable to date should be 2022-07-16
        start_at_shrawan = self.client.post(
            self.url,
            self.payload(
                self.overlap_month_payload(),
                name="abc", start="2020-12-16",
                end="2021-12-15",
                app_from="2020-12-16",
                app_to="2021-12-15"
            ),
            format='json'
        )
        self.assertEqual(
            start_at_shrawan.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(start_at_shrawan.json())
        )
        self.assertEqual(
            start_at_shrawan.json().get('non_field_errors'),
            ['Fiscal Year applicable to date should be 2022-07-16']
        )

    def test_fy_validations(self):
        pl = self.next_month_payload()

        # 3. end_date should be greater then start date
        start_smaller_than_end = self.client.post(
            self.url,
            self.payload(
                pl,
                start="2022-07-16",
                end="2022-07-15"
            ),
            format='json'
        )
        self.assertEqual(
            start_smaller_than_end.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        # 4. end_at should be within 1 Year From Start Date (not more than 366 days)
        fy_greater_than_366_days = self.client.post(
            self.url,
            self.payload(
                pl,
                start="2022-07-16",
                end="2023-07-18"
            ),
            format='json'
        )

        self.assertEqual(
            fy_greater_than_366_days.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(fy_greater_than_366_days.json())
        )
        self.assertEqual(
            fy_greater_than_366_days.json().get('end_at'),
            ['Should be within 1 Year From Start Date']
        )

        # 5. applicable_to should be greater than Applicable From Date
        app_to_greater_than_app_from = self.client.post(
            self.url,
            self.payload(
                pl,
                app_from="2022-07-16",
                app_to="2022-07-15"
            ),
            format='json'
        )
        self.assertEqual(
            app_to_greater_than_app_from.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(app_to_greater_than_app_from.json())
        )
        self.assertEqual(
            app_to_greater_than_app_from.json().get('applicable_to'),
            ['Should be greater than Applicable From Date']
        )

        # 6. applicable_from Should be greater than or equals to Start Date
        app_from_greater_or_equal_to_start = self.client.post(
            self.url,
            self.payload(
                pl,
                start="2022-07-16",
                app_from="2022-07-15"
            ),
            format='json'
        )

        self.assertEqual(
            app_from_greater_or_equal_to_start.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(app_from_greater_or_equal_to_start.json())
        )
        self.assertEqual(
            app_from_greater_or_equal_to_start.json().get('applicable_from'),
            ['Should be greater than or equals to Start Date']
        )

        # 7. applicable_to should be less than or equals to End Date
        app_to_less_or_equal_to_end = self.client.post(
            self.url,
            self.payload(
                pl,
                end="2023-07-16",
                app_to="2023-07-17"
            ),
            format='json'
        )

        self.assertEqual(
            app_to_less_or_equal_to_end.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(app_to_less_or_equal_to_end.json())
        )
        self.assertEqual(
            app_to_less_or_equal_to_end.json().get('applicable_to'),
            ['Should be less than or equals to End Date']
        )

        # 10. Start date of Shrawan should be the FY start Date
        start_date_shrawan = self.client.post(
            self.url,
            self.payload(
                pl,
                start="2022-07-16",
                end="2023-07-15",
                app_from="2022-07-16",
                app_to="2023-07-15"
            ),
            format='json'
        )
        self.assertEqual(
            start_date_shrawan.status_code,
            status.HTTP_400_BAD_REQUEST,
            str(start_date_shrawan.json())
        )
        self.assertEqual(
            start_date_shrawan.json().get('month'),
            ['Start date of Shrawan should be the FY start Date']
        )
