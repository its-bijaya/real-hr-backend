#### Decoupled migrations for Task and Hris

- python manage.py migrate --fake task zero
- REMOVE HRIS DEPENDENCY FROM user 0001 and 0010
- python manage.py migrate --fake hris zero
- then checkout to migration-refactor
- manually add task and user migrations in django_migrations table
--- users , 0021_auto_20190502_1838
--- task , 0001_initial
- python manage.py migrate 