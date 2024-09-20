from django.contrib.auth import get_user_model
from django.urls import reverse
from faker import Factory

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.common.api.tests.factory import EquipmentCategoryFactory
from irhrs.core.constants.common import INTANGIBLE, SCORE_CHOICES
from irhrs.organization.api.v1.tests.factory import EquipmentFactory
from irhrs.task.api.v1.tests import ResultAreaFactory, CoreTaskFactory
from irhrs.task.models.ra_and_core_tasks import UserResultArea
from irhrs.users.api.v1.tests.factory import UserLegalInfoFactory, UserLanguageFactory, \
    UserSocialActivityFactory
from irhrs.users.models import UserExperience, UserLanguage, UserSocialActivity


class EmploymentProfileTestCase(RHRSTestCaseWithExperience):
    """
    test for user's objective, job_description, key result areas , equipment, possession
    """
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()

    user_profile_url = 'api_v1:users:users-detail'
    user_equipment_possession_url = 'api_v1:organization:assigned-equipment-employee-equipments'

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        super().setUp()
        self.user = get_user_model()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.user_check = self.user.objects.get(email=self.users[0][0])

    def test_job_description(self):
        """
        test job description of user
        """
        user_experience = self.user_check.current_experience
        user_experience.job_description = self.fake.text(max_nb_chars=500)
        user_experience.save()

        response = self.client.get(reverse(
            self.user_profile_url,
            kwargs={
                'user_id': self.user_check.id
            }
        ))

        # test description from response is equal to job description from database
        self.assertEqual(response.data.get('current_experience').get('job_description'),
                         user_experience.job_description)

    def test_objective(self):
        """
        test user objective in profile
        """
        user_experience = self.user_check.current_experience
        user_experience.objective = self.fake.text(max_nb_chars=500)
        user_experience.save()

        response = self.client.get(reverse(
            self.user_profile_url,
            kwargs={
                'user_id': self.user_check.id
            }
        ))

        # test user objective from response is equal to database
        self.assertEqual(response.data.get('current_experience').get('objective'),
                         user_experience.objective)

    def test_equipment(self):
        """
        test equipment assigned to user. Here equipment type is other than INTANGIBLE
        """
        equipment_category = EquipmentCategoryFactory()
        equipment = EquipmentFactory(category=equipment_category, organization=self.organization)
        self.user_check.equipments.create(equipment=equipment)

        response_data = self.client.get(reverse(
            self.user_equipment_possession_url,
            kwargs={
                'organization_slug': self.organization.slug,
                'user_id': self.user_check.id,
            }
        ), data={
            'detail': 'false'
        })

        # test equipment assigned to user is in list and possessions is empty
        self.assertEqual(response_data.json().get('equipments')[0],
                         equipment.name)
        self.assertFalse(response_data.json().get('possessions'))

    def test_possessions(self):
        """
        test Intangible assets assigned to user
        """
        equipment_category_factory = EquipmentCategoryFactory(type=INTANGIBLE)
        equipment_factory = EquipmentFactory(category=equipment_category_factory,
                                             organization=self.organization)

        self.user_check.equipments.create(equipment=equipment_factory)

        # test intangible equipment assigned to user is in possessions list and equipments is empty
        response_data = self.client.get(reverse(
            self.user_equipment_possession_url,
            kwargs={
                'organization_slug': self.organization.slug,
                'user_id': self.user_check.id,
            }
        ), data={
            'detail': 'false'
        })
        self.assertEqual(response_data.json().get('possessions')[0],
                         equipment_factory.name)
        self.assertFalse(response_data.json().get('equipments'))

    def test_key_result_areas(self):
        """
        test key result ares of user
        """

        # create result ares of user
        result_area = ResultAreaFactory(division=self.organization.divisions.first())
        core_task = CoreTaskFactory(result_area=result_area)
        experience_id = UserExperience.objects.get(user=self.user_check)
        user_result_area = UserResultArea.objects.create(
            user_experience=experience_id,
            result_area=result_area,
            key_result_area=True
        )
        user_result_area.core_tasks.add(core_task)

        # user detail response
        response = self.client.get(reverse(
            self.user_profile_url,
            kwargs={
                'user_id': self.user_check.id
            }
        ))
        self.assertEqual(response.json().get('key_result_area')[0],
                         user_result_area.result_area.title)

    def test_legal_information(self):
        """
        test legal information of user. Test covers the api test case, get response
        """

        # create legal info of user
        user_legal_info = UserLegalInfoFactory(user=self.user_check)

        # response from api
        response = self.client.get(reverse('api_v1:users:user-legal-info',
                                           kwargs={
                                               'user_id': self.user_check.id,
                                           }))

        # test response from api is equal to database value
        self.assertEqual(response.json().get('pan_number'),
                         user_legal_info.pan_number)
        self.assertEqual(response.json().get('pf_number'), user_legal_info.pf_number)
        self.assertEqual(response.json().get('cit_number'), user_legal_info.cit_number)
        self.assertEqual(response.json().get('citizenship_number'),
                         user_legal_info.citizenship_number)
        self.assertEqual(response.json().get('passport_number'), user_legal_info.passport_number)

    def test_language(self):
        """
        test language of user. Api rest case for language response from api
        """
        # create language experience from language experience factory
        for score in SCORE_CHOICES:
            UserLanguageFactory(
                user=self.user_check,
                speaking=score[0],
                reading=score[0],
                writing=score[0],
                listening=score[0],
            )

        # get user language experience from database
        language_db = UserLanguage.objects.filter(user=self.user_check)

        # get language detail response of individual user from url
        response = self.client.get(reverse('api_v1:users:user-language-list',
                                           kwargs={
                                               'user_id': self.user_check.id,
                                           }))

        # test response from url is equal to database value
        self.validate_data(
            results=response.json().get('results'),
            data=language_db
        )

    def test_social_activity(self):
        """
        test social activity of user
        """
        for _ in range(5):
            UserSocialActivityFactory(
               user=self.user_check
            )

        social_activity_db = UserSocialActivity.objects.filter(user=self.user_check)

        response = self.client.get(reverse('api_v1:users:social-activity-list',
                                           kwargs={
                                               'user_id': self.user_check.id,
                                           }))

        # test response from url is equal to database value
        self.validate_data(
            results=response.json().get('results'),
            data=social_activity_db
        )
