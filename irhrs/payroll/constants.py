INITIAL_VARIABLES = [
    '__YTD__'
]

# originally type two specific but now also allowed in addition deduction
TYPE_TWO_CONSTANT_VARIABLES = [
    '__SLOT_DAYS_COUNT__',
    '__REMAINING_DAYS_IN_FY__',
    '__REMAINING_MONTHS_IN_FY__'
]


FXN_CAPTURING_REGEX = r"\w+\((\s*('[^'\\]*'|\"[^\"\\]*\"|\d+(?:\.\d*)?|\w+(?:\(\w*\))?)(?:\s*[,+\/*-]\s*(?1))*\s*)?\)"


# Voluntary Rebate type constants
(
    HEALTH_INSURANCE,
    LIFE_INSURANCE,
    DONATION,
    CIT
) = (
    'Health Insurance',
    'Life Insurance',
    'Donation',
    'CIT'
)

# Voluntary Rebate duration unit constants

(
    YEARLY,
    MONTHLY
) = (
    'Yearly',
    'Monthly'
)

VOLUNTARY_REBATE_TYPE_CHOICES = (
    (HEALTH_INSURANCE, HEALTH_INSURANCE),
    (LIFE_INSURANCE, LIFE_INSURANCE),
    (DONATION, DONATION),
    (CIT, CIT)
)

VOLUNTARY_REBATE_DURATION_UNIT_CHOICES = (
    (YEARLY, YEARLY),
    (MONTHLY, MONTHLY)
)

PAYSLIP_HEADING_CHOICES = (
    ('Earning', 'Earning'),
    ('Deduction', 'Deduction')
)
