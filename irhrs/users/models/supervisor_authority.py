from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from irhrs.common.models import BaseModel
from django.contrib.auth import get_user_model

from irhrs.organization.models import Organization

User = get_user_model()


class UserSupervisor(BaseModel):
    user = models.ForeignKey(to=User,
                             related_name='supervisors',
                             on_delete=models.CASCADE)
    supervisor = models.ForeignKey(to=User,
                                   related_name='as_supervisor',
                                   on_delete=models.CASCADE)
    # supervisor authority order is meant to be up to 3 level as of now
    authority_order = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(3)])

    user_organization = models.ForeignKey(
        Organization,
        related_name='sub_ordinate_organization',
        on_delete=models.CASCADE,
        null=True
    )
    supervisor_organization = models.ForeignKey(
        Organization,
        related_name='supervisor_organization',
        on_delete=models.CASCADE,
        null=True
    )
    # Three basic authority of supervisor, each supervisor has the following
    # authority actions to make
    approve = models.BooleanField(default=False)
    deny = models.BooleanField(default=False)
    forward = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.supervisor} as supervisor of {self.user} - Authority Order: {self.authority_order}"
