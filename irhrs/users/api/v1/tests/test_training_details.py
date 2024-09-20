from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from faker import Factory

from irhrs.common.api.tests.common import RHRSTestCaseWithExperience
from irhrs.users.api.v1.tests.factory import UserTrainingFactory, UserVolunteerExperienceFactory
from irhrs.users.models import UserTraining, UserVolunteerExperience


class EmploymentProfileTrainingVolunteerDetailsTestCase(RHRSTestCaseWithExperience):
    """
    test user training details and volunteer experience api test case, test covers get request
    from volunteer and training details api
    """
    users = [
        ('checktest@gmail.com', 'secretWorldIsThis', 'Male', 'Manager'),
    ]
    organization_name = "Google"
    division_name = "Programming"
    branch_name = "Kathmandu"
    division_ext = 123
    fake = Factory.create()

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        super().setUp()
        self.user = get_user_model()
        self.client.login(email=self.users[0][0], password=self.users[0][1])
        self.user_check = self.user.objects.get(email=self.users[0][0])

    def test_training(self):
        """
        test user training detail. get training detail from api and test
        """

        # here we create the training detail of user
        for count in range(5):
            UserTrainingFactory(
                start_date=timezone.now() - relativedelta(days=count + 1),
                end_date=None if count == 0 else timezone.now() - relativedelta(days=count),
                user=self.user_check,
                is_current=True if count == 0 else False
            )

        # get all training detail from database
        training_db = UserTraining.objects.filter(user=self.user_check)

        # get training detail response of individual user from url
        response = self.client.get(reverse('api_v1:users:user-training-list',
                                           kwargs={
                                               'user_id': self.user_check.id,
                                           }))

        # test response from url is equal to database value
        self.validate_data(
            results=response.json().get('results'),
            data=training_db
        )

    def test_volunteer_experience(self):
        """
        test volunteer experience of user. test covers the get api request and verifies the data
        """

        # create volunteer experience from volunteer experience factory
        for count in range(5):
            UserVolunteerExperienceFactory(
                start_date=timezone.now() - relativedelta(days=count),
                end_date=None if count == 0 else timezone.now() - relativedelta(days=count),
                user=self.user_check,
                organization=self.fake.name(),
                currently_volunteering=True if count == 0 else False
            )

        # get user volunteer experience from database
        volunteer_db = UserVolunteerExperience.objects.filter(user=self.user_check)

        # get volunteer detail response of individual user from url
        response = self.client.get(reverse('api_v1:users:user-volunteer-experience-list',
                                           kwargs={
                                               'user_id': self.user_check.id,
                                           }))

        # test response from url is equal to database value
        self.validate_data(
            results=response.json().get('results'),
            data=volunteer_db
        )
