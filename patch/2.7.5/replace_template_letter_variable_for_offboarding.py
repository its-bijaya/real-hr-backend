from django.db.models import Value
from django.db.models.functions import Replace

from irhrs.hris.constants import OFFBOARDING
from irhrs.hris.models import LetterTemplate


def replace_offboarding_variables():
    """
    Replace separation_date with resign_date and
    release_date with last_working_date
    parted_date with resign_date
    """
    offboarding_letter_templates = LetterTemplate.objects.filter(
        type=OFFBOARDING
    )
    # replace separation_date
    offboarding_letter_templates.update(
        message=Replace(
            'message',
            Value('{{separation_date}}'),
            Value('{{resign_date}}')
        )
    )

    # replace release_date
    offboarding_letter_templates.update(
        message=Replace(
            'message',
            Value('{{release_date}}'),
            Value('{{last_working_date}}')
        )
    )

    # replace parted_date
    offboarding_letter_templates.update(
        message=Replace(
            'message',
            Value('{{parted_date}}'),
            Value('{{resign_date}}')
        )
    )
