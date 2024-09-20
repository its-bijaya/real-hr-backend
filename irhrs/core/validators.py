"""@irhrs_docs"""
import re
import magic

from dateutil import relativedelta
from dateutil.rrule import rrulestr
from django.conf import settings
from django.core.exceptions import ValidationError as CoreValidationError
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from config.settings import TEXT_FIELD_MAX_LENGTH
from .constants.common import RELIGION, ETHNICITY, MAX_CHRONIC_DISEASES, BOTH
from .constants.user import (CONTACT_CHOICES, CENTIMETERS, FOOT_INCHES,
                             POUNDS, KILOGRAMS, CONTACT_PERSON_CHOICES)
from .assertion import valid_instance_from_model
from .validation_messages import (
    USERDETAIL_REPLACING_MESSAGE, START_DATE_GREATER_MESSAGE,
    DOB_LESSER_MESSAGE, DOJ_LESSER_MESSAGE,
    END_DATE_CANNOT_SET_MESSAGE, MANDATORY_END_DATE_FOR_CONTRACT,
    END_DATE_GREATER_THAN_TODAY,
    END_DATE_IN_FUTURE_MESSAGE, END_DATE_REQUIRED)

INT_LIST_REGEX = r"(\d+,)*\d+"
ALLOW_PAST_REQUESTS = getattr(settings, 'ALLOW_PAST_REQUESTS_FOR_PRE_APPROVAL', False)


def validate_comma_separated_integers(string, message=None):
    """Validate that a string contains integers separated by comma"""
    if not re.fullmatch(INT_LIST_REGEX, string):
        if not message:
            message = _("This value must be comma separated numbers. Eg. 1,2,3")
        raise ValidationError(message)
    return string


def validate_image_size(file):
    """
    Raises Validation Error if the image size is greater than MAX_IMAGE_SIZE
    :param file:
    :return:
    """
    file_extension = file.name.split(".")[-1].lower()
    file_type = [k for k, v in settings.ACCEPTED_FILE_FORMATS.items() if
                 file_extension in v][0] \
        if [k for k, v in settings.ACCEPTED_FILE_FORMATS.items() if
            file_extension in v] else None
    if file_type == 'images':
        if file.size > settings.MAX_IMAGE_SIZE * 1024 * 1024:
            raise ValidationError("Image must be less than " +
                                  str(settings.MAX_IMAGE_SIZE) + " MB.")
    return file


def validate_natural_number(value):
    if value < 1:
        raise CoreValidationError(
            _('%(value)s is less than 1.'), params={'value': value},
        )


def validate_ethnicity(instance_id):
    """
    Validates for Ethnicity instance from ReligionAndEthnicity Model
    """
    from ..common.models.commons import ReligionAndEthnicity
    instance = valid_instance_from_model(instance_id, ReligionAndEthnicity)
    if instance.category != ETHNICITY:
        raise ValidationError(_("This field must be a valid Ethnicity."))
    return instance.id


def validate_religion(instance_id):
    """
    Validates for Religion instance from ReligionAndEthnicity Model
    """
    from ..common.models.commons import ReligionAndEthnicity
    instance = valid_instance_from_model(instance_id, ReligionAndEthnicity)
    if instance.category != RELIGION:
        raise ValidationError(_("This field must be a valid Religion."))
    return instance.id


# Validation for age
def validate_user_age(value):
    """
    Validates Age, raises validation error if age is not between 16-99
    :param value:
    :return:
    """
    if value < settings.MIN_USER_AGE or value > settings.MAX_USER_AGE:
        raise ValidationError(
            _(f"Age must be between {settings.MIN_USER_AGE} and "
              f"{settings.MAX_USER_AGE}"))
    return value


def validate_user_birth_date(value):
    age = (timezone.now().date() - value).days / 365
    if age < settings.MIN_USER_AGE or age > settings.MAX_USER_AGE:
        raise ValidationError(_(f"Invalid birth date. Age must be between "
                                f"{settings.MIN_USER_AGE} and "
                                f"{settings.MAX_USER_AGE}"))
    return value


def validate_extension_number(value):
    if value > 999999:
        raise ValidationError(
            "Ensure this value has not more than 6 characters")
    return value


def validate_past_date(value):
    """validates whether given date is from past or not. Raises error if not
    :param value: date to validate
    :type value: timezone.day()
    """
    if value:
        if value >= timezone.now().date():
            raise ValidationError(_('The date must be a past date.'))
    return value


def validate_past_date_or_today(value):
    """validates whether given date is from past, today or not. Raises error if not
        :param value: date to validate
        :type value: timezone.day()
        """
    if value:
        if value > timezone.now().date():
            raise ValidationError(_('The date must be a past date.'))
    return value


def validate_past_datetime(value):
    """validates whether given time is not from past or not"""
    if value:
        if value >= timezone.now():
            raise ValidationError(_('The time must be past.'))
    return value


def validate_future_date(value):
    """
    Raise exception if value is from past
    :param value: datetime to validate
    :type value: datetime
    :return: value
    """
    if value and value < timezone.now().date():
        raise ValidationError(_("This value can not be a past date."))
    return value


def validate_future_date_or_today(value):
    """
    Raise exception if value is from past or today
    :param value: datetime to validate
    :type value: datetime
    :return: value
    """
    if value and value <= timezone.now().date():
        raise ValidationError(_("This value must be a future date"))
    return value


def validate_future_datetime(value):
    """
    Raise exception if value is from past
    :param value: datetime to validate
    :type value: datetime
    :return: value
    """
    if value and value < timezone.now():
        raise ValidationError(_("This value can not be a past time."))
    return value


def validate_weight(obj, input_data):
    """
    Validate Weight for POUNDS and KILOGRAMS
    :param obj: object instance
    :param input_data: the validated_data
    :return: validation error or None
    """
    weight = input_data.get('weight') if 'weight' in input_data.keys() else \
        obj.weight if obj else None
    weight_unit = input_data.get(
        'weight_unit') if 'weight_unit' in input_data.keys() else \
        obj.weight_unit if obj else None
    weight = round(weight, 2)
    if weight_unit == POUNDS:
        if weight > 300 or weight < 60:
            raise ValidationError({'weight': 'The weight must be between '
                                             '60 and 300 lbs.'})
    elif weight_unit == KILOGRAMS:
        if weight < 25 or weight > 130:
            raise ValidationError({'weight': 'The weight must be between '
                                             '25 and 130 kgs.'})
    return


def validate_height(obj, input_data):
    """
    Validates Height for CENTIMETERS and FOOT_INCHES
    """
    height = input_data.get('height') if 'height' in input_data.keys() else \
        obj.height if obj else None
    height_unit = input_data.get(
        'height_unit') if 'height_unit' in input_data.keys() else \
        obj.height_unit if obj else None
    if height_unit == CENTIMETERS:
        if not 0 < float(height) < 300:
            raise ValidationError(
                {'height': 'The height is invalid. '
                           'Please make sure the height is under 300 cms'})
    elif height_unit == FOOT_INCHES:
        ft_in_regex = re.compile('(\d)|(\d\.\d{1,2})')
        if ft_in_regex.fullmatch(height):
            if '.' in height:
                _, inch = height.split('.')
                if len(inch) == 2:
                    if inch[0] > '1' or inch[1] not in ['0', '1']:
                        raise ValidationError(
                            {'height': 'The inches is not valid. Please make '
                                       'sure height is under 12 inches'})
        else:
            raise ValidationError({
                'height': 'Please enter a valid height. It must be under 300 '
                          'cms and inches must be under 12'})
    return


def has_no_parent(value):
    """
    Raise exception if value has parent
    Used while limiting self relation to depth 1
    """
    if getattr(value, 'parent', None):
        raise ValidationError(_('Child depth can not be more than 1'))
    return value


def validate_title(value):
    """
    Accept Title Characters.
    Must start with a Character.
    Can Contain Alpha-Numeric Characters.
    Special Characters allowed ampersand, hyphen, question, space and parenthesis
    """
    # TODO: define class that accepts allowed symbols or regex and matches
    # 100+ Usage. Recommended????
    # because title requirements can be different for different models
    title_regex = re.compile('[A-Za-z][\w\-&. ?/,\(\)]*')
    if title_regex.fullmatch(value):
        return value
    raise ValidationError(_("This field must start with a Character. "
                            "Can only contain space, parenthesis, alphanumeric and -?&./,"))


def validate_description(value):
    """
        :raise ValidationError if length is greater than config.settings.TEXT_FIELD_MAX_LENGTH
    """
    if len(value) > TEXT_FIELD_MAX_LENGTH:
        raise ValidationError(
            _("This field must be less than "
              f"{TEXT_FIELD_MAX_LENGTH} characters")
        )
    return value


def validate_address(value):
    """Validate address string"""
    address_regex = re.compile('\w[\w\-, .]*')
    if address_regex.fullmatch(value):
        return value
    raise ValidationError(_("This field must start with a Alphanumeric. "
                            "Can only contain space, alphanumeric, comma,"
                            "dot and -. "))


def validate_invalid_chars(value):
    """
    Raise Validation Error if contains any special character except - or space.
    """
    special_character_regex = re.compile('[^\-\s\w]')
    if special_character_regex.search(value):
        raise ValidationError(_("Special Characters except '-' are not "
                                "supported."))
    return value


def validate_has_digit(value):
    """
    Raise Validation Error if the input does not contain digits.
    """
    if value == '':
        return value
    numeric_input_regex = re.compile('\d')
    if not numeric_input_regex.search(value):
        raise ValidationError(_("The field must contain at least one number"))
    return value


def validate_is_hex_color(value):
    """
    Raise Validation Error if the input does not contain hex color code.
    Sample color code #00FF11AA
    """
    if value == '':
        return value
    color_regex = re.compile('^#([0-9a-fA-F]{8})$')
    if not color_regex.search(value):
        raise ValidationError(_("The field must contain hex color code"))
    return value


def validate_contact_regex(regex, contact, accepts_slash=False):
    # extra validator for braces enclosure
    # TODO: @Ravi Handle Braces properly.
    open_brace, close_brace = re.compile(r'.*\(.*'), re.compile(r'.*\).*')
    num_match = regex.fullmatch(contact)
    open_match = open_brace.fullmatch(contact)
    close_match = close_brace.fullmatch(contact)
    error_msg = "The Phone number format is not valid. It must be 3 to 20 in length and there " \
                "can be numbers, hyphens"
    if num_match and not (bool(open_match) - bool(close_match)):
        pass
    else:
        if accepts_slash:
            raise ValidationError(error_msg + ", slash(/) and braces.")
        raise ValidationError(error_msg + " and braces.")


def validate_json_contact(contacts):
    """
    Validator for Contact, which has JSONTextField.
    """
    if not isinstance(contacts, dict):
        raise ValidationError(_("Value must be valid JSON."))
    for contact_type, contact_value in contacts.items():
        if contact_type not in (x[1] for x in CONTACT_CHOICES):
            raise ValidationError(
                f'{contact_type} is not a valid contact type')
        number_regex = re.compile(r'^[+\d()\-]{3,20}$')
        validate_contact_regex(number_regex, contact_value)

    return contacts


def validate_json_contact_in_branch(contacts):
    """
        Validation for contacts field which is currently json.
        Supports multiple contacts separated by /
    """
    if not isinstance(contacts, dict):
        raise ValidationError(_("Value must be valid JSON."))
    for contact_type, contact_value in contacts.items():
        if len(contact_value) > 255:
            raise ValidationError("The length of contact cannot be more than 255.")
        if contact_type not in (x[1] for x in CONTACT_CHOICES):
            raise ValidationError(
                f'{contact_type} is not a valid contact type')

        number_regex = re.compile(r'^([+\d()\-]{3,20})(\/[+\d()\-]{3,20})*$')
        validate_contact_regex(number_regex, contact_value, accepts_slash=True)

    return contacts


def validate_phone_number(phone_number):
    number_regex = re.compile(r'^[+\d\(\)\-\s]+$')
    if not number_regex.fullmatch(phone_number):
        raise ValidationError("The Phone number format is not valid. "
                              "There can be numbers, hyphens and braces.")
    return phone_number


def validate_unique_source(required_fields):
    """
    TODO: @ravi write docstring about the unique source.
    """
    ret = None
    field_names = ', '.join(required_fields.keys())
    sum = 0
    for field_name, field_value in required_fields.items():
        if field_value:
            ret = field_name
            sum += 1
        if sum > 1:
            raise ValidationError(_("Ensure one and only one parameter is set"
                                    "out of {}".format(field_names)))
    if sum == 0:
        raise ValidationError(_(
            "Ensure at least one parameter is set out of {}".format(
                field_names)))
    return ret


def validate_start_end_date(start_date, end_date, self_object=None,
                            current_boolean=empty, duration=empty):
    if start_date and start_date > timezone.now().date():
        raise ValidationError('Start date must not be in future.')
    if end_date and end_date > timezone.now().date():
        raise ValidationError('End date must not be in future.')
    if (start_date and end_date) and (start_date > end_date):
        raise ValidationError("Start date must not be greater than end date.")
    if not current_boolean == empty:
        if current_boolean and end_date:
            raise ValidationError('There could not be end date if current is '
                                  'checked ')

        if not current_boolean and not end_date:
            if self_object and self_object.partial:
                pass
            else:
                raise ValidationError('End date is required if'
                                      ' current is not checked.')
    if not duration == empty:
        if start_date and end_date:
            months = relativedelta.relativedelta(end_date, start_date).months
            if not months == duration:
                raise ValidationError("Entered duration and duration from end "
                                      "date and start date don't match.")


def validate_contact_person(contact_person):
    """
    Validator for Contact, which has JSONTextField.
    """
    person_list = contact_person.get('person_list')
    if contact_person:
        if not isinstance(person_list, list):
            raise ValidationError("List of contact person is expected.")
        try:
            for person in person_list:
                if not isinstance(person, dict):
                    raise ValidationError(f"{person} must be valid JSON.")
                for key, value in person.items():
                    if key not in (x[1] for x in CONTACT_PERSON_CHOICES):
                        raise ValidationError(
                            f'{key} is not a valid field for contact person.')
                    if key == "Contacts":
                        # just some hacks to re-raise the validation error in the form of k:v
                        try:
                            validate_json_contact(value)
                        except ValidationError as v_error:
                            if len(v_error.args) >= 0:
                                raise ValidationError(
                                    [{key: v_error.args[0]}]) from v_error
                            raise
                    else:
                        # just some hacks to re-raise the validation error in the form of k:v
                        try:
                            validate_title(value)
                        except ValidationError as v_error:
                            if len(v_error.args) >= 0:
                                raise ValidationError(
                                    [{key: v_error.args[0]}]) from v_error
                            raise

        except AttributeError:
            pass
    if not isinstance(contact_person, dict):
        raise ValidationError("Value must be valid JSON.")
    return contact_person


def key_exists(key, dictionary):
    """
    Returns True if key exist in dictionary
    :param key: key to test
    :param dictionary: dictionary
    :return: True or False
    """
    return key in dictionary.keys()


def validate_text_only(value):
    if re.fullmatch(r'[a-zA-Z \.]+', value):
        return
    raise ValidationError(_("The field must contain only alphabets."))


def validate_names_only(value):
    if re.fullmatch(r'[a-zA-Z \.-]+', value):
        return
    raise ValidationError(_("The field must contain only alphabets."))


def validate_chronic_disease(value):
    if type(value) == list:
        if len(value) > MAX_CHRONIC_DISEASES:
            raise ValidationError({
                'chronic_disease': f"The chronic diseases must be less than "
                                   f"{MAX_CHRONIC_DISEASES}"
            })
    return


def validate_image_file_extension(file):
    file_extension = file.name.split('.')[-1]
    if file_extension.lower() in settings.ACCEPTED_FILE_FORMATS.get('images'):
        return
    raise ValidationError(_(f'Invalid file format .{file_extension}.'))


def validate_wysiwyg_field(value):
    # Limit set to 100.000
    if len(value) > 1000000:
        raise ValidationError(_('This field must be less than 1000000 characters.'))
    return value


# UserExperience Validators
"""
Data to Validate:

{
    "replacing":
    "userdetail":
    "start_date":
    "end_date":
    "emp_status":
    "is_current":
}

"""


def throw_validation_error(field=None, message=''):
    if field:
        raise ValidationError({
            field: message
        })
    raise ValidationError(message)


def validate_userdetail_replacing(replacing, user):
    if (
        replacing and user
        and user == replacing
    ):
        throw_validation_error('replacing', USERDETAIL_REPLACING_MESSAGE)


def validate_start_end_dob_doj_dates(
    user, start_date, end_date
):
    """
    :Assumptions:
        userdetail and start_date is compulsory
    :param user:
    :param start_date: start date of employment
    :param end_date: end date of employment
    """
    userdetail = getattr(user, 'detail', None)
    joined_date = getattr(userdetail, 'joined_date', None)
    dob = getattr(userdetail, 'date_of_birth', None)
    if end_date and start_date and start_date > end_date:
        throw_validation_error('start_date', START_DATE_GREATER_MESSAGE)
    if dob and start_date and dob > start_date:
        throw_validation_error('start_date', DOB_LESSER_MESSAGE)
    if joined_date and start_date and joined_date > start_date:
        throw_validation_error('start_date', DOJ_LESSER_MESSAGE)


def validate_contract_current(
    employment_status, end_date, is_current
):
    if employment_status and employment_status.is_contract:
        if not end_date:
            throw_validation_error(
                'end_date', MANDATORY_END_DATE_FOR_CONTRACT
            )
        if is_current and end_date and end_date < timezone.now().date():
            throw_validation_error(
                'end_date', END_DATE_GREATER_THAN_TODAY
            )


def validate_end_date_is_current(
    end_date, is_current, employment_status
):
    if is_current:
        if end_date and not employment_status.is_contract:
            throw_validation_error(
                'end_date', END_DATE_CANNOT_SET_MESSAGE
            )
    else:
        if not end_date:
            throw_validation_error(
                'end_date', END_DATE_REQUIRED
            )
        elif end_date > timezone.now().date():
            throw_validation_error(
                'end_date', END_DATE_IN_FUTURE_MESSAGE
            )


# used in leave rule time off
def validate_multiple_of_half(value):
    """
    raise validation error when field is not multiple of 0.5 or 1/5
    eg. valid: 0.5, 1.0, 1.5, 2.0.., invalid: 1.2, 1.3, 3.6, ...

    :param value: value to be validated
    :type value: float
    :return: value
    """
    if not (value % 0.5 == 0.0):
        raise ValidationError(_("The value must be multiple of 0.5"))
    return value


def validate_recurring_rule(value):
    """
    Validates recurring rule

    :param value: recurring_rule
    :return: validated_rule
    """
    if not ('count' in value.lower() or 'until' in value.lower()):
        # value = value+";UNTIL={}".format(
        # "".join(timezone.now().date().replace(
        # month=12, day=31).__str__().split('-')
        # ))
        raise ValidationError('Should contain run limit COUNT or UNTIL date')

    if 'count' in value.lower() and 'until' in value.lower():
        raise ValidationError(
            'Cannot contain End date and Iteration count at the same time ')

    if 'hourly' in value.lower():
        raise ValidationError('Cannot set frequency as HOURLY')
    rule_dict = {i.split('=')[0].lower(): i.split('=')[1] for i in
                 value.split(';')}
    if 'until' in rule_dict.keys():
        # maybe we also need to check if its a valid date in future
        # as a fallback rrulestr(str(value)) will handle everything
        if not rule_dict.get('until'):
            raise ValidationError('End Date cannot be blank')
    if 'count' in rule_dict.keys():
        if not rule_dict.get('count'):
            raise ValidationError('Total Repetitions Count cannot be blank')
    try:
        rrulestr(str(value))
    except (ValueError, AttributeError):
        raise ValidationError('Invalid rule format')
    return value


@deconstructible
class MinMaxValueValidator:
    message = _(
        'Ensure this value is between {min_value} and {max_value} (it is {show_value}).')
    code = 'limit_value'

    def __init__(self, min_value, max_value, message=None):
        self.min_value = min_value
        self.max_value = max_value

        if message:
            self.message = message

    def __call__(self, value):
        params = {'min_value': self.min_value, 'max_value': self.max_value,
                  'show_value': value, 'value': value}
        if self.compare(value, self.min_value, self.max_value):
            raise ValidationError(self.message.format(**params), code=self.code)

    @staticmethod
    def compare(value, min_value, max_value):
        return not (min_value <= value <= max_value)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.min_value == other.min_value and
            self.max_value == other.max_value and
            self.message == other.message and
            self.code == other.code
        )


@deconstructible
class DocumentTypeValidator:
    message = _(
        'The document type must be of association type {association} or Both.')
    code = 'invalid_type'

    def __init__(self, association_type, message=None):
        self.association_type = association_type

        if message:
            self.message = message

    def __call__(self, value):
        params = {'association': self.association_type, 'value': value}
        if self.compare(value, self.association_type):
            raise ValidationError(self.message.format(**params), code=self.code)

    @staticmethod
    def compare(value, association_type):
        return value.associated_with not in [association_type, BOTH]

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.document_type == other.document_type and
            self.message == other.message and
            self.code == other.code
        )


def validate_prior_approval_requests(date):
    if ALLOW_PAST_REQUESTS:
        return
    validate_future_date(date)


def validate_username(username):
    username_regex = re.compile(r'([a-zA-Z0-9][a-zA-Z0-9_.@-]?)+')
    if not username_regex.fullmatch(username):
        raise ValidationError(
            'Username may only contain alphabets(a-z), numbers(0-9), underscores(_),'
            'at(@), hyphen(-) and period(.)'
        )
    return username.lower()


def validate_fiscal_year_months_amount(fiscal_year_months: QuerySet, fiscal_year_months_amount: dict):
    """Validate fiscal year months amount for user voluntary rebate

    :param fiscal_year_months: current fiscal year months which is fed from FiscalYear model
    :param fiscal_year_months_amount: actual JSONField stored in UserVoluntaryRebate model
    """

    if not isinstance(fiscal_year_months_amount, dict):
        raise ValidationError(_("Value must be valid JSON."))

    fiscal_year_months = {fiscal_year_month[0] for fiscal_year_month in fiscal_year_months}

    if set(fiscal_year_months_amount.keys()) != fiscal_year_months:
        raise ValidationError(_("Fiscal year months mismatched."))

    if any(float(x) < 0 for x in fiscal_year_months_amount.values()):
        raise ValidationError(_("Only positive value supported for fiscal months amount."))

    try:
        all(type(float(x)) == float for x in fiscal_year_months_amount.values())
    except ValueError:
        raise ValidationError(_("Only integer and float field supported for fiscal months amount."))

class ExcelFileValidator:
    """
    Excel file validator for validating uploaded file.

    This validator checks if an uploaded file is a valid Excel file by examining
    its extension and content type. Validating a file based solely on its
    extension can be unreliable, as file extensions can be easily changed or
    manipulated. Therefore, this validator also examines the content type of
    the file to ensure that it is a valid Excel file
    """

    def __call__(self, file):
        file_type = magic.from_buffer(file.read(1024), mime=True)
        if file_type != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            raise ValidationError('Invalid file type. Expected an Excel file.')
        return file
