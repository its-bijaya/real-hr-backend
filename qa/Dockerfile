FROM python:3.9
MAINTAINER aayulogic@aayulogic.com

RUN mkdir -p /app/requirements && mkdir /dbdump && mkdir -p /dj-media

WORKDIR /app

RUN apt update && apt install redis-server -y
RUN apt install postgresql postgresql-contrib -y

COPY ./requirements requirements
RUN pip install --no-cache-dir -r /app/requirements/dev.txt

COPY ./ /app
COPY ./qa/.env /app

#COPY ./config/settings/env.py /app/config/settings/local.py

RUN python manage.py generate_rsa_keys

EXPOSE 8000
CMD ["bash", "qa/start_script.sh"]
