# PwnSafe Dockerfile
# Multi-stage build for PwnSafe application

# Build stage
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libffi8 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application files
COPY pwnsafe.py ./
COPY README.md ./

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash pwnsafe && \
    chown -R pwnsafe:pwnsafe /app
USER pwnsafe

# Expose port (if needed for future web interface)
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command
CMD ["python", "pwnsafe.py"]

# Development stage
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Switch back to pwnsafe user
USER pwnsafe

# Set development environment
ENV PYTHONPATH=/app
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

# Default command for development
CMD ["python", "-c", "import pwnsafe; print('PwnSafe development environment ready')"]
