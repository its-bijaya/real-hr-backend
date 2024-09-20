from django.db import models
from django.db import models
from django.urls import reverse
from rest_framework import status

from irhrs.common.api.tests.common import RHRSUnitTestCase
from irhrs.core.utils import nested_getattr
from irhrs.users.api.v1.tests.factory import UserMedicalInfoFactory, ChronicDiseaseFactory


class TestEmployeeMedicalInformation(RHRSUnitTestCase):
    def setUp(self):
        super().setUp()
        self.create_medical_info()

    def create_users(self, count=10):
        super().create_users(count=5)

    @property
    def employee_medical_info_detail_url(self):
        return reverse(
            'api_v1:users:user-medical-info',
            kwargs=self.kwargs
        )

    def create_medical_info(self):
        for user in self.SYS_USERS:
            UserMedicalInfoFactory(user=user)
            ChronicDiseaseFactory(user=user)

    def test_employee_medical_info(self):
        """
        test for viewing employee medical information
        :return:
        """
        self._test_detail_view()

    def _test_detail_view(self):
        """
        :return:
        """
        """
        --------------------------------------------------------------------------------------------
        viewing other medical_info as hr
        """
        user = self.SYS_USERS[0]
        medical_info = user.medical_info
        chronic_diseases = user.chronicdisease_set.all()
        self.kwargs = {
            'user_id': user.id
        }
        response = self.client.get(
            self.employee_medical_info_detail_url
        )
        self.validate_employee_medical_info(
            response=response,
            medical_info=medical_info,
            chronic_diseases=chronic_diseases
        )

        """
        --------------------------------------------------------------------------------------------
        viewing employee medical information by other user who is not hr
        """
        self.client.force_login(user=self.SYS_USERS[3])
        response = self.client.get(
            self.employee_medical_info_detail_url
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.json().get('detail'),
            "You do not have permission to perform this action."
        )

        """
        --------------------------------------------------------------------------------------------
        viewing employee medical information by self
        """
        user = self.SYS_USERS[1]
        self.client.force_login(user=user)
        self.kwargs['user_id'] = user.id
        response = self.client.get(
            self.employee_medical_info_detail_url
        )
        self.validate_employee_medical_info(response=response,
                                            medical_info=user.medical_info,
                                            chronic_diseases=user.chronicdisease_set.all())

    def validate_employee_medical_info(self, response, medical_info, chronic_diseases=None):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()
        _chronic_diseases = results.pop('chronic_disease')  # data for response of chronic disease
        # test for medical info
        for key, value in results.items():
            if hasattr(medical_info, key):
                if isinstance(getattr(medical_info, key), models.Manager):
                    self.assertEqual(
                        list(getattr(medical_info, key).values(
                            *(list(value[0].keys()))
                        )),
                        value
                    )
                elif isinstance(getattr(medical_info, key), models.Model):
                    self.assertEqual(
                        nested_getattr(medical_info, key).id,
                        value,
                        f'Computed {key} id and response {key} id must be equal'
                    )
                else:
                    self.assertEqual(
                        nested_getattr(medical_info, key),
                        value,
                        f'Computed {key} and response {key} must be equal'
                    )

        # test for chronic diseases
        for index, disease in enumerate(chronic_diseases):
            for key, value in _chronic_diseases[index].items():
                if isinstance(getattr(disease, key), models.Model):
                    self.assertEqual(
                        nested_getattr(disease, key).id,
                        value,
                        f'Computed {key} id and response {key} id must be equal'
                    )
                else:
                    self.assertEqual(
                        nested_getattr(disease, key),
                        value,
                        f'Computed {key} and response {key} must be equal'
                    )
