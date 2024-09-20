from irhrs.payroll.models import Payroll

# whose payroll approval history does not exist and are approved state
Payroll.objects.filter(
    status='Approved',
    payroll_approval_histories__isnull=True
).update(status='Confirmed')
