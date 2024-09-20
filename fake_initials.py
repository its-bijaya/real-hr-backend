import os
import django
from django.core.management import call_command

# no need to perform now, new migrations are already commited
# Delete all migrations
# find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
# find . -path "*/migrations/*.pyc"  -delete

# Create new migrations


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


def main():
    call_command('migrate', fake=True)


if __name__ == "__main__":
    main()
