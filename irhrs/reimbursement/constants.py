TRAVEL = 'Travel'
BUSINESS = 'Business'
MEDICAL = 'Medical'
OTHER = 'Other'

EXPENSE_TYPE = (
    (TRAVEL, 'Travel'),
    (BUSINESS, 'Business'),
    (MEDICAL, 'Medical'),
    (OTHER, 'Other'),
)

CASH = 'Cash'
CHEQUE = 'Cheque'
TRANSFER = 'Transfer'
DEPOSIT = 'Deposit'

SETTLEMENT_OPTION = (
    (CASH, CASH),
    (CHEQUE, CHEQUE),
    (TRANSFER, TRANSFER),
    (DEPOSIT, DEPOSIT)
)

PER_DIEM = 'Per diem'
LODGING = 'Lodging'
OTHER = 'Other'

TRAVEL_EXPENSE_OPTIONS = (
    (PER_DIEM, PER_DIEM),
    (LODGING, LODGING),
    (OTHER, OTHER),
)

USD = 'USD'
NPR = 'NPR'

CURRENCY_OPTION = (
    (USD, USD),
    (NPR, NPR),
    (OTHER, OTHER),
)
