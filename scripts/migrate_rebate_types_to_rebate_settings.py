from django.db import transaction

from irhrs.payroll.models import RebateSetting, UserVoluntaryRebate

VOLUNTARY_REBATE_TYPE_CHOICES = {
    'Health Insurance': 20000,
    'Life Insurance': 25000,
    'Donation': 100000,
    'CIT': 500000
}


def create_rebate_setting_from_previous_voluntary_rebate_types():
    organization_id = 1
    for key, value in VOLUNTARY_REBATE_TYPE_CHOICES.items():
        RebateSetting.objects.create(
            organization_id=organization_id,
            title=key,
            duration_type='Yearly',
            amount=value,
            is_archived=False
        )


def migrate_data_from_rebate_setting_to_user_voluntary_rebate():
    for instance in UserVoluntaryRebate.objects.all():
        rebate = RebateSetting.objects.filter(title=instance.type).first()
        if rebate:
            instance.rebate = rebate
            instance.save()


@transaction.atomic
def main():
    create_rebate_setting_from_previous_voluntary_rebate_types()
    migrate_data_from_rebate_setting_to_user_voluntary_rebate()


if __name__ == "__main__":
    main()
