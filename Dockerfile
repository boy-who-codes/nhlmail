# Base Image
FROM python:3.10-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies
# libpq-dev for potential postgres (optional), build-essential for compiling
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Requirements
COPY requirements.txt /app/

# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Project Code
COPY . /app/

# Environment Variables (Defaults, can be overridden)
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=meip.settings

# Expose Port
EXPOSE 8000

# Default Command (Overridden by docker-compose)
CMD ["python", "meip/manage.py", "runserver", "0.0.0.0:8000"]
