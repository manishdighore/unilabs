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

# Create necessary directories first
RUN mkdir -p /app/db /app/reports /app/static /app/templates

# Copy application files
COPY . .

# Ensure all necessary directories exist with correct permissions
RUN mkdir -p /app/db /app/reports /app/static /app/templates /app/agents /app/api /app/scheduler && \
    chmod -R 755 /app && \
    # Verify key files exist
    [ -f /app/app.py ] || (echo "ERROR: app.py not found" && exit 1) && \
    [ -d /app/templates ] || (echo "ERROR: templates directory not found" && exit 1)

# Expose port
EXPOSE 8001

# Set environment variables
ENV UNILABS_DB_DIR=/app/db
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]
