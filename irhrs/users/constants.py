HEALTH_INSURANCE = 'health_insurance'
LIFE_INSURANCE = 'life_insurance'

POLICY_TYPE_OPTIONS = (
    (HEALTH_INSURANCE, 'Health Insurance'),
    (LIFE_INSURANCE, 'Life Insurance')
)


APPLICANT, INTERVIEWER, REFERENCE_CHECKER, NO_OBJECTION_VERIFIER = (
    'applicant', 'interviewer', 'reference_checker', 'no_objection_verifier'
)
EXTERNAL_USER_TYPE = (
    (APPLICANT, 'Applicant'),
    (INTERVIEWER, 'Interviewer'),
    (REFERENCE_CHECKER, 'Reference Checker'),
    (NO_OBJECTION_VERIFIER, 'No Objection Verifier'),
)
