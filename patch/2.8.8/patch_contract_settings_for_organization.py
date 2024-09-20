from irhrs.organization.models import Organization, ContractSettings


def create_organization_settings():
    organizations = Organization.objects.filter(contract_settings=None)
    for organization in organizations:
        ContractSettings.objects.update_or_create(organization=organization)


# Run above function to get desired output
create_organization_settings()

