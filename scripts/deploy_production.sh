#!/bin/bash

# Production Deployment Script for Short Term Landlord Property Management System
# This script sets up the production environment with all performance and monitoring features

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
   exit 1
fi

log "Starting production deployment..."

# Check prerequisites
log "Checking prerequisites..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    warning ".env file not found. Creating from template..."
    if [ -f ".env.production.example" ]; then
        cp .env.production.example .env
        warning "Please edit .env file with your production values before continuing."
        echo "Press Enter to continue after editing .env file..."
        read
    else
        error ".env.production.example file not found. Cannot create production configuration."
        exit 1
    fi
fi

# Validate required environment variables
log "Validating environment configuration..."

source .env

required_vars=(
    "SECRET_KEY"
    "DATABASE_URL"
    "REDIS_URL"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        error "Required environment variable $var is not set in .env file"
        exit 1
    fi
done

success "Environment validation passed"

# Build and start services
log "Building and starting services..."

# Stop existing containers
docker-compose down

# Build new images
docker-compose build --no-cache

# Start services in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services to be ready
log "Waiting for services to start..."
sleep 30

# Health checks
log "Running health checks..."

# Check if web service is healthy
if docker-compose ps | grep -q "web.*Up.*healthy"; then
    success "Web service is healthy"
else
    error "Web service is not healthy"
    docker-compose logs web
    exit 1
fi

# Check if database is ready
if docker-compose exec -T db pg_isready -U postgres; then
    success "Database is ready"
else
    error "Database is not ready"
    exit 1
fi

# Check if Redis is ready
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    success "Redis is ready"
else
    error "Redis is not ready"
    exit 1
fi

# Run database migrations
log "Running database migrations..."
docker-compose exec -T web flask db upgrade

# Check application health endpoint
log "Checking application health..."
sleep 10

# Try to access health endpoint
for i in {1..5}; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        success "Application health check passed"
        break
    else
        warning "Health check attempt $i failed, retrying..."
        sleep 5
    fi
    
    if [ $i -eq 5 ]; then
        error "Application health check failed after 5 attempts"
        docker-compose logs web
        exit 1
    fi
done

# Display service status
log "Service status:"
docker-compose ps

# Display logs
log "Recent logs:"
docker-compose logs --tail=20

# Cache warming
log "Warming application cache..."
curl -s http://localhost:5000/health > /dev/null

# Display monitoring endpoints
success "Deployment completed successfully!"
echo ""
echo "Service Endpoints:"
echo "  Application: http://localhost:5000"
echo "  Health Check: http://localhost:5000/health"
echo "  Metrics: http://localhost:5000/metrics (if Prometheus enabled)"
echo ""
echo "Monitoring Commands:"
echo "  View logs: docker-compose logs -f"
echo "  Check status: docker-compose ps"
echo "  Monitor performance: docker stats"
echo ""
echo "Cache Statistics:"
curl -s http://localhost:5000/health | jq '.checks.redis' 2>/dev/null || echo "  Install jq to see detailed Redis statistics"

# Setup log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/stll > /dev/null <<EOF
/var/lib/docker/containers/*/*-json.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
    postrotate
        docker kill --signal="USR1" \$(docker ps -q) 2>/dev/null || true
    endscript
}
EOF

# Create monitoring script
log "Creating monitoring script..."
cat > monitoring.sh << 'EOF'
#!/bin/bash
# Simple monitoring script for production

echo "=== System Status ==="
docker-compose ps

echo -e "\n=== Application Health ==="
curl -s http://localhost:5000/health | jq '.' || curl -s http://localhost:5000/health

echo -e "\n=== Resource Usage ==="
docker stats --no-stream

echo -e "\n=== Recent Errors ==="
docker-compose logs --tail=10 web | grep -i error || echo "No recent errors"

echo -e "\n=== Cache Statistics ==="
docker-compose exec redis redis-cli info stats | grep -E "(keyspace_hits|keyspace_misses|used_memory_human)"
EOF

chmod +x monitoring.sh

success "Production deployment completed!"
warning "Next steps:"
echo "1. Set up SSL certificates with Let's Encrypt"
echo "2. Configure your domain DNS to point to this server"
echo "3. Set up external monitoring (e.g., Uptime Robot)"
echo "4. Configure backup procedures"
echo "5. Review security settings"
echo ""
echo "Run './monitoring.sh' to check system status anytime" 