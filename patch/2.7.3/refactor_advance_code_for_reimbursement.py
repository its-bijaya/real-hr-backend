from irhrs.reimbursement.models import AdvanceExpenseRequest
from irhrs.reimbursement.models.setting import ReimbursementSetting


def refactor_advance_code():
    advance_requests = AdvanceExpenseRequest.objects.all().order_by('created_at')
    for index, request in enumerate(advance_requests):
        request.advance_code = request.advance_code.split('-')[
            -1] if request.advance_code else index
        request.save()

    if advance_requests:
        print('Updated advance requests: ')
        print(advance_requests.values_list('id', flat=True))

    expense_settings = ReimbursementSetting.objects.all()
    for setting in expense_settings:
        setting.advance_code = 1
        setting.save()

    if expense_settings:
        print('Updated reimbursement setting: ')
        print(expense_settings.values_list('id', flat=True))
