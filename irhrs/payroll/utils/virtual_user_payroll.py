from dateutil.relativedelta import relativedelta

from irhrs.core.constants.organization import GLOBAL
from irhrs.hris.constants import OFFER_LETTER, ONBOARDING
from irhrs.core.utils import get_payroll_dummy_user
from irhrs.core.utils.common import DummyObject
from irhrs.payroll.utils.calculator import NoEmployeeSalaryCalculator
from irhrs.payroll.utils.generate import PayrollGenerator


def calculate_payroll(pre_employment):
    """
    Generate Payroll for a Pre-Employment User.
    :param pre_employment: On Boarding User whose package breakdown is to be shown.
    :return: Package Heading Name, Package Heading Order, Package Heading Amount
    """
    from_date = pre_employment.date_of_join
    salary_package = pre_employment.payroll

    organization_slug = pre_employment.organization.slug

    from irhrs.organization.models import FiscalYearMonth
    fiscal_object = FiscalYearMonth.objects.filter(
        fiscal_year__organization=pre_employment.organization,
        start_at__gte=from_date
    ).order_by('-end_at').first()

    if not fiscal_object:
        return []
    date_work, payroll_start_fiscal_year = PayrollGenerator.get_FY(
        organization_slug,  # The organization from Offer Letter
        fiscal_object.start_at,  # The employee Joined Date.
        fiscal_object.end_at  # a month from that date.
    )
    def first_date_range_user_experiences(*args):
        return DummyObject(current_step=1)

    pre_employment.first_date_range_user_experiences = first_date_range_user_experiences
    calculation = NoEmployeeSalaryCalculator(
        employee=pre_employment,
        datework=date_work,
        from_date=fiscal_object.start_at,
        to_date=fiscal_object.end_at,
        salary_package=salary_package,
        appoint_date=fiscal_object.start_at,
        dismiss_date=None,
        calculate_tax=True,
        extra_headings=None,
        edited_general_headings_difference_except_tax_heading=0,
        edited_general_headings=None,
    )
    package_rows = list()
    for row in calculation.payroll.rows:
        # Format the row.amount with ```'{:15,.2f}'.format(row.amount)``` for CSV format.
        package_rows.append({
            'order': row.package_heading.order,
            'package_name': row.package_heading.heading.name,
            'amount': row.amount
        })
    return package_rows


def generate_payroll_section_for_letter_template(pre_employment):
    payroll = pre_employment.payroll
    if not payroll:
        return ''
    html = (
        '<div style="margin:10px; word-break: break-all">'
        'Your payroll breakdown is presented below:'
        '<table>'
        '<thead>'
        '    <tr>'
        '        <th style="padding: 10px">Particulars</th>'
        '        <th style="padding: 10px">Amount</th>'
        '    </tr>'
        '</thead>'
        '<tbody>'
    )
    payroll_details = calculate_payroll(pre_employment)
    for _json in sorted(payroll_details, key=lambda f: f.get('order')):
        html += (
            "<tr>"
            "    <td style='padding: 10px;'>"
            f"        <strong>{_json.get('package_name')}</strong>"
            "    </td>"
            "    <td style='padding:10px; text-align:right'>"
            f"        {'{:20,.2f}'.format(_json.get('amount'))}"
            "    </td>"
            "</tr>"
         )
    html += '</tbody></table></div>'
    return html
