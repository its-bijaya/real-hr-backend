(FORM, ) = ("Form",)
QUESTION_SET_CHOICES = (
    (FORM, "Form")
)

(
    DRAFT, REQUESTED, PENDING, IN_PROGRESS, APPROVED, DENIED
) = (
    "draft", "requested", "pending", "in progress", "approved", "denied"
)

FORM_STATUS = (
    (REQUESTED, REQUESTED),
    (APPROVED, APPROVED),
    (DENIED, DENIED)
)

ANSWER_SHEET_APPROVAL_STATUS = (
    (APPROVED, APPROVED),
    (DENIED, DENIED)
)

DYNAMIC_FORM_STATUS = (
    (DRAFT, DRAFT),
    (PENDING, PENDING),
    (IN_PROGRESS, IN_PROGRESS),
    (APPROVED, APPROVED),
    (DENIED, DENIED),
    ("", "")
)
