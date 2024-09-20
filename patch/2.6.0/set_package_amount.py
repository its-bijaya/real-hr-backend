from irhrs.payroll.models import ReportRowRecord


def set_package_amount():
    for report_row in ReportRowRecord.objects.filter(package_amount=0):
        report_row.package_amount = report_row.current_package_amount or 0
        report_row.save()
