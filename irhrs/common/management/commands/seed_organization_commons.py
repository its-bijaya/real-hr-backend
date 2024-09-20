import os
import pickle

from django.conf import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Initial Data for Notification templates"

    def handle(self, *args, **options):
        commons = [
            'holiday_category',
            'disability',
            'document_category',
        ]

        for file in commons:
            with open(
                    os.path.join(
                        settings.PROJECT_DIR,
                        f'fixtures/commons/{file}.pkl',
                    ),
                    'rb'
            ) as fp:
                objects = pickle.load(fp)
            for q in objects:
                try:
                    q.save()
                except:
                    pass
