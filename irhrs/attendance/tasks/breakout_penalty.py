from django.db import connection


def refresh_break_out_report_view():
    with connection.cursor() as cursor:
        cursor.execute(
            """REFRESH MATERIALIZED VIEW attendance_break_out_report_view;"""
        )

