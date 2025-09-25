# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies for development
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    nano \
    htop \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY example_queries.py example_mutation.py example_subscription.py database.py app.py .
COPY templates/ templates/

# Install additional development tools
RUN pip install --no-cache-dir \
    black \
    isort \
    flake8 \
    pylint \
    pytest \
    pytest-cov \
    ipython \
    jupyter

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
#ENV PYTHONPATH=/app

# Expose port
EXPOSE 5001

# Keep container running for development
CMD ["python", "app.py"]
