from datetime import timedelta

import factory
from factory.django import DjangoModelFactory

from irhrs.core.utils.common import get_today
from irhrs.training.models import Training, TrainingType, UserTraining, Trainer
from irhrs.users.api.v1.tests.factory import UserFactory
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.organization.api.v1.tests.factory import MeetingRoomStatusFactory


class TrainingTypeFactory(DjangoModelFactory):
    class Meta:
        model = TrainingType

    title = factory.Faker('text', max_nb_chars=100)
    description = factory.Faker('paragraph', nb_sentences=3)
    budget_limit = 200000


class TrainingFactory(DjangoModelFactory):
    class Meta:
        model = Training

    training_type = factory.SubFactory(TrainingTypeFactory)
    meeting_room = factory.SubFactory(MeetingRoomStatusFactory)
    start = get_today(with_time=True, reset_hours=True) + timedelta(days=1, hours=12)
    end = get_today(with_time=True, reset_hours=True) + timedelta(days=1, hours=20)


class UserTrainingFactory(DjangoModelFactory):
    class Meta:
        model = UserTraining

    user = factory.SubFactory(UserFactory)
    training = factory.SubFactory(TrainingFactory)
    start = get_today(with_time=True) + timedelta(days=1, hours=5)


class TrainerFactory(DjangoModelFactory):
    class Meta:
        model = Trainer

    full_name = factory.Sequence(lambda n: f"Trainer {n}")
    email = factory.Sequence(lambda n: f"external_trainer{n}@gmail.com")
    organization = factory.SubFactory(OrganizationFactory)
    contact_info = {
        "Phone": "9841234567"
    }
