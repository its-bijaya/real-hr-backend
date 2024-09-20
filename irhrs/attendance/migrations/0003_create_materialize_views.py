# Custom migration to create materialized views for attendance break reports
from django.db import migrations
QUERY_1 = """
SELECT
      ROW_NUMBER() over (ORDER BY a.timesheet_id) as id,
      remark_category,
      a.timesheet_id,
      date_trunc('second', b.timestamp) - date_trunc('second', a.timestamp) as total_lost,
      a.timesheet_for,
      a.user_id
    FROM
      (SELECT
         ROW_NUMBER()
         OVER (
           PARTITION BY timesheet_id
           ORDER BY timestamp
           ) AS id,
         timesheet_id,
        timesheet.timesheet_user_id AS user_id,
        timesheet.timesheet_for AS timesheet_for,
         timestamp,
         remarks,
         remark_category
       FROM attendance_timesheetentry
         INNER JOIN attendance_timesheet timesheet
           on attendance_timesheetentry.timesheet_id = timesheet.id
       WHERE entry_type = 'Break Out') a
      LEFT JOIN
      (SELECT
         ROW_NUMBER()
         OVER (
           PARTITION BY timesheet_id
           ORDER BY timestamp
           ) AS id,
         timesheet_id,
         timestamp
       FROM attendance_timesheetentry
       WHERE entry_type = 'Break In') b
        on a.id = b.id and a.timesheet_id = b.timesheet_id
    ORDER BY b.timestamp - a.timestamp DESC NULLS LAST
"""
QUERY_2 = """
SELECT timesheet_id, SUM(total_lost) AS total_lost_due_to_in_between_breaks
FROM attendance_break_out_report_view GROUP BY timesheet_id
"""


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_auto_20210211_1614'),
    ]

    operations = [
        migrations.RunSQL(
            f"""
            CREATE MATERIALIZED VIEW attendance_break_out_report_view AS
            {QUERY_1};
            """,
            """
            DROP MATERIALIZED VIEW attendance_break_out_report_view;
            """
        ),
        migrations.RunSQL(
            f"""
                CREATE MATERIALIZED VIEW attendance_aggregate_breakout_result AS
                {QUERY_2};
                """,
            """
            DROP MATERIALIZED VIEW attendance_aggregate_breakout_result;
            """
        )
    ]
