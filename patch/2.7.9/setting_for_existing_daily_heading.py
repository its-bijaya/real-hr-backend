from django.db.models import Q

from irhrs.payroll.models import PackageHeading, Heading

fil = Q(duration_unit="Daily") & (
    Q(deduct_amount_on_leave__isnull=True) | Q(pay_when_present_holiday_offday__isnull=True)
)

update = dict(deduct_amount_on_leave=True, pay_when_present_holiday_offday=True)

heading_update_count = Heading.objects.filter(fil).count()
Heading.objects.filter(fil).update(**update)
print(f"Updated {heading_update_count} headings.")
package_heading_update_count = PackageHeading.objects.filter(fil).count()
PackageHeading.objects.filter(fil).update(**update)
print(f"Updated {package_heading_update_count} package headings.")
