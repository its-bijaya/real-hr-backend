import logging
from django_q.tasks import async_task

from irhrs.export.constants import FAILED

logger = logging.getLogger(__name__)


def begin_export(*args, **kwargs):
    async_task(
        process_export,
        *args,
        **kwargs
    )


def process_export(cls, queryset, export_fields, export_instance, extra_content, description=None):
    try:
        logger.info(f"Preparing export for {export_instance.__str__()}")
        file_content = cls.get_exported_file_content(
            queryset,
            title=export_instance.title[:30],
            columns=export_fields,
            extra_content=extra_content,
            description=description
        )
        cls.save_file_content(export_instance, file_content)
    except Exception as e:
        import traceback
        export_instance.remarks = str(e)[:255]
        export_instance.traceback = str(traceback.format_exc())
        export_instance.status = FAILED
        logger.error(f"Could not complete export for {export_instance.__str__()}", exc_info=True)
        export_instance.save()
