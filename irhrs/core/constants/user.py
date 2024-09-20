MALE, FEMALE, OTHER = "Male", "Female", "Other"
GENDER_CHOICES = (
    (MALE, "Male"),
    (FEMALE, "Female"),
    (OTHER, "Other"),
)

MASTER, MR, MS, MRS, DR, SIR = "Master", "Mr", "Ms", "Mrs", "Dr", "Sir"
INITIALS = (
    (SIR, "Sir"),
    (DR, "Dr."),
    (MS, "Ms."),
    (MRS, "Mrs."),
    (MASTER, "Master"),
    (MR, "Mr.")
)

SINGLE, MARRIED, DIVORCED, WIDOWED = "Single", "Married", "Divorced", "Widowed"
MARITAL_STATUS_CHOICES = (
    (SINGLE, "Single"),
    (MARRIED, "Married"),
    (DIVORCED, "Divorced"),
    (WIDOWED, "Widowed")
)


INTEREST, HOBBY = "Interest", "Hobby"
INTEREST_AND_HOBBY_CHOICES = (
    (INTEREST, "Interest"),
    (HOBBY, "Hobby")
)

# Contact and Addresses

NEPAL = '+977'
COUNTRY_CHOICE = (
    (NEPAL, '+977'),
)

FAX, PHONE, MOBILE, WORK = "Fax", "Phone", "Mobile", "Work"
CONTACT_CHOICES = (
    (FAX, "Fax"),
    (PHONE, "Phone"),
    (MOBILE, "Mobile"),
    (WORK, "Work")
)

PERMANENT = 'Permanent'
TEMPORARY = 'Temporary'
ADDRESS_TYPES = (
    (PERMANENT, 'Permanent'),
    (TEMPORARY, 'Temporary')
)
# --

# Education

# Assigning constants in Integer for ordering purposes
PHD, MASTER, BACHELOR, DIPLOMA, INTERMEDIATE, SLC, BELOW_SLC = \
    'PHD', 'Master', 'Bachelor', 'Diploma', 'Intermediate', 'SLC', 'Below SLC'
EDUCATION_DEGREE_CHOICES = (
    (PHD, 'PHD'),
    (MASTER, 'Master'),
    (BACHELOR, 'Bachelor'),
    (DIPLOMA, 'Diploma'),
    (INTERMEDIATE, 'Intermediate'),
    (SLC, 'SLC'),
    (BELOW_SLC, 'Below SLC')
)

MARKS_TYPE = (
    ('cgpa', 'CGPA'),
    ('percentage', 'Percentage')
)
# --

# Medical / Health
BLOOD_GROUP_CHOICES = (
    ('a+', 'A +ve'),
    ('a-', 'A -ve'),
    ('b+', 'B +ve'),
    ('b-', 'B -ve'),
    ('ab+', 'AB +ve'),
    ('ab-', 'AB -ve'),
    ('o+', 'O +ve'),
    ('o-', 'O -ve')
)
FOOT_INCHES, CENTIMETERS = "ft.in", "cms"
HEIGHT_UNIT_CHOICES = (
    (FOOT_INCHES, "Foot and Inches"),
    (CENTIMETERS, "Centimeters")
)

POUNDS, KILOGRAMS = "lbs", "kgs"
WEIGHT_UNIT_CHOICES = (
    (POUNDS, 'Pounds'),
    (KILOGRAMS, 'Kilograms')
)
# --


SELF = "Self"
FATHER = "Father"
MOTHER = "Mother"
SPOUSE = "Spouse"
GRANDFATHER = "Grandfather"
GRANDMOTHER = "Grandmother"
SON = "Son"
DAUGHTER = "Daughter"
SIBLING = "Sibling"
FRIEND = "Friend"
RELATIVE = "Relative"
HOME = "Home"
OFFICE = "Office"
FAMILY = "Family"
PARENT = "Parent"
CHILDREN = "Children"


CONTACT_OF = (
    (SELF, "Self"),
    (FATHER, "Father"),
    (MOTHER, "Mother"),
    (SPOUSE, "Spouse"),
    (GRANDFATHER, "Grandfather"),
    (GRANDMOTHER, "Grandmother"),
    (SON, "Son"),
    (DAUGHTER, "Daughter"),
    (SIBLING, "Sibling"),
    (FRIEND, "Friend"),
    (RELATIVE, "Relative"),
    (HOME, "Home"),
    (OFFICE, "Office"),
    (FAMILY, "Family"),
    (PARENT, "Parent"),
    (CHILDREN, "Children")
)

RESEARCH_PAPER = "Research Paper"
ARTICLE = "Article"
NEWSPAPER_ARTICLE = "Newspaper Article"
MAGAZINE_ARTICLE = "Magazine Article"
BLOG = "Blog"
VIDEO_AND_ARTICLE = "Video & Audio"
LITERATURE = "Literature"
BOOKS = "Books"


PUBLISHED_CONTENT_TYPE = (
    (RESEARCH_PAPER, "Research Paper"),
    (ARTICLE, "Article"),
    (NEWSPAPER_ARTICLE, "Newspaper Article"),
    (MAGAZINE_ARTICLE, "Magazine Article"),
    (BLOG, "Blog"),
    (VIDEO_AND_ARTICLE, "Video & Audio"),
    (LITERATURE, "Literature"),
    (BOOKS, "Books")
)

NAME, DESIGNATION, CONTACTS = "Name", "Designation", "Contacts"
CONTACT_PERSON_CHOICES = (
    (NAME, "Name"),
    (DESIGNATION, "Designation"),
    (CONTACTS, "Contacts"),
)


PENDING, APPROVED, REJECTED = "Pending", "Approved", "Rejected"
CHANGE_REQUEST_STATUS_CHOICES = (
    (PENDING, "Pending"),
    (APPROVED, "Approved"),
    (REJECTED, "Rejected")
)


RESIGNED, TERMINATED, CONTRACT_COMPLETED = (
    "Resigned",
    "Terminated",
    "Contract Completed"
)

PARTING_REASON_CHOICES = (
    (RESIGNED, "Resigned"),
    (TERMINATED, "Terminated"),
    (CONTRACT_COMPLETED, "Contract Completed")
)


# ACCOUNT STATUS CHOICES
NOT_ACTIVATED, ACTIVE_USER, BLOCKED = "Not Activated", "Active", "Blocked"
CITIZENSHIP_CERTIFICATE, BIRTH_CERTIFICATE = 1, 2

DEPENDENT_DOCUMENT_TYPES = (
    (CITIZENSHIP_CERTIFICATE, 'citizenship certificate'),
    (BIRTH_CERTIFICATE, 'birth certificate')
) 

