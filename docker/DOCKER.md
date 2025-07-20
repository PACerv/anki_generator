# 🐳 Docker Setup Guide

This guide explains how to containerize and run the Anki Card Creator app using Docker.

## Prerequisites
- Docker installed on your machine
- A `.env` file with your API keys (see Environment Setup below)

## 🔐 Environment Setup

Before running the application, create a `.env` file in the project root with your API keys:

```bash
# Create .env file in project root (copy from example if available)
cp .env.example .env
# Edit .env file with your actual API keys
```

Your `.env` file should contain:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

## 🚀 Local Docker Build and Run

**Note:** Make sure you're in the project root directory (where `pyproject.toml` is located) when running these commands.

### Option 1: Using Docker directly

1. **Build the Docker image:**
   ```bash
   # Run from the project root directory
   docker build -f docker/Dockerfile -t anki-card-creator .
   ```

2. **Run locally with Docker:**
   ```bash
   # Load environment variables from .env file
   docker run -p 7860:7860 --env-file .env anki-card-creator
   ```

3. **Access the app:**
   Open http://localhost:7860 in your browser

### Option 2: Using Docker Compose

If you prefer using Docker Compose:

1. **Start the application:**
   ```bash
   docker-compose up --build
   ```

2. **Run in background:**
   ```bash
   docker-compose up -d --build
   ```

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

## 🔧 Docker Configuration

### Dockerfile Overview

The Docker image is configured with:
- **Base Image:** Python 3.12-slim
- **Working Directory:** `/app`
- **Exposed Port:** 7860 (Gradio default)
- **Entry Point:** Gradio app with host binding to 0.0.0.0

### Environment Variables

The application reads the following environment variables:
- `GOOGLE_API_KEY`: Your Google Gemini API key (required)

### Volume Mounting (Optional)

For development, you can mount your local code:

```bash
docker run -p 7860:7860 \
  --env-file .env \
  -v $(pwd)/src:/app/src \
  anki-card-creator
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
