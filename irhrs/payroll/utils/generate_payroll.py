from .generate import PayrollGenerator


def generate_payroll(*args, **kwargs):
    return PayrollGenerator.generate_payrolls(*args, **kwargs)


def payroll_excel_update(*args, **kwargs):
    return PayrollGenerator.update_payroll(*args, **kwargs)
