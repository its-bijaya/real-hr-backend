from irhrs.core.constants.common import P_TASK

TASK_REPORT_PERMISSION = {
    "name": "Can generate/download task report.",
    "code": "8.01",
    "category": P_TASK,
    "organization_specific": False,
}

TASK_APPROVALS_PERMISSION = {
    "name": "Can approve task.",
    "code": "8.02",
    "category": P_TASK,
    "organization_specific": False,
}

TASK_PROJECT_PERMISSION = {
    "name": "Can create task project.",
    "code": "8.04",
    "category": P_TASK,
    "organization_specific": False,
}
