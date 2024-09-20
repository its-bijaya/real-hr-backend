from irhrs.core.constants.common import P_ASSESSMENT, P_TRAINING, P_QUESTIONNAIRE

FULL_ASSESSMENT_PERMISSION = {
    "name": "Has Complete Permission in Assessment.",
    "code": "13.00",
    "category": P_ASSESSMENT,
    "organization_specific": True,
    "description": ""
}

ASSESSMENT_READ_ONLY_PERMISSION = {
    "name": "Has read-only Permission in Assessment.",
    "code": "13.99",
    "category": P_ASSESSMENT,
    "organization_specific": True,
    "description": ""
}


ASSESSMENT_SET_PERMISSION = {
    "name": "Can Create Assessments, Sections, etc.",
    "code": "13.01",
    "category": P_ASSESSMENT,
    "organization_specific": True,
    "description": ""
}

ASSESSMENT_ASSIGN_PERMISSION = {
    "name": "Can Assign assessments to users.",
    "code": "13.02",
    "category": P_ASSESSMENT,
    "organization_specific": True,
    "description": ""
}

ASSESSMENT_REVIEW_PERMISSION = {
    "name": "Can Review and rate answered assessments.",
    "code": "13.03",
    "category": P_ASSESSMENT,
    "organization_specific": True,
    "description": ""
}
ASSESSMENT_SCORE_PERMISSION = {
    "name": "Can view assessment scores and send user to a training.",
    "code": "13.04",
    "category": P_ASSESSMENT,
    "organization_specific": True,
    "description": ""
}

ASSESSMENT_ATTACH_QUESTIONS_PERMISSION = {
    "name": "Can attach questions to assessment sections.",
    "code": "13.05",
    "category": P_ASSESSMENT,
    "organization_specific": True,
    "description": ""
}

FULL_TRAINING_PERMISSION = {
    "name": "Has complete permission in Training.",
    "code": "14.00",
    "category": P_TRAINING,
    "organization_specific": True,
    "description": ""
}

TRAINING_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in Training.",
    "code": "14.99",
    "category": P_TRAINING,
    "organization_specific": True,
    "description": ""
}

TRAINING_CREATE_PERMISSION = {
    "name": "Can create Trainings.",
    "code": "14.01",
    "category": P_TRAINING,
    "organization_specific": True,
    "description": ""
}

TRAINING_ASSIGN_PERMISSION = {
    "name": "Can assign users to trainings.",
    "code": "14.02",
    "category": P_TRAINING,
    "organization_specific": True,
    "description": ""
}

TRAINER_PROFILE_PERMISSION = {
    "name": "Can create/modify Trainer's Profile.",
    "code": "14.03",
    "category": P_TRAINING,
    "organization_specific": True,
    "description": ""
}

FULL_QUESTIONNAIRE_PERMISSION = {
    "name": "Has complete permission in Questionnaire.",
    "code": "15.00",
    "category": P_QUESTIONNAIRE,
    "organization_specific": True,
    "description": ""
}

QUESTIONNAIRE_READ_ONLY_PERMISSION = {
    "name": "Has read-only permission in Questionnaire.",
    "code": "15.99",
    "category": P_QUESTIONNAIRE,
    "organization_specific": True,
    "description": ""
}

QUESTIONNAIRE_READ_PERMISSION = {
    "name": "Can view Questions.",
    "code": "15.01",
    "category": P_QUESTIONNAIRE,
    "organization_specific": True,
    "description": ""
}
