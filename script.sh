#!/bin/bash


# Copy project files into the container
cp . .

# Verify Python 3.8 installation
python3.8 --version

# Set up Python environment and install dependencies
python3.8 -m venv /app/myenv && \
    /app/myenv/bin/pip install --upgrade pip wheel && \
    /app/myenv/bin/pip install -r /app/requirements/dev.txt

# Create symlinks for python3 and python3.8
ln -sf $(which python3.8) /usr/local/bin/python3.8 && \
    ln -sf $(which python3.8) /usr/local/bin/python3

# Copy the environment sample to .env
cp .env.sample .env

# Start PostgreSQL, Redis, and the Django r
service postgresql start && \
    service redis-server start && \
    source myenv/bin/activate && \
    python manage.py generate_rsa_keys && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:8000