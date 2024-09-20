"""@irhrs_docs"""


def check_in_setting(master_setting, field):
    return getattr(master_setting, field)
