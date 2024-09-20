from copy import deepcopy

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory
from rest_framework import status

from irhrs.appraisal.api.v1.tests.factory import AppraisalSettingFactory, \
    SubPerformanceAppraisalSlotModeFactory
from irhrs.appraisal.constants import SELF_APPRAISAL
from irhrs.appraisal.models.performance_appraisal import PerformanceAppraisalYear
from irhrs.appraisal.models.performance_appraisal import PerformanceAppraisalYear, SubPerformanceAppraisalSlot
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.appraisal.constants import IDLE, COMPLETED, CANCELED, ACTIVE
from irhrs.organization.models import FiscalYear, get_today
from irhrs.appraisal.api.v1.tests.factory import (SubPerformanceAppraisalSlotFactory,
                                                  PerformanceAppraisalYearFactory, AppraisalFactory)

User = get_user_model()


class TestPerformanceAppraisalYear(RHRSAPITestCase):
    organization_name = "Necrophos"
    users = [
        ('admin@gmail.com', 'hellonepal', 'Male'),
        ('luffy@onepiece.com', 'passwordissecret', 'Female'),
        ('guest@admin.com', 'guestnotallowed', 'Other')
    ]
    fake = Factory.create()

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.users = User.objects.all()
        self.fiscal_year, self.past_fiscal_year, self.future_fiscal_year = self.create_fiscal_years()

    def create_appraisal_years(self):
        self.past_performance_appraisal_year = PerformanceAppraisalYearFactory(
            year=self.past_fiscal_year,
            organization=self.organization
        )
        self.current_performance_appraisal_year = PerformanceAppraisalYearFactory(
            year=self.fiscal_year,
            organization=self.organization
        )
        self.future_performance_appraisal_year = PerformanceAppraisalYearFactory(
            year=self.future_fiscal_year,
            organization=self.organization
        )

    def create_fiscal_years(self):
        today = get_today()
        current_fy = FiscalYear.objects.create(
            name=self.fake.word(),
            description=self.fake.word(),
            start_at=today,
            end_at=today + relativedelta(years=1),
            applicable_from=today,
            applicable_to=today + relativedelta(years=1),
            organization=self.organization
        )
        past_fy = FiscalYear.objects.create(
            name=self.fake.word(),
            description=self.fake.word(),
            start_at=today - relativedelta(years=1),
            end_at=today - relativedelta(days=360),
            applicable_from=today - relativedelta(years=1),
            applicable_to=today + relativedelta(days=360),
            organization=self.organization
        )
        future_fy = FiscalYear.objects.create(
            name=self.fake.word(),
            description=self.fake.word(),
            start_at=today + relativedelta(years=2),
            end_at=today + relativedelta(years=3),
            applicable_from=today + relativedelta(years=2),
            applicable_to=today + relativedelta(days=360),
            organization=self.organization
        )
        return current_fy, past_fy, future_fy

    @property
    def data(self):
        return {
            "name": self.fake.word(),
            "year": self.fiscal_year.id,
            "slots": [
                {
                    "title": "First Quarter",
                    "weightage": 50,
                    "from_date": f"{self.fiscal_year.applicable_from}",
                    "to_date": f"{self.fiscal_year.applicable_from + relativedelta(months=6)}"
                },
                {
                    "title": "Second Quarter",
                    "weightage": 50,
                    "from_date": f"{self.fiscal_year.applicable_from + relativedelta(months=6) + relativedelta(days=1)}",
                    "to_date": f"{self.fiscal_year.applicable_to}"
                }
            ]
        }

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:performance-appraisal-year-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:performance-appraisal-year-list',
                kwargs={
                    'organization_slug': self.organization.slug,
                    **kwargs
                }
            )

    def do_create(self, data):
        return self.client.post(self.url(), data=data, format='json')

    def test_create(self):
        data = deepcopy(self.data)
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        instance = PerformanceAppraisalYear.objects.first()

        slots = data.pop('slots')
        self.validate_data([data], [instance])
        self.assertEqual(len(slots), instance.slots.count())
        self.validate_data(slots, instance.slots.all().order_by('from_date'))
        data['slots'] = slots

        # Validation of unique performance appraisal name
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check for past year
        today = get_today()
        fy = FiscalYear.objects.create(
            name=self.fake.word(),
            description=self.fake.word(),
            start_at=today - relativedelta(years=1),
            end_at=today,
            applicable_from=today - relativedelta(years=1),
            applicable_to=today,
            organization=self.organization
        )
        past_year_data = deepcopy(data)
        slots = past_year_data['slots']
        slots[0].update({
            "from_date": f"{fy.applicable_from}",
            "to_date": f"{fy.applicable_from + relativedelta(months=6)}"
        })
        slots[1].update({
            "from_date": f"{fy.applicable_from + relativedelta(months=6) + relativedelta(days=1)}",
            "to_date": f"{fy.applicable_to}"
        })
        past_year_data.update({
            "name": self.fake.word(),
            "year": fy.id,
        })
        response = self.do_create(past_year_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # check duplicate frequency name
        frequency_data = deepcopy(data)
        frequency_data['slots'].append(
            {
                'title': 'Second Quarter',
                'weightage': 25,
                'from_date': f'{self.fiscal_year.applicable_to + relativedelta(days=1)}',
                'to_date': f'{self.fiscal_year.applicable_to + relativedelta(months=6)}'
            }
        )
        response = self.do_create(frequency_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check overlap of date range
        overlapped_data = deepcopy(data)
        slots = overlapped_data['slots'][0]
        slots.update({
            'to_date': f'{self.fiscal_year.applicable_from + relativedelta(months=7)}'
        })
        response = self.do_create(overlapped_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check whether from_date is less then to_date or not
        new_data = deepcopy(data)
        slots = new_data['slots'][0]
        slots.update({
            'from_date': slots.get('to_date'),
            'to_date': slots.get('from_date')
        })
        response = self.do_create(new_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # check for total weightage more than 100
        data['slots'][0].update({
            'weightage': 100
        })
        response = self.do_create(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update(self):
        new_data = deepcopy(self.data)
        new_data.update({
            'name': self.fake.word(),
        })
        self.do_create(self.data)
        instance = PerformanceAppraisalYear.objects.first()
        mode = SubPerformanceAppraisalSlotModeFactory(
            appraisal_type=SELF_APPRAISAL,
            weightage=50,
            start_date=get_today(with_time=True),
            deadline=get_today(with_time=True),
            sub_performance_appraisal_slot=SubPerformanceAppraisalSlotFactory()
        )
        response = self.client.put(
            self.url(pk=instance.id),
            data=new_data,
            format='json'
        )

        self.assertEqual(
            mode.appraisal_type,
            'Self Appraisal'
        )

        self.assertEqual(
            mode.weightage,
            50
        )

        instance.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        slots = new_data.pop('slots')
        self.validate_data([new_data], [instance])
        self.assertEqual(len(slots), instance.slots.count())
        self.validate_data(slots, instance.slots.all().order_by('from_date'))

    def test_list(self):
        _ = self.do_create(data=self.data)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def tearDown(self):
        self.fiscal_year.delete()
        self.past_fiscal_year.delete()
        self.future_fiscal_year.delete()
        return super().tearDown()


class TestPerformanceAppraisalSlotStatus(RHRSAPITestCase):
    organization_name = "Necrophos"
    users = [
        ('admin@gmail.com', 'hellonepal', 'Male'),
        ('luffy@onepiece.com', 'passwordissecret', 'Female'),
        ('guest@admin.com', 'guestnotallowed', 'Other')
    ]
    fake = Factory.create()

    def url(self, **kwargs):
        if kwargs:
            return reverse(
                'api_v1:appraisal:performance-appraisal-year-detail',
                kwargs={
                    'organization_slug': self.organization.slug,
                    **kwargs
                }
            )
        else:
            return reverse(
                'api_v1:appraisal:performance-appraisal-year-list',
                kwargs={
                    'organization_slug': self.organization.slug,
                    **kwargs
                }
            ) + "?as=hr"

    def setUp(self):
        super().setUp()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.users = User.objects.all()
        self.fiscal_year, self.past_fiscal_year, self.future_fiscal_year = self.create_fiscal_years()
        self.past_performance_appraisal_year = PerformanceAppraisalYearFactory(
            year=self.past_fiscal_year,
            organization=self.organization
        )
        self.current_performance_appraisal_year = PerformanceAppraisalYearFactory(
            year=self.fiscal_year,
            organization=self.organization
        )
        self.future_performance_appraisal_year = PerformanceAppraisalYearFactory(
            year=self.future_fiscal_year,
            organization=self.organization
        )

    def create_fiscal_years(self):
        today = get_today(with_time=True)
        current_fy = FiscalYear.objects.create(
            name=self.fake.word(),
            description=self.fake.word(),
            start_at=today,
            end_at=today + relativedelta(years=1),
            applicable_from=today,
            applicable_to=today + relativedelta(years=1),
            organization=self.organization
        )
        past_fy = FiscalYear.objects.create(
            name=self.fake.word(),
            description=self.fake.word(),
            start_at=today - relativedelta(years=1),
            end_at=today - relativedelta(days=360),
            applicable_from=today - relativedelta(years=1),
            applicable_to=today + relativedelta(days=360),
            organization=self.organization
        )
        future_fy = FiscalYear.objects.create(
            name=self.fake.word(),
            description=self.fake.word(),
            start_at=today + relativedelta(years=2),
            end_at=today + relativedelta(years=3),
            applicable_from=today + relativedelta(years=2),
            applicable_to=today + relativedelta(days=360),
            organization=self.organization
        )
        return current_fy, past_fy, future_fy

    def test_status_active(self):
        # Curent date means active
        active_sub_performance_appraisal_slot = SubPerformanceAppraisalSlotFactory(
            performance_appraisal_year=self.current_performance_appraisal_year,
            from_date = get_today(with_time=True),
            to_date = get_today(with_time=True) + relativedelta(days=10)
        )
        response = self.client.get(self.url())
        appraisal_years = [app_year for app_year in response.json().get("results")]
        slots = [slot for slots in appraisal_years for slot in slots.get("slots")]
        slot = [slot for slot in slots if slot["id"]==active_sub_performance_appraisal_slot.id][0]
        self.assertEqual(slot["status"], ACTIVE)

    def test_status_idle(self):
        # Future date means IDLE
        future_sub_performance_appraisal_slot = SubPerformanceAppraisalSlotFactory(
            performance_appraisal_year=self.future_performance_appraisal_year,
            from_date=get_today(with_time=True) + relativedelta(days=1),
            to_date=get_today(with_time=True) + relativedelta(days=10)
        )
        response = self.client.get(self.url())
        appraisal_years = [app_year for app_year in response.json().get("results")]
        slots = [slot for slots in appraisal_years for slot in slots.get("slots")]
        slot = [slot for slot in slots if slot["id"]==future_sub_performance_appraisal_slot.id][0]
        self.assertEqual(slot["status"], IDLE)

    def test_status_completed(self):
        # Past date means Completed
        completed_sub_performance_appraisal_slot = SubPerformanceAppraisalSlotFactory(
            performance_appraisal_year=self.past_performance_appraisal_year,
        )
        response = self.client.get(self.url())
        appraisal_years = [app_year for app_year in response.json().get("results")]
        slots = [slot for slots in appraisal_years for slot in slots.get("slots")]
        slot = [slot for slot in slots if slot["id"]==completed_sub_performance_appraisal_slot.id][0]
        self.assertEqual(slot["status"], COMPLETED)

    def tearDown(self):
        self.past_performance_appraisal_year.delete()
        self.future_performance_appraisal_year.delete()
        self.current_performance_appraisal_year.delete()
