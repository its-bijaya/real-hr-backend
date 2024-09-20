from django.contrib.auth import get_user_model

from irhrs.core.constants.user import SELF, TEMPORARY
from irhrs.users.api.v1.serializers.thin_serializers import UserFieldThinSerializer

USER = get_user_model()


class UserWrap:
    """User Wrap used in Dynamic Report"""

    def __init__(self, user):
        self.user = user

    def __getattr__(self, item):
        return getattr(self.user, item)

    @property
    def user_experiences_one(self):
        return [self.current_experience] if self.current_experience else []

    @property
    def user_education_one(self):
        return self.user_education.all().order_by('-from_year')[:1]

    @property
    def past_experiences_one(self):
        return self.past_experiences.all().order_by('-end_date')[:1]

    @property
    def contacts_one(self):
        return self.contacts.all().filter(contact_of=SELF)[:1]

    @property
    def addresses_one(self):
        return self.addresses.all().filter(address_type=TEMPORARY)[:1]


class DynamicHRISReportSerializer(UserFieldThinSerializer):
    def __new__(cls, instance=None, *args, **kwargs):
        """Use custom model wrapper for representing instances"""
        if isinstance(instance, USER):
            instance_wrapped = UserWrap(instance) if instance else None
        else:
            # passed constructor to map
            # what happened here?
            instance_wrapped = map(UserWrap, instance)

        if kwargs.pop('many', False):
            return cls.many_init(instance_wrapped, *args, **kwargs)
        return super().__new__(cls, instance_wrapped, *args, **kwargs)
