#!/bin/bash

# Pego Backend Deployment Script
# This script helps deploy your Pego backend to production

set -e  # Exit on any error

echo "🚀 Pego Backend Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create production environment file if it doesn't exist
if [ ! -f .env.prod ]; then
    print_warning "Production environment file not found. Creating from template..."
    cp .env.prod.template .env.prod
    print_warning "Please edit .env.prod with your actual values before continuing!"
    print_warning "Important: Change all secret keys, passwords, and API keys!"
    
    read -p "Have you updated .env.prod with your values? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Please update .env.prod first, then run this script again."
        exit 1
    fi
fi

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
fi

print_status "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

print_status "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check if MongoDB is ready
print_status "Checking MongoDB connection..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T mongodb mongosh --eval "db.runCommand('ping')" > /dev/null 2>&1; then
        print_status "MongoDB is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "MongoDB failed to start within 30 attempts"
        exit 1
    fi
    sleep 2
done

# Check if backend is ready
print_status "Checking backend API..."
for i in {1..30}; do
    if curl -f http://localhost:8001/api/ > /dev/null 2>&1; then
        print_status "Backend API is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Backend API failed to start within 30 attempts"
        exit 1
    fi
    sleep 2
done

# Create default admin user
print_status "Creating default admin user..."
docker-compose -f docker-compose.prod.yml exec -T backend python setup_admin.py

print_status "Deployment completed successfully!"
print_status "Services are running on:"
print_status "  - Backend API: http://localhost:8001/api/"
print_status "  - Admin Panel: http://localhost:8001/api/admin/"
print_status "  - MongoDB: localhost:27017"

print_warning "Next steps:"
print_warning "1. Set up SSL certificates in ./ssl/ directory"
print_warning "2. Update nginx.conf with your domain name"
print_warning "3. Configure your domain DNS to point to this server"
print_warning "4. Test your API endpoints"

echo ""
print_status "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
print_status "To stop services: docker-compose -f docker-compose.prod.yml down"
print_status "To restart services: docker-compose -f docker-compose.prod.yml restart"