# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and environment file
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY .env .env
COPY fastchat.config.json ./src/fastchat.config.json
COPY fastchat.config.json fastchat.config.json

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (if needed for health checks or monitoring)
EXPOSE 8000

# Set the default command to run the evolution_ws.py script
CMD ["python", "src/evolution_ws.py"]