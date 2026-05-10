# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/db /app/reports

# Expose port
EXPOSE 8001

# Set environment variables
ENV UNILABS_DB_DIR=/app/db
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]
