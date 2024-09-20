from irhrs.users.constants import INTERVIEWER
from irhrs.users.models.user import ExternalUser
import random
from random import randint

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Factory

from irhrs.common.models import Disability
from irhrs.core.constants.common import POOR
from irhrs.core.constants.user import (MALE, OTHER, BLOOD_GROUP_CHOICES,
                                       KILOGRAMS, FOOT_INCHES, MARKS_TYPE)
from irhrs.core.utils.common import get_today
from irhrs.organization.api.v1.tests.factory import OrganizationFactory, \
    EmploymentStatusFactory, EmploymentJobTitleFactory,\
    OrganizationDivisionFactory
from irhrs.common.api.tests.factory import DocumentCategoryFactory
from irhrs.users.models import (
    UserPhone, UserExperience, UserMedicalInfo, ChronicDisease,
    UserEducation, UserPastExperience, UserTraining,
    UserVolunteerExperience,
    UserLegalInfo
)
from irhrs.organization.models import UserOrganization
from irhrs.users.models.other import UserDocument, UserLanguage, UserSocialActivity
from ....models import UserDetail

USER = get_user_model()


class UserDetailFactory(DjangoModelFactory):
    class Meta:
        model = UserDetail

    gender = OTHER
    date_of_birth = factory.LazyFunction(lambda: get_today() - timezone.timedelta(days=365 * 20))
    completeness_percent = factory.LazyAttribute(lambda x: random.randint(0, 100))
    organization = factory.SubFactory(OrganizationFactory)


class UserPhoneFactory(DjangoModelFactory):
    class Meta:
        model = UserPhone

    phone = factory.Sequence(lambda n: '98%08d' % n)
    is_verified = True
    verification_sent_at = timezone.now()


class UserExperienceFactory(DjangoModelFactory):
    class Meta:
        model = UserExperience

    organization = factory.SubFactory(OrganizationFactory)
    current_step = randint(1, 9)
    is_current = True
    start_date = get_today()

    @factory.post_generation
    def job_title(self, *args, **kwargs):
        job_title = EmploymentJobTitleFactory(organization=self.organization)
        self.job_title = job_title
        self.save()

    @factory.post_generation
    def employment_status(self, *args, **kwargs):
        employment_status =  EmploymentStatusFactory(organization=self.organization)
        self.employment_status = employment_status
        self.save()

    @factory.post_generation
    def division(self, *args, **kwargs):
        division = OrganizationDivisionFactory(organization=self.organization)

class SimpleUserFactory(DjangoModelFactory):
    """
    Simple user pactory that does not perform any post generate actions
    params:
        _organization --> pass _organization param at the time of instantiation
                          to set user.detail.organization attribute

                          Eg. UserFactory(_organization=org_instance)
    """
    class Meta:
        model = USER

    email = factory.sequence(lambda n: f'email{n}@email.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = 'defaultpassword'
    is_active = True
    is_blocked = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        _organization = kwargs.pop('_organization', None)

        instance = super()._create(model_class, *args, **kwargs)
        instance._organization = _organization
        return instance

class UserFactory(DjangoModelFactory):
    """
    params:

        _organization --> pass _organization param at the time of instantiation
                          to set user.detail.organization attribute

                          Eg. UserFactory(_organization=org_instance)
    """

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        _organization = kwargs.pop('_organization', None)

        instance = super()._create(model_class, *args, **kwargs)
        instance._organization = _organization
        return instance

    class Meta:
        model = USER

    email = factory.sequence(lambda n: f'email{n}@email.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = 'defaultpassword'
    is_active = True
    is_blocked = False

    @factory.post_generation
    def uphone(self, *args, **kwargs):
        UserPhoneFactory(
            phone=randint(111111111, 999999999),
            user=self
        )

    @factory.post_generation
    def user_experiences(self, *args, **kwargs):
        UserExperienceFactory(
            user=self,
            **({'organization': self._organization} if self._organization else {})
        )

    @factory.post_generation
    def detail(self, *args, **kwargs):
        UserDetailFactory(
            user=self,
            **({'organization': self._organization} if self._organization else {})
        )


class UserMinimalFactory(DjangoModelFactory):
    class Meta:
        model = USER

    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = 'None'
    is_active = True
    is_blocked = False

    detail = factory.RelatedFactory(UserDetailFactory, 'user')


class UserDocumentFactory(DjangoModelFactory):
    class Meta:
        model = UserDocument

    title = factory.Faker('text', max_nb_chars=225)
    document_type = factory.SubFactory(DocumentCategoryFactory)


class UserMedicalInfoFactory(DjangoModelFactory):
    class Meta:
        model = UserMedicalInfo

    blood_group = random.choice(
        list(
            dict(BLOOD_GROUP_CHOICES).keys()
        )
    )
    height = str(random.randint(5, 6))
    weight = random.randint(60, 80)
    height_unit = FOOT_INCHES
    weight_unit = KILOGRAMS
    smoker = random.choice([True, False])
    drinker = random.choice([True, False])
    on_medication = random.choice([True, False])

    @factory.post_generation
    def add_disabilities(self, *args, **kwargs):
        fake = Factory.create()
        self.disabilities.add(
            Disability.objects.create(
                title=fake.text(max_nb_chars=150),
                description=fake.text(max_nb_chars=250)
            )
        )


class ChronicDiseaseFactory(DjangoModelFactory):
    class Meta:
        model = ChronicDisease

    title = factory.Faker('text', max_nb_chars=150)
    description = factory.Faker('text', max_nb_chars=500)


class UserEducationFactory(DjangoModelFactory):
    class Meta:
        model = UserEducation

    degree = factory.Faker('text', max_nb_chars=20)
    field = factory.Faker('text', max_nb_chars=150)
    institution = factory.Faker('text', max_nb_chars=150)
    university = factory.Faker('text', max_nb_chars=150)
    marks_type = random.choice(list(dict(MARKS_TYPE).keys()))
    marks = randint(50, 90)


class UserPastExperienceFactory(DjangoModelFactory):
    class Meta:
        model = UserPastExperience

    title = factory.Faker('text', max_nb_chars=150)
    organization = factory.Faker('text', max_nb_chars=150)
    responsibility = factory.Faker('text', max_nb_chars=5000)
    department = factory.Faker('text', max_nb_chars=150)
    employment_level = factory.Faker('text', max_nb_chars=150)
    employment_status = factory.Faker('text', max_nb_chars=150)
    job_location = factory.Faker('address')


class UserTrainingFactory(DjangoModelFactory):
    class Meta:
        model = UserTraining

    name = factory.Faker('text', max_nb_chars=100)
    institution = factory.Faker('text', max_nb_chars=100)
    is_current = True
    start_date = timezone.now()
    end_date = timezone.now()


class UserVolunteerExperienceFactory(DjangoModelFactory):
    class Meta:
        model = UserVolunteerExperience

    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Faker('text', max_nb_chars=150)
    role = factory.Faker('text', max_nb_chars=150)
    description = factory.Faker('text', max_nb_chars=600)
    start_date = timezone.now()
    end_date = timezone.now()


class UserLegalInfoFactory(DjangoModelFactory):
    class Meta:
        model = UserLegalInfo

    pan_number = factory.Sequence(lambda n: '1%02d' % n)
    cit_number = factory.Sequence(lambda n: '11%02d' % n)
    pf_number = factory.Sequence(lambda n: '10%01d' % n)
    citizenship_number = factory.Sequence(lambda n: '10%012d' % n)
    passport_number = factory.Sequence(lambda n: '10%013d' % n)


class UserLanguageFactory(DjangoModelFactory):
    class Meta:
        model = UserLanguage

    name = factory.Faker('text', max_nb_chars=100)
    speaking = POOR
    reading = POOR
    writing = POOR
    listening = POOR


class UserSocialActivityFactory(DjangoModelFactory):
    class Meta:
        model = UserSocialActivity

    title = factory.Faker('text', max_nb_chars=150)
    description = factory.Faker('text', max_nb_chars=500)


class UserOrganizationFactory(DjangoModelFactory):
    class Meta:
        model = UserOrganization

    user = factory.SubFactory(OrganizationFactory)
    organization = factory.SubFactory(OrganizationFactory)
    can_switch = True

class ExternalUserFactory(DjangoModelFactory):
    class Meta:
        model = ExternalUser

    full_name = factory.Faker('name')
    phone_number = factory.Faker('random_number', digits=15)
    email = factory.Faker('email')
    gender = MALE
    dob = factory.Faker('date')
    user_type = INTERVIEWER
    is_archived = factory.Faker('pybool')
