from irhrs.organization.models import Organization
from irhrs.payroll.models import Heading, Package, ReportRowRecord, CONFIRMED, GENERATED


def get_all_heading_dependencies(heading: Heading, package: Package = None, visited: list = None) -> list:
    """
    :returns: all dependent headings for a heading

    NOTE: returned headings are not sorted
    """
    if visited is None:
        visited = []
    else:
        if heading in visited:
            return visited

        if package and package.package_headings.filter(heading=heading).exists():
            return visited

        # exclude first call as it is not a dependency but dependent
        visited.append(heading)

    for dependency in heading.heading_dependencies.all():
        get_all_heading_dependencies(dependency.target, package, visited)

    return visited


def get_heading_details(obj, headings, set_attribute=False):
    '''
    Returns headings details.
    Also, sets the attribute to the `obj` if `set_attribute` flag is set to true
    '''
    row_report_records = ReportRowRecord.objects.filter(
        employee_payroll=obj,
        heading__in=[heading.id for heading in headings],
        employee_payroll__payroll__status__in=[GENERATED, CONFIRMED]
    )
    res = dict()
    for row_report_record in row_report_records:
        heading_id = row_report_record.heading.id
        res[heading_id] = row_report_record.amount
        if set_attribute:
            setattr(obj,
                    f'amount_of_{heading_id}',
                    row_report_record.amount
                    )
    return res


def is_rebate_type_used_in_heading(organization: Organization, title: str) -> bool:
    """Returns bool whether rebate type exists in any of the heading in given organization"""
    headings = Heading.objects.filter(organization=organization)
    for heading in headings:
        heading_rule = heading.rules
        if isinstance(heading_rule, int):
            continue
        if heading_rule.rfind(title) != -1:
            return True

    return False
