# Multi-stage Dockerfile for ARK-TOOLS API

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install build && \
    pip install -e .

# Development stage
FROM builder as development

# Install development dependencies
RUN pip install -e ".[dev]"

# Copy source code
COPY src/ ./src/
COPY .mcp/ ./.mcp/

# Set development environment
ENV FLASK_ENV=development
ENV FLASK_DEBUG=true
ENV PYTHONPATH=/app/src

# Expose development port
EXPOSE 5000

# Development command
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]

# Production stage
FROM python:3.11-slim as production

# Install production system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ark && useradd -r -g ark ark

# Set work directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY .mcp/ ./.mcp/
COPY docker/api/entrypoint.sh ./entrypoint.sh

# Create necessary directories
RUN mkdir -p logs .ark_output .ark_config && \
    chmod +x entrypoint.sh && \
    chown -R ark:ark /app

# Set production environment
ENV FLASK_ENV=production
ENV FLASK_DEBUG=false
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health/ping || exit 1

# Switch to non-root user
USER ark

# Expose port
EXPOSE 5000

# Use dumb-init for signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["./entrypoint.sh"]