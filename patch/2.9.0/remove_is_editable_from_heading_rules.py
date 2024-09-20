from irhrs.payroll.models import Heading


def remove_is_editable_from_heading_rules():
    invalid_headings = list()
    for heading in Heading.objects.all():
        temp_value = heading.rules
        heading.rules = heading.rules.replace('"editable":true,', "")
        if heading.rules == temp_value:
            heading.rules = heading.rules.replace('"editable":false,', "")
        is_valid, validator = heading.rule_is_valid()
        heading.save() if is_valid else invalid_headings.append(heading)

    if invalid_headings:
        print("These are invalid headings, please fix them.")
        for heading in invalid_headings:
            print(heading)


remove_is_editable_from_heading_rules()
