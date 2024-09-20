# Payroll Heading TDS type
import json
import regex

from django.db.models import signals
from irhrs.payroll.signals import update_package_heading_rows

from irhrs.payroll.models import Heading, PackageHeading


from irhrs.payroll.utils.helpers import ( 
    get_heading_name_from_variable
)

def get_changed_rule(rule_string):
    def replacer(x):
        arg = x.groups()[0]
        new_arg = get_heading_name_from_variable(arg)

        return f'__ANNUAL_AMOUNT__("{new_arg}")'

    return_str = regex.sub(
        '__ANNUAL_AMOUNT__\\(\s*([A-Z0-9_]+)\s*\\)', 
        replacer, 
        rule_string
    )
    
    return return_str.strip()

def modify_rule(heading_):
    rules = heading_.rules
    if rules:
        rules = json.loads(rules)

    for rule in rules:
        old_rule = rule.get('rule')
        old_condition = rule.get('condition')

        rule['rule'] = get_changed_rule(old_rule)

        if old_condition:
            rule['condition'] = get_changed_rule(old_condition)

    heading_.rules = json.dumps(rules)
    heading_.save()


headings = Heading.objects.all()

for heading in headings:
    modify_rule(heading)


signals.post_save.disconnect(receiver=update_package_heading_rows, sender=PackageHeading)

setattr(PackageHeading, 'is_used_package_heading', False)

package_headings = PackageHeading.objects.all()
for heading in package_headings:
    modify_rule(heading)

signals.post_save.connect(receiver=update_package_heading_rows, sender=PackageHeading)
