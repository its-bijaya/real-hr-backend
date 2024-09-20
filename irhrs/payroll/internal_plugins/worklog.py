from django.db import models
from django.db.models import Subquery, OuterRef, Sum, Value, F, Exists

from irhrs.payroll.internal_plugins.registry import register_plugin
from irhrs.task.models import WorkLog, SENT, WorkLogAction
from irhrs.task.models.settings import UserActivityProject


@register_plugin('employee-amount-from-worklog')
def amount_from_worklog(calculator, package_heading):

    employee = calculator.employee
    from_date = calculator.from_date
    to_date = calculator.to_date

    queryset = WorkLog.objects.filter(
        sender=employee,
        worklog_actions__action=SENT
    ).annotate(
        is_billable=Exists(
            UserActivityProject.objects.filter(
                user=employee,
                project=OuterRef('project'),
                activity=OuterRef('activity'),
                is_billable=True
            )
        )
    ).filter(is_billable=True).annotate(
        sent_date=Subquery(
            WorkLogAction.objects.filter(
                worklog=OuterRef('pk'),
                action=SENT
            ).order_by('-action_date').values('action_date')[:1]
        )
    ).filter(
        sent_date__lte=to_date,
        sent_date__gte=from_date,
    )
    amount = queryset.aggregate(amount=Sum('total_amount'))['amount'] or 0
    sources = list(queryset.values(
        model_name=Value('WorkLog', output_field=models.CharField()),
        instance_id=F('pk'),
        url=Value('', output_field=models.CharField())
    ))

    return amount, sources
