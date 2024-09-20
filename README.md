# iRealHRSoft [![CI](https://github.com/aayulogic/irealhrsoft-backend/actions/workflows/main.yml/badge.svg?branch=stage)](https://github.com/aayulogic/irealhrsoft-backend/actions/workflows/main.yml)
## [Complete HR Intelligence Technology](https://realhrsoft.com/)


# Readme
1. [Installation](#installation)
    1.  [On ubuntu 20.04 LTS](#org55972aa)
    2.  [On Arch linux](#orgd5e1425)
    3.  [Frequently used commands](#org23af2b4)
        1.  [To take DB dump:](#orgd782175)
        2.  [To restore DB dump:](#org9b634dc)
        3.  [QA/QC server shortcuts](#orgd52908a)
            1.  [To copy dump from container to local PC:](#orga402f7a)
            2.  [To ssh inside the container](#org199b5d5)
2. [Docker](#docker)
3. [Merging guidelines](#merging_guidelines)


<a id="org55972aa"></a>

# Installation
<a id="installation"></a>
## Installation on ubuntu 20.04 LTS

1.  Install git.
    ```
    sudo apt install git
    ```
2.  Clone backend repository:
   ```
    git clone https://github.com/aayulogic/irealhrsoft-backend.git && cd irealhrsoft-backend
   ```
3.  Setup virtual env
    ```
    sudo apt install python3-venv
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  Install requirements and their dependencies
    ```
    sudo apt install gcc python3-dev
    pip3 install wheel
    pip3 install -r requirements/dev.txt
    ```
5.  Configure settings
    ```
    cp .env.sample .env
    ```
6.  Setup PostgreSQL
    ```
    sudo apt install postgresql postgresql-contrib
    sudo systemctl enable postgresql.service && sudo systemctl start postgresql.service

    # login as postgres user
    sudo -iu postgres

    # IMPORTANT: while performing createuser, use currently logged in users name for the role name field.
    # Type `whoami` in a terminal to know the current users name.
    createuser --interactive --pwprompt
    ```
7.  Exit the postgres user shell by typing \`exit\` and from normal users terminal do the following:
    ```
    createdb <db_name_here>
    ```

8.  Update the following variables in `.env` file according to the newly created role and `db_name`.
    ```
    # for example:
    DATABASE_NAME='realhrsoft'
    DATABASE_USER='john'
    DATABASE_PASSWORD='password'
    ```
9.  Install redis
    ```
    sudo apt install redis-server
    sudo systemctl enable redis-server.service && sudo systemctl start redis-server.service
    ```

10.  Generate RSA keys
   ```
    python manage.py generate_rsa_keys
   ```

11.  Migrations and databases:

   We can either use a database dump with prepoulated dump(request DB dump with someone from the team) or apply migrations ourselves. The first way is the recommended approach because its quicker and comes with preloaded data. If you want to do the latter, try this:

```
    # Add admin user to the system, create first organization
    ./manage.py initial_setup
    ./manage.py call_seeders
    ./manage.py seed_org_data
    ./manage.py seed_organization_commons
    ./manage.py schedule_tasks
    ./manage.py seed_id_cards
    ./manage.py seed_notification_templates
    ./manage.py setup_hrs_permissions
    ./manage.py seed_locations

    ./manage.py seed_initials
    ./manage.py update_system_admin
```


<a id="orgd5e1425"></a>

## Installation on Arch linux

1.  Update your system:
    ```
    sudo pacman -Syyu
    ```
2.  Install git
    ```
    sudo pacman -S git
    ```
3.  Clone backend repository
    ```
    git clone https://github.com/aayulogic/irealhrsoft-backend.git && cd irealhrsoft-backend
    ```

4.  Setup virtual env
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```

5.  Install requirements and their dependencies
    ```
    sudo pacman -S python3 python-lxml gcc mysql
    pip3 install wheel
    pip3 install -r requirements/dev.txt
    ```

6.  Configure settings
    ```
    cp .env.sample .env
    ```

7.  Setup PostgreSQL

    ```
    sudo pacman -S postgresql

    # login as postgres user
    sudo -iu postgres

    initdb -D /var/lib/postgres/data

    # IMPORTANT: while performing createuser, use currently logged in users name for the role name field.
    # Type `whoami` in a terminal to know the current users name.
    createuser --interactive --pwprompt

    ```

8.  Exit the postgres user shell by typing \`exit\` and from normal users terminal do the following:
```
    sudo systemctl enable postgresql.service && sudo systemctl start postgresql.service
    createdb <db_name_here>
```

9.  Update the following variables in `.env` file according to the newly created role and `db_name`.
```
    DATABASE_NAME
    DATABASE_USER
    DATABASE_PASSWORD
```

10.  Install redis
```
    sudo pacman -S redis
    sudo systemctl enable redis.service && sudo systemctl start redis.service
```

11.  Generate RSA keys

```
    python manage.py generate_rsa_keys
```

12.  Migrations and databases:

  We can either use a database dump with prepoulated dump(request DB dump with someone from the team) or apply migrations ourselves. The first way is the recommended approach because its quicker and comes with preloaded data. If you want to do the latter, try this:
```
    # Add admin user to the system, create first organization
    ./manage.py initial_setup
    ./manage.py call_seeders
    ./manage.py seed_org_data
    ./manage.py seed_organization_commons
    ./manage.py schedule_tasks
    ./manage.py seed_id_cards
    ./manage.py seed_notification_templates
    ./manage.py setup_hrs_permissions
    ./manage.py seed_locations

    ./manage.py seed_initials
    ./manage.py update_system_admin
```


<a id="org23af2b4"></a>

# Frequently used commands


<a id="orgd782175"></a>

## To take DB dump:

    pg_dump <database_name> <destination_path>
    #for eg:
    pg_dump realhrsoft > ~/Downloads/question_set_changed.sql


<a id="org9b634dc"></a>

## To restore DB dump:

**IMPORTANT: Always do the following before restoring dump:**
```
    dropdb <database_name>
    createdb <database_name>
```
Dump restore instructions
```
    # for .dump format
    pg_restore --no-owner --role=<role_name> -d <database_name> <dump_file_path>
    # for eg, to restore reassign.dump into table called realhrsoft:
    pg_restore --no-owner --role=john -d realhrsoft ~/Downloads/reassign.dump
    # for .sql format dumps
    psql -d <database_name> < <path_to_sql_file>
    # example
    psql -d realhrsoft < ~/Downloads/forms_report_questions.sql
```

<a id="orgd52908a"></a>

## QA/QC server shortcuts

We have a few aliases setup on our qa/qc servers to make certain operations easier.


<a id="orga402f7a"></a>

### To copy dump from container to local PC:

First, login to qa/qc server. Inside the server:

    backupdb <container_name> <dump_file_name>
    # for example
    backupdb payroll_report payroll_report.dump # here the container name is `be_payroll_report`, dont put `be_`

    # copy the dump from inside the container to outside the container
    copydb payroll_report payroll_report.dump

    # finally copy dump from server to local PC through scp, for example:
    scp prahlad@192.168.102.249:/home/prahlad/payroll_report.dump ~/Downloads/


<a id="org199b5d5"></a>
