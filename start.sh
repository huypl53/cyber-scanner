#!/bin/bash

echo "====================================="
echo "AI Threat Detection System - Startup"
echo "====================================="
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    echo "Please install Docker and Docker Compose first"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Start services
echo "Starting all services with Docker Compose..."
docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 10

echo ""
echo "====================================="
echo "System Status:"
echo "====================================="
docker-compose ps

echo ""
echo "====================================="
echo "Access Points:"
echo "====================================="
echo "Frontend:        http://localhost:3000"
echo "Backend API:     http://localhost:8000"
echo "API Docs:        http://localhost:8000/docs"
echo "PostgreSQL:      localhost:5432"
echo "Kafka:           localhost:9092"
echo ""
echo "====================================="
echo "Quick Commands:"
echo "====================================="
echo "View logs:       docker-compose logs -f"
echo "Stop services:   docker-compose down"
echo "Restart:         docker-compose restart"
echo ""
echo "System is ready! Visit http://localhost:3000 to get started."
