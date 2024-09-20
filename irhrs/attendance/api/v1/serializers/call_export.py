from django_q.tasks import async_task

from .process_export import export_failed, _save_file
save_file = _save_file


def import_attendance(*args, **kwargs):
    async_task(
        export_failed,
        *args,
        **kwargs
    )
