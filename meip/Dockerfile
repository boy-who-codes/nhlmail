# Use official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
# - whois: Required for python-whois
# - netcat-openbsd: For wait-for-it scripts (optional but good practice)
# - gcc/build-essential: For compiling python extensions if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    whois \
    netcat-openbsd \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Create non-root user for security (optional but recommended)
# RUN useradd -m myuser
# USER myuser

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "meip.wsgi:application"]
