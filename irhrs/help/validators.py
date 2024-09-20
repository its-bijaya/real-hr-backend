import re
from rest_framework.exceptions import ValidationError


def validate_title(value):
    """
    Accept Title Characters.
    Must start with a Character.
    Can Contain Alpha-Numeric Characters.
    Special Characters allowed ampersand, hyphen, question, space.
    """
    title_regex = re.compile('[A-Za-z][\w\-&. ?/,]*')
    if title_regex.fullmatch(value):
        return value
    raise ValidationError(_("This field must start with a Character. "
                            "Can only contain space, alphanumeric and -?&./,"))


def validate_invalid_chars(value):
    """
    Raise Validation Error if contains any special character except - or space.
    """
    special_character_regex = re.compile('[^\-\s\w]')
    if special_character_regex.search(value):
        raise ValidationError(_("Special Characters except '-' are not "
                                "supported."))
    return value
