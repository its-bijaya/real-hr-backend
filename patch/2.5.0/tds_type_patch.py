# Payroll Heading TDS type
import json

from irhrs.payroll.models import Heading, PackageHeading


def set_tds_type(heading_):
    rules = heading_.rules
    if rules:
        rules = json.loads(rules)

    for rule in rules:
        if rule["rule"] == "0":
            rule["tds_type"] = "33"
        else:
            rule["tds_type"] = "20"
    heading_.rules = json.dumps(rules)
    heading_.save()


headings = Heading.objects.all().filter(type="Tax Deduction")

for heading in headings:
    set_tds_type(heading)

# monkey patch property to allow editing of used PackageHeading
PackageHeading.is_used_package_heading = False

package_headings = PackageHeading.objects.filter(type="Tax Deduction")
for heading in package_headings:
    # patch to let package headings edit
    set_tds_type(heading)
