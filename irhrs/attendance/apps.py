from django.apps import AppConfig


def initialize_pymysql():
    """
        Initialization requirement for pymysql.
        Original location config/__init__.py
    """
    from django.conf import settings
    if settings.USING_ADMS:
        import pymysql
        # TODO ensure maintaining version in config/settings.py
        # For adms, mysqlclient version and pymysql version is mismatched, assign version to match
        # accordingly.
        pymysql.version_info = (2, 1, 0, "final", 0)
        pymysql.install_as_MySQLdb()


class AttendanceConfig(AppConfig):
    name = 'irhrs.attendance'

    def ready(self):
        from . import signals
        initialize_pymysql()
