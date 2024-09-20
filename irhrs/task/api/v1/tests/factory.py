from random import randint

import factory
from factory.django import DjangoModelFactory

from irhrs.organization.api.v1.tests.factory import OrganizationDivisionFactory
from irhrs.task.models import Task, WorkLog
from irhrs.task.models.ra_and_core_tasks import ResultArea, CoreTask, UserResultArea
from irhrs.task.models.settings import Project, Activity
from irhrs.task.models.task import TaskAssociation


class ResultAreaFactory(DjangoModelFactory):
    class Meta:
        model = ResultArea
    title = factory.Faker('text')
    description = factory.Faker('text')
    division = factory.SubFactory(OrganizationDivisionFactory)


class CoreTaskFactory(DjangoModelFactory):
    class Meta:
        model = CoreTask
    result_area = factory.SubFactory(ResultAreaFactory)
    title = factory.Faker('text')
    description = factory.Faker('text')
    order = randint(0, 100)


class UserResultAreaFactory(DjangoModelFactory):
    class Meta:
        model = UserResultArea

####################################################################################################


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Faker('text', max_nb_chars=100)
    description = factory.Faker('text')


class TaskAssociationFactory(DjangoModelFactory):
    class Meta:
        model = TaskAssociation


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Faker('text')
    description = factory.Faker('text')
    is_billable = False


class ActivityFactory(DjangoModelFactory):
    class Meta:
        model = Activity

    name = factory.Faker('text')
    description = factory.Faker('text')
    employee_rate = 500
    client_rate = 600


class WorkLogFactory(DjangoModelFactory):
    class Meta:
        model = WorkLog

    activity_description = factory.Faker('text')
