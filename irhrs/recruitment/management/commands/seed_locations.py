import json
import os

from django.conf import settings
from django.core.management import BaseCommand

from irhrs.recruitment.models import Country, City, District, Province
with open(
    os.path.abspath(
        os.path.join(
            settings.PROJECT_DIR,
            'fixtures/commons/locations.json'
        )
    )
) as f:
    location_data = json.load(f)
    COUNTRIES = location_data['countries']
    PROVINCES = location_data['provinces']
    DISTRICTS = location_data['districts']
    CITIES = location_data['cities']


class Command(BaseCommand):
    help = "Populate database with location"

    def handle(self, *args, **options):
        count = 0

        # Seed countries
        for count, country_data in enumerate(COUNTRIES, start=1):
            _id = country_data.pop('id')
            Country.objects.get_or_create(id=_id, defaults=country_data)
        print(f"Seeded {count} countries.")

        # seed provinces
        nepal = Country.objects.get(name="Nepal")
        for count, province in enumerate(PROVINCES, start=1):
            _id = province.pop('id')
            province.update({"country": nepal})
            Province.objects.get_or_create(id=_id, defaults=province)
        print(f"Seeded {count} provinces.")

        for count, district in enumerate(DISTRICTS, start=1):
            _id = district["id"]

            data = {
                "province_id": district["province_id"],
                "name": district["name"].title(),
                "alternative_names": district.get("alternative_names", []),
                "alternative_names_ne": district.get("alternative_names_ne", [])
            }
            District.objects.get_or_create(id=_id, defaults=data)
        print(f"Seeded {count} districts.")

        for count, city in enumerate(CITIES, start=1):
            _id = city.pop("id")
            City.objects.get_or_create(id=_id, defaults=city)

        print(f"Seeded {count} cities.")
