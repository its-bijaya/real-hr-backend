from irhrs.reimbursement.models import AdvanceExpenseRequest


def generate_code():
    requests = AdvanceExpenseRequest.objects.filter(advance_code__isnull=True)
    print('Updated advance request:')
    for index, request in enumerate(requests):
        organization = request.employee.detail.organization
        code = organization.reimbursement_setting.advance_code if hasattr(
            organization,
            'reimbursement_setting'
        ) else ''
        if not code:
            code = f'ADV-{request.type[:3].upper()}'
        request.advance_code = f'{code}-{index}'
        request.save()
        print(request.id)
