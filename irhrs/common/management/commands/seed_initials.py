from django.core.management import BaseCommand

from irhrs.common.models import (Industry, DocumentCategory,
                                 ReligionAndEthnicity, HolidayCategory)
from irhrs.organization.models import (EmploymentLevel, EmploymentStatus)
from irhrs.core.constants.common import RELIGION, ETHNICITY
from irhrs.core.seeder import (DOCUMENT_CATEGORIES, INDUSTRIES, RELIGIONS,
                               ETHNICITIES, EMPLOYMENT_STATUS, EMPLOYMENT_LEVEL,
                               EMPLOYMENT_CHANGE_TYPES, HOLIDAY_CATEGORIES)


class Command(BaseCommand):
    help = 'Migrate initial data to database.'

    def handle(self, *args, **options):
        self.seed_document_categories()
        self.seed_industry()
        self.seed_religions_and_ethnicities()
        # self.seed_employment_level()
        # self.seed_employment_status()
        self.seed_holiday_categories()

    def seed_document_categories(self):
        for name in DOCUMENT_CATEGORIES:
            DocumentCategory.objects.get_or_create(name=name)
        self.stdout.write("Created Document Categories ...")

    def seed_industry(self):
        for name in INDUSTRIES:
            Industry.objects.get_or_create(name=name)
        self.stdout.write("Created Organization Industry ...")

    def seed_religions_and_ethnicities(self):
        for name in RELIGIONS:
            ReligionAndEthnicity.objects.get_or_create(
                name=name, category=RELIGION)
        self.stdout.write("Created Religions ...")
        for name in ETHNICITIES:
            ReligionAndEthnicity.objects.get_or_create(
                name=name, category=ETHNICITY)
        self.stdout.write("Created Ethnicities ...")

    def seed_employment_level(self):
        for title in EMPLOYMENT_LEVEL:
            EmploymentLevel.objects.get_or_create(organization_id=1,
                                                  title=title)
        self.stdout.write("Created Employment Level ...")

    def seed_employment_status(self):
        for title in EMPLOYMENT_STATUS:
            EmploymentStatus.objects.get_or_create(organization_id=1,
                                                   title=title)
        self.stdout.write("Created Employment Status ...")

    def seed_holiday_categories(self):
        for name in HOLIDAY_CATEGORIES:
            HolidayCategory.objects.get_or_create(name=name)
        self.stdout.write("Created Holiday Categories ...")
