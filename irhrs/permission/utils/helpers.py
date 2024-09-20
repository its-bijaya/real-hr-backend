"""@irhrs_docs"""
def is_supervisor(user):
    """
    check whether the user is still supervisor i.e. supervisor of at least one
    employee
    """
    return user.as_supervisor.all().exists()


def is_org_head(user):
    """
    check whether the user is still organization head i.e. head of at least
    one organization
    """
    return user.org_head_of.all().exists()


def is_division_head(user):
    """
    check whether user is still division head i.e. head of at least one
    division
    """
    return user.detail.division_head.filter(is_archived=False).exists()


def is_branch_manager(user):
    """
    check whether user is still branch head i.e. head of at least one
    branch
    """
    return user.detail.branch_manager_of.all().exists()
