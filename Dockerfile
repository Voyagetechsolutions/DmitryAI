# Dmitry AI Assistant - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY MarkX/requirements_production.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_production.txt

# Copy application code
COPY MarkX/ /app/

# Create necessary directories
RUN mkdir -p logs knowledge_base memory

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DMITRY_ENV=production

# Expose ports
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8765/health')"

# Run validation on startup
RUN python validate_setup.py || true

# Start application
CMD ["python", "run_dmitry.py", "--mode", "server"]
