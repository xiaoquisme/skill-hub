#!/bin/bash
# SkillHub Quick Start Script
# Automates Docker build and run for easy setup

set -e

echo "SkillHub Quick Start"
echo "==================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "Error: Docker daemon is not running."
    echo "Please start Docker and try again."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed."
    echo "Please install Docker Compose or Docker Desktop."
    exit 1
fi

# Build and run
echo "Building SkillHub image..."
docker compose build

echo ""
echo "Starting SkillHub..."
docker compose up -d

# Wait for service to be ready (through nginx proxy)
echo "Waiting for SkillHub to be ready..."
PORT="${SKILLHUB_PORT:-80}"
RETRIES=0
MAX_RETRIES=30
while [ $RETRIES -lt $MAX_RETRIES ]; do
    if curl -sf "http://localhost:${PORT}/api/health" > /dev/null 2>&1; then
        break
    fi
    RETRIES=$((RETRIES + 1))
    sleep 1
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "Warning: SkillHub may not be ready yet. Check logs with: docker compose logs"
else
    echo "SkillHub is ready!"
fi

echo ""
echo "Web UI: http://localhost:${PORT}"
echo "API docs: http://localhost:${PORT}/docs"
echo ""
echo "To stop: docker compose down"
echo "To view logs: docker compose logs -f"
