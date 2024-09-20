import regex

from irhrs.payroll.models import ExternalTaxDiscount, UserVoluntaryRebate, YEARLY, \
    UserVoluntaryRebateDocument, UserVoluntaryRebateAction, CREATED, HEALTH_INSURANCE


def migrate_data_from_external_tax_discount_to_user_voluntary_rebate_model():
    external_tax_discounts = ExternalTaxDiscount.objects.all()
    print(f"Migrating {external_tax_discounts.count()} data from ExternalTaxDiscount model to "
          f"UserVoluntaryRebate model")
    for external_tax_discount in external_tax_discounts:
        user_voluntary_rebate = UserVoluntaryRebate.objects.create(
            title=external_tax_discount.title,
            description=external_tax_discount.description,
            user=external_tax_discount.employee,
            fiscal_year=external_tax_discount.fiscal_year,
            type=HEALTH_INSURANCE,
            duration_unit=YEARLY,
            amount=external_tax_discount.amount
        )
        UserVoluntaryRebateAction.objects.create(
            user_voluntary_rebate=user_voluntary_rebate,
            action=CREATED,
            remarks="Migrating from ExternalTaxDiscount"
        )
        external_tax_discount_attachment_name = getattr(
            external_tax_discount.attachment, 'name', None
        )
        file_name = None
        if external_tax_discount_attachment_name:
            # extract file_name from attachment
            file_name = regex.findall(r'[^\/]+(?=\.)', external_tax_discount_attachment_name)

        UserVoluntaryRebateDocument.objects.create(
            user_voluntary_rebate=user_voluntary_rebate,
            file_name=file_name,
            file=external_tax_discount.attachment
        )


migrate_data_from_external_tax_discount_to_user_voluntary_rebate_model()
