FROM python:3.8

# Set working directory
WORKDIR /app

# Install dependencies for system packages
RUN apt-get update && \
    apt-get install -y software-properties-common gcc && \
    apt-get clean

# Copy project files
COPY . .

# Create virtual environment and install Python dependencies
RUN pip install --upgrade pip wheel && \
    pip install -r requirements/dev.txt
    

# Copy sample environment variables file
COPY .env.sample .env 

# Expose the application's port
EXPOSE 8080

# Start services and application using the virtual environment
CMD ["/bin/bash", "-c", " \
    python manage.py generate_rsa_keys --skip-checks && \
    python manage.py migrate && \
    python manage.py runserver 0.0.0.0:8080"]
