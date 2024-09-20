from django.core.management import BaseCommand

from irhrs.recruitment.models import City


class Command(BaseCommand):
    help = "Update country and province data in city model"

    def handle(self, *args, **options):
        for city in City.objects.all():
            city.save()
        print("Updated City fields")
