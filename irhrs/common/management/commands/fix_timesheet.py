from django.core.management import BaseCommand

try:
    from irhrs.attendance.models import TimeSheet

    from irhrs.attendance.managers.utils import fix_entries_on_commit
except ImportError:
    class TimeSheet:
        class Manager:
            def all(self):
                return []

            def iterator(self, chunk_size=None):
                return self.all()

        objects = Manager()


    def fix_entries_on_commit(instance, send_notification=True):
        pass


class Command(BaseCommand):
    help = "Fix time sheets entries"

    def handle(self, *args, **options):
        print("Fixing TimeSheet Entries")
        for time_sheet in TimeSheet.objects.iterator(chunk_size=10000):
            print("Doing fix for", time_sheet)
            fix_entries_on_commit(time_sheet, send_notification=False)

        print("Successfully Fixed Entries")
