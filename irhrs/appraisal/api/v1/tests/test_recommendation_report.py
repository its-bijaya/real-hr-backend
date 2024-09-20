from dateutil.relativedelta import relativedelta
from irhrs.core.utils.common import get_today

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from faker import Factory
from irhrs.common.api.tests.common import RHRSAPITestCase
from irhrs.appraisal.api.v1.tests.factory import (AppraisalFactory,
                                                  SubPerformanceAppraisalSlotFactory,
                                                  PerformanceAppraisalYearFactory,
                                                  FiscalYearFactory,
                                                  SubPerformanceAppraisalSlotWeightFactory,
                                                  StepUpDownRecommendationFactory)
from irhrs.hris.api.v1.tests.factory import ChangeTypeFactory
from irhrs.hris.models import EmploymentReview


User = get_user_model()

class TestRecommendationReport(RHRSAPITestCase):
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
        self.fiscal_year = FiscalYearFactory(
            organization=self.organization,
            start_at = get_today(),
            end_at = get_today() +
            relativedelta(years=1)
        )
        self.performance_appraisal_year = PerformanceAppraisalYearFactory(
           year = self.fiscal_year
        )
        self.sub_performance_slot = SubPerformanceAppraisalSlotFactory(
            performance_appraisal_year = self.performance_appraisal_year,
            from_date=self.performance_appraisal_year.year.start_at,
            to_date=self.performance_appraisal_year.year.start_at + relativedelta(months=3)
        )
        self.bad_score_sub_performance_slot_weight = SubPerformanceAppraisalSlotWeightFactory(
            appraiser = self.users[0],
            sub_performance_appraisal_slot = self.sub_performance_slot,
            percentage= 10
        )
        self.good_score_sub_performance_slot_weight = SubPerformanceAppraisalSlotWeightFactory(
            appraiser = self.users[1],
            sub_performance_appraisal_slot = self.sub_performance_slot,
            percentage= 90
        )
        self.negative_step_up_down_recommendation = StepUpDownRecommendationFactory(
            sub_performance_appraisal_slot = self.sub_performance_slot,
            score_acquired_from = 0,
            score_acquired_to = 10,
            change_step_by = -1
        )
        self.positive_step_up_down_recommendation = StepUpDownRecommendationFactory(
            sub_performance_appraisal_slot = self.sub_performance_slot,
            score_acquired_from = 10,
            score_acquired_to = 100,
            change_step_by = 2
        )
        self.change_type = ChangeTypeFactory(
            title='Promotion',
            slug='promotion'
        )

    def test_recommendation_report_list(self):
        response = self.client.get(self.recommendation_report_url())
        results = response.json().get('results')
        from irhrs.appraisal.models.performance_appraisal import SubPerformanceAppraisalSlotWeight
        self.assertEqual(len(results), 2)
        luffy = list(filter(lambda x: x.get('user').get('id')==self.users[0].id, results))[0]
        guest = list(filter(lambda x: x.get('user').get('id')==self.users[1].id, results))[0]
        self.assertEqual(luffy.get('step_up_down'), -1)
        self.assertEqual(guest.get('step_up_down'), 2)


    def test_start_employment_review(self):
        payload = {
            "employee_review_list": [
                {
                    "employee": self.users[0].id,
                    "change_type": self.change_type.slug
                }
            ]
        }
        response = self.client.post(self.start_employment_review_url(), data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = EmploymentReview.objects.filter(employee__id=self.users[0].id, change_type=self.change_type).first()
        self.assertTrue(review)

    def start_employment_review_url(self, **kwargs):
        if not kwargs:
            return reverse(
                'api_v1:appraisal:recommendation-report-start-employment-review',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.sub_performance_slot.id
                }
            )
        return reverse(
            'api_v1:appraisal:recommendation-report-start-employment-review',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.sub_performance_slot.id,
                **kwargs
            }
        )

    def recommendation_report_url(self, **kwargs):
        if not kwargs:
            return reverse(
                'api_v1:appraisal:recommendation-report-list',
                kwargs={
                    'organization_slug': self.organization.slug,
                    'sub_performance_appraisal_slot_id': self.sub_performance_slot.id
                }
            )
        return reverse(
            'api_v1:appraisal:recommendation-report-list',
            kwargs={
                'organization_slug': self.organization.slug,
                'sub_performance_appraisal_slot_id': self.sub_performance_slot.id,
                **kwargs
            }
        )

