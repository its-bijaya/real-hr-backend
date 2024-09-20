from irhrs.core.utils.common import get_today

(APPLIED, SHORTLISTED, INTERVIEWED, SELECTED,
 SCREENED, REJECTED, REFERENCE_VERIFIED) = (
    'applied', 'shortlisted',
    'interviewed', 'selected',
    'screened', 'rejected',
    'reference_verified'
)

PRE_SCREENING_INTERVIEWED = 'pre_screening_interviewed'
ASSESSMENT_TAKEN = 'assessment_taken'
SALARY_DECLARED = 'salary_declared'

JOB_APPLY_STATUS_CHOICES = [
    (APPLIED, 'Applied'),
    (SCREENED, 'Screened'),
    (SHORTLISTED, 'Shortlisted'),
    (PRE_SCREENING_INTERVIEWED, 'Pre Screening Interview'),
    (ASSESSMENT_TAKEN, 'Assessment Taken'),
    (INTERVIEWED, 'Interviewed'),
    (REFERENCE_VERIFIED, 'Reference Verified'),
    (SALARY_DECLARED, 'Salary Declared'),
    (SELECTED, 'Selected'),
    (REJECTED, 'Rejected')
]
NOT_INITIALIZED = 'not-initialized'
INITIALIZED = 'initialized'

INTERVIEW_STATUS = (
    (NOT_INITIALIZED, 'Not Initialized'),
    (INITIALIZED, 'Initialized'),
    (INTERVIEWED, 'Interviewed'),
)

REFERENCE_VERIFIED_STATUS = (
    (NOT_INITIALIZED, 'Not Initialized'),
    (INITIALIZED, 'Initialized'),
    (REFERENCE_VERIFIED, 'Reference Verified'),
)


JOB_APPLY, SALARY_DECLARATION = 'apply', 'salary_declaration'
ATTACHMENT_TYPE_CHOICES = (
    (JOB_APPLY, 'Job Apply'),
    (SALARY_DECLARATION, 'Salary Declaration')
)


PENDING, PROGRESS, COMPLETED = 'Pending', 'Progress', 'Completed'
PROCESS_STATUS_CHOICES = [
    (PENDING, 'Pending'),
    (PROGRESS, 'Progress'),
    (COMPLETED, 'Completed')
]

FULL_TIME = 'full_time'
PART_TIME = 'part_time'
CONTRACTUAL = 'contractual'
FREELANCING = 'freelancing'
INTERNSHIP = 'internship'
VOLUNTEER = 'volunteer'
TEMPORARY = 'temporary'
TRAINEESHIP = 'traineeship'

AVAILABLE_FOR_CHOICES = (
    (FULL_TIME, 'Full Time'),
    (PART_TIME, 'Part Time'),
    (CONTRACTUAL, 'Contractual'),
    (FREELANCING, 'Freelancing'),
    (INTERNSHIP, 'Internship'),
    (VOLUNTEER, 'Volunteer'),
    (TEMPORARY, 'Temporary'),
    (TRAINEESHIP, 'Traineeship'),
)


def get_default_available_for():
    return [FULL_TIME]


MORNING, DAY, EVENING, ANYTIME, NIGHT = (
    "Morning", "Day",
    "Evening", "Anytime",
    "Night"
)
PREFERRED_SHIFT_CHOICES = (
    (MORNING, "Morning"),
    (DAY, "Day"),
    (EVENING, "Evening"),
    (ANYTIME, "Anytime"),
    (NIGHT, "Night"),
)

TOP_LEVEL, SENIOR_LEVEL, MID_LEVEL, ENTRY_LEVEL = (
    'top_level', 'senior_level', 'mid_level', 'entry_level'
)
JOB_LEVEL_CHOICES = (
    (TOP_LEVEL, 'Top Level'),
    (SENIOR_LEVEL, 'Senior Level'),
    (MID_LEVEL, 'Mid Level'),
    (ENTRY_LEVEL, 'Entry Level')
)

(ALL, PENDING, APPROVED, DENIED, DRAFT,
 PUBLISHED, DELETED, MERGED) = ('All', 'Pending', 'Approved',
                                'Denied', 'Draft', 'Published',
                                'Deleted', 'Merged')

JOB_STATUS_CHOICES = (
    (DRAFT, 'Draft'),
    (PENDING, 'Pending'),
    (DENIED, 'Denied'),
    (PUBLISHED, 'Published'),
    (DELETED, 'Deleted')
)

# Common models verification status
PENDING, APPROVED, DENIED, MERGED = 'Pending', 'Approved', 'Denied', 'Merged'

VERIFICATION_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied'),
    (MERGED, 'Merged'),
)

MALE, FEMALE, OTHER = 'Male', 'Female', 'Other'

GENDER_CHOICES = (
    (MALE, "Male"),
    (FEMALE, "Female"),
    (OTHER, "Other"),
)

MARRIED, UNMARRIED = "Married", "Unmarried"

MARITAL_STATUS = (
    (MARRIED, 'Married'),
    (UNMARRIED, 'Unmarried'),
)

NRS, DOLLAR, IRS = 'NRs', '$', 'IRs'
CURRENCY = (
    (NRS, NRS),
    (DOLLAR, DOLLAR),
    (IRS, IRS),
)

BELOW, ABOVE, EQUALS = 'Below', 'Above', 'Equals'
SALARY_OPERATOR = (
    (ABOVE, 'Above'),
    (BELOW, 'Below'),
    (EQUALS, 'Equals')
)

HOURLY, DAILY, WEEKLY, MONTHLY, ANNUAL = 'Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly'
SALARY_UNITS = (
    (HOURLY, "Hourly"),
    (DAILY, "Daily"),
    (WEEKLY, "Weekly"),
    (MONTHLY, "Monthly"),
    (ANNUAL, "Yearly"),

)

SCORE_CHOICES = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5))


SHORT_ANSWER, MULTI_LINE_ANSWER = 'text', 'textarea'
QUESTION_TYPE_CHOICES = (
    (SHORT_ANSWER, 'Short Answer'),
    (MULTI_LINE_ANSWER, 'Multi-line Answer'),
)


(JOB, PRE_SCREENING, POST_SCREENING, INTERVIEW_EVALUATION, REFERENCE_CHECK) = (
    'vacancy', 'pre_screening', 'post_screening', 'interview_evaluation', 'reference_check')

PRE_SCREENING_INTERVIEW = 'pre_screening_interview'
ASSESSMENT = 'assessment'

QUESTION_SET_CHOICES = (
    (JOB, 'Vacancy Question'),
    (PRE_SCREENING, 'Pre Screening'),
    (POST_SCREENING, 'Post Screening'),
    (PRE_SCREENING_INTERVIEW, 'Pre Screening Interview'),
    (ASSESSMENT, 'Assessment'),
    (INTERVIEW_EVALUATION, 'Interview Evaluation'),
    (REFERENCE_CHECK, 'Reference Check'),
)


VERIFIED = 'Verified'

SALARY_DECLARATION_STATUS = (
    (PENDING, 'Pending'),
    (PROGRESS, 'Progress'),
    (COMPLETED, 'Completed'),
    (DENIED, 'Denied')
)

NO_OBJECTION_STATUS = (
    (PENDING, 'Pending'),
    (COMPLETED, 'Completed'),
    (APPROVED, 'Approved'),
    (DENIED, 'Denied')
)

start_year = get_today().year + 1
end_year = start_year - 100

year_choice_list = []
for year in range(end_year, start_year):
    yr = (year, year)
    year_choice_list.append(yr)
sorted_year_choice_list = sorted(year_choice_list, reverse=True)
sorted_year_choice_list.insert(0, (None, "Year"))
YEAR_CHOICES = tuple(sorted_year_choice_list)


MONTH_CHOICES = (
    (None, "Month"),
    (1, 'January'),
    (2, 'February'),
    (3, 'March'),
    (4, 'April'),
    (5, 'May'),
    (6, 'June'),
    (7, 'July'),
    (8, 'August'),
    (9, 'September'),
    (10, 'October'),
    (11, 'November'),
    (12, 'December'),
)

ATTACHMENT_MAX_UPLOAD_SIZE = 2 * 1024 * 1024

# ***************************** Templates ******************

(
    CANDIDATE_LETTER, EXTERNAL_USER_LETTER, NO_OBJECTION_LETTER, SALARY_DECLARATION_LETTER,
    SHORTLIST_MEMORANDUM, INTERVIEW_MEMORANDUM, EMPLOYMENT_AGREEMENT
) = (

    'candidate_letter', 'external_user_letter', 'no_objection_letter', 'salary_declaration_letter',
    'shortlist_memorandum', 'interview_memorandum', 'employment_agreement'
)

TEMPLATE_TYPE_CHOICES = (
    (CANDIDATE_LETTER, 'Candidate Letter'),
    (EXTERNAL_USER_LETTER, 'External User Letter'),
    (NO_OBJECTION_LETTER, 'No Objection Letter'),
    (SALARY_DECLARATION_LETTER, 'Salary Declaration Letter'),
    (SHORTLIST_MEMORANDUM, 'Post Screening Memorandum Report'),
    (INTERVIEW_MEMORANDUM, 'Interview Memorandum Report'),
    (EMPLOYMENT_AGREEMENT, 'Employment Agreement'),
)


CANDIDATE_LETTER_PARAMS = {
    '{{full_name}}': 'Full Name of Recipient.',
    '{{job_title}}': 'Title of Job.',
}

NO_OBJECTION_LETTER_PARAMS = {
    '{{full_name}}': 'Full Name of Recipient.',
    '{{job_title}}': 'Title of Job.',
    '{{published_date}}': 'Job published date.',
    '{{deadline}}': 'Job deadline',
}

EXTERNAL_USER_LETTER_PARAMS = {
    '{{full_name}}': 'Full Name of Recipient.',
    '{{candidate_name}}': 'Full Name of Applicant.',
    '{{job_title}}': 'Title of Job.',
    '{{link}}': 'Link where the use could verify the form.',
}

SALARY_DECLARATION_LETTER_PARAMS = {
    '{{candidate_name}}': 'Full Name of Applicant.',
    '{{job_title}}': 'Title of Job.',
    '{{link}}': 'Link where the use could verify the form.',
}

# Some keys must be confusing as keys are set up for the use of mca
SHORTLIST_MEMORANDUM_PARAMS = {
    '{{job_title}}': 'Job title.',
    '{{no_of_vacancies}}': 'Total number of vacancies.',
    '{{total_applicants}}': 'Total applicants.',
    '{{hr_shortlisted}}': 'Number of applicant shortlisted by HR',
    '{{hiring_manager_shortlisted}}': 'Number of applicant shortlisted by hiring manager.',
    '{{shortlisted_candidate_detail_table}}': 'Table for candidate with '
                                              'score provided by hr and hiring manager.',
    '{{pre_screening_questions}}': 'Questions '
                                   'used for evaluating candidate during screening process.'
}

INTERVIEW_MEMORANDUM_PARAMS = {
    '{{job_title}}': 'Job title.',
    '{{job_link}}': 'Link for title.',
    '{{no_of_vacancies}}': 'Total number of vacancies.',
    '{{total_applicants}}': 'Total applicants.',

    '{{total_eliminated_initially}}': 'No of Candidates eliminated due to duplication, test,'
                                      'or not fulfilling minimum requirement.',
    '{{applicants_after_removing_duplication_test_data}}': 'No of Candidates after removing'
                                      'duplicate or test data.',
    '{{applicants_not_meeting_minimum_requirements}}': 'No of Candidates not meeting required'
                                                       'minimum requirements.',
    '{{total_duplicate}}': 'Total duplicate or test applicants.',
    '{{long_list_eligible_candidate}}': 'Total applicants eligible for applicant process.',
    '{{hr_shortlisted}}': 'Number of applicant shortlisted by HR',
    '{{hiring_manager_shortlisted}}': 'Number of applicant shortlisted by hiring manager.',
    '{{interview_completed}}': 'No of candidate who completed an interview.',
    '{{interview_absent}}': 'No of candidate who does"nt successfully completed an interview.',

    '{{interview_absent_names}}': 'Names of candidate '
                                  'who does"nt successfully completed an interview.',

    '{{backup_candidates_names}}': 'Names of backup candidate.',

    '{{pre_screening_questions}}': 'Questions '
                                   'used for evaluating candidate during screening process.',

    '{{cv_scoring_criteria_table}}': 'Table for CV scoring criteria and total possible points.',
    '{{preliminary_shortlisted_candidate_table}}': 'Table for preliminary shortlisted candidate.',
    '{{application_data_interpretation_table}}': 'Table for application data'
                                                 ' interpretation.',
    '{{final_shortlist_by_hiring_manager_table}}': 'Final Shortlist by hiring Manager table.',
    '{{written_assessment_and_pre_screening_interview_table}}': 'Table for written'
                                                                ' assessment and interview.',
    '{{recommended_candidate_table}}': 'Table for Recommended candidate.',
    '{{final_structured_interview_table}}': 'Table for candidate'
                                            'after final structured interview.',
}

EMPLOYMENT_AGREEMENT_PARAMS = {
    '{{job_title}}': 'Job title.',
    '{{candidate_name}}': 'Full Name of Applicant.',
    '{{duty_location}}': 'Duty Location.',
    '{{residing_at}}': 'Applicant Address.',
    '{{date}}': 'No Objection Initialized Date.',
    '{{total_salary}}': 'Applicant Expected Salary.',
}

# ***************** Templates end ***********************
