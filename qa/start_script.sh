#!/bin/bash

# finds out major psql version installed
psql_version=$(psql -V | awk 'split($3, arr, ".") {print arr[1]}')
pg_ctlcluster $psql_version main start

su - postgres -c "createdb qarhrs"

su - postgres -c "psql -c \"CREATE ROLE qa WITH PASSWORD 'qapass'\""

su - postgres -c "psql -c \"ALTER ROLE qa WITH LOGIN;\""

# su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE \"qarhrs\" to qa;\""

# su - postgres -c "psql qarhrs -c \"GRANT ALL ON ALL TABLES IN SCHEMA public to qa;\""
# su - postgres -c "psql qarhrs -c \"GRANT ALL ON ALL SEQUENCES IN SCHEMA public to qa;\""
# su - postgres -c "psql qarhrs -c \"GRANT ALL ON ALL FUNCTIONS IN SCHEMA public to qa;\""

redis-server --daemonize yes

FILE=/dbdump/dump.sql
if [[ -f "$FILE" ]]; then
    # su - postgres -c "psql -d qarhrs -f $FILE"
    su - postgres -c "pg_restore --no-owner --role=qa --verbose -d qarhrs $FILE"
else
    echo "$FILE does not exist."
fi

su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE \"qarhrs\" to qa;\""

su - postgres -c "psql qarhrs -c \"GRANT ALL ON ALL TABLES IN SCHEMA public to qa;\""
su - postgres -c "psql qarhrs -c \"GRANT ALL ON ALL SEQUENCES IN SCHEMA public to qa;\""
su - postgres -c "psql qarhrs -c \"GRANT ALL ON ALL FUNCTIONS IN SCHEMA public to qa;\""

python manage.py migrate
python manage.py collectstatic

python manage.py setup_hrs_permissions
python manage.py schedule_tasks_non_interactive

# set -m

# python manage.py qcluster 2> qcluster_error_log.log > qcluster_output.log &
python manage.py qcluster &> qcluster.log &
# daphne config.asgi:application -b 0.0.0.0 -p 8000
python manage.py runserver 0.0.0.0:8000

# fg %1
