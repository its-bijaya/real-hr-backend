import os
import random

import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


def fake_zero():
    with connection.cursor() as cursor:
        print("Resetting migrations.", end="")
        cursor.execute(
            "TRUNCATE TABLE django_migrations"
        )
        print(" [COMPLETE]")


if __name__ == '__main__':
    if input("Are you sure you want to fake all app migrations to zero? (yes/no) ") == 'yes':
        word = random.choice([
            "czechoslovakia",
            "pneumonia",
            "azithromycin",
            "Incomprehensibilities",
            "honorificabilitudinitatibus"
        ])
        try:
            if int(input(f"How many letters are there in {word}? ")) == len(word):
                fake_zero()
            else:
                raise AssertionError
        except (ValueError, AssertionError):
            print("Invalid option quiting.")
    else:
        print("Quiting script.")



