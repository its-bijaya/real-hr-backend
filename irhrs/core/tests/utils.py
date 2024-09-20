import faker
from django.contrib.auth import get_user_model
from django.utils.functional import classproperty

from irhrs.core.utils.common import get_yesterday, DummyObject
from irhrs.organization.api.v1.tests.factory import OrganizationFactory
from irhrs.users.models import UserDetail, UserExperience


def create_users(user_count=1):
    _faker = faker.Faker()
    # instead of UserFactory in loop, bulk create users.
    emails = set()
    while len(emails) < user_count:
        emails.add(_faker.email())
    emails = list(emails)
    organization = OrganizationFactory()
    users = get_user_model().objects.bulk_create(
        [
            get_user_model()(
                email=emails[i],
                first_name=_faker.first_name(),
                last_name=_faker.last_name()
            ) for i in range(user_count)
        ]
    )
    UserDetail.objects.bulk_create(
        [
            UserDetail(user=u, date_of_birth=get_yesterday(), organization=organization)
            for u in users
        ]
    )
    UserExperience.objects.bulk_create(
        [
            UserExperience(
                user=u,
                start_date=get_yesterday(),
                current_step=1,
                is_current=True
            ) for u in users
        ]
    )
    return users


class FakeQuerySet(list):

    def count(self, *args):
        return len(self)

    def exclude(self, *args, **kwargs):
        # implement this method if needed
        return self

    def filter(self, *args, **kwargs):
        # implement this method if needed
        return self

    def select_related(self, *args, **kwargs):
        return self

    def prefetch_related(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self

    def first(self):
        try:
            return self[0]
        except IndexError:
            return None

    def last(self):
        try:
            return self[-1]
        except IndexError:
            return None

    def distinct(self):
        return FakeQuerySet(set(self))

    def values_list(self, *args, flat=False):
        return_value = list()
        for item in self:
            if flat:
                for field_name in args:
                    return_value.append(getattr(item, field_name, None))
            else:
                return_value.append(
                    tuple(
                        getattr(item, field_name, None)
                        for field_name in args
                    ))
        return return_value


class FakeManager:
    """Implement fake model manager class"""

    def __init__(self, faked_class, return_count=0):
        self.model_class = faked_class
        self.return_count = return_count

    def all(self):
        """
        to get counts
        """
        if self.return_count > 0:
            return self.model_class.get_batch(count=self.return_count)
        return FakeQuerySet()

    def exclude(self, *args, **kwargs):
        return self.all().exclude(*args, **kwargs)

    def filter(self, *args, **kwargs):
        return self.all().filter(*args, **kwargs)


class FakeModel(DummyObject):
    class FakeMeta:
        manager_class = FakeManager
        all_objects_count = 0

    @classproperty
    def objects(cls):
        return cls.FakeMeta.manager_class(
            faked_class=cls, return_count=cls.FakeMeta.all_objects_count
        )

    @classmethod
    def get_batch(cls, count):
        return FakeQuerySet(cls(id=i) for i in range(0, count + 1))

    @property
    def id(self):
        return getattr(self, 'pk', None)

    def __int__(self):
        return self.id or 0

