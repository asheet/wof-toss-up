# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# OpenShift compatibility: Set permissions for arbitrary user IDs
# OpenShift runs containers with random user IDs, so we need to make directories writable by group
RUN chgrp -R 0 /app && \
    chmod -R g+rwX /app

# OpenShift runs with arbitrary user IDs, so we don't specify a USER
# The container will run with whatever user ID OpenShift assigns

# Expose port
EXPOSE 8000

# Health check using curl (more lightweight and OpenShift-compatible)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/', timeout=10)"

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
