from django.db.models import Subquery, OuterRef

from irhrs.payroll.models import ReportRowRecord, PackageHeading, PayrollEditHistoryAmount


def update_report_rows():
    return ReportRowRecord.objects.filter(heading__isnull=True).update(
        heading=Subquery(
            PackageHeading.objects.filter(id=OuterRef('package_heading_id')).values('heading')[:1]
        )
    )


def update_edit_history():
    return PayrollEditHistoryAmount.objects.filter(heading__isnull=True).update(
        heading=Subquery(
            PackageHeading.objects.filter(id=OuterRef('package_id')).values('heading')[:1]
        )
    )


print("Updated report rows count:", update_report_rows())
print("Updated edit histories count:", update_edit_history())
