from django.db import transaction

from irhrs.users.models import UserContactDetail


@transaction.atomic
def main():
    dependent_id_mapper = {1: 2, 2: 1}
    for contact_data in UserContactDetail.objects.filter(dependent_id_type__isnull=False):
        dependent_id_type = contact_data.dependent_id_type
        contact_data.dependent_id_type = dependent_id_mapper[dependent_id_type]
        contact_data.save()


if __name__ == "__main__":
    main()
