# ==============================================================================
# Build stage - for installing dependencies and building the application
# ==============================================================================
FROM python:3.11-slim as builder

# Set environment variables for build stage
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies to a target directory
COPY requirements.txt .
RUN pip install --no-cache-dir -t /app/packages -r requirements.txt

# Copy the application code
COPY . .

# Install the package to the same target directory
RUN pip install --no-cache-dir -t /app/packages -e .

# ==============================================================================
# Runtime stage - minimal image for running the application
# ==============================================================================
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/packages:/app/src:${PYTHONPATH}"

# Set the working directory
WORKDIR /app

# Copy Python packages from builder stage (including site-packages)
COPY --from=builder /app/packages /app/packages

# Copy the application code and metadata
COPY --from=builder /app/src ./src
COPY --from=builder /app/pyproject.toml ./
COPY --from=builder /app/requirements.txt ./

EXPOSE 7860

# Set the default command to run the application
CMD ["python", "-m", "anki_gen.app"]
