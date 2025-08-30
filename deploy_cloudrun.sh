#!/bin/bash

# Short Term Landlord - Cloud Run Deployment Script
# Deploy to Google Cloud Run in the speech-memorization project

set -e  # Exit on any error

# Configuration
PROJECT_ID="speech-memorization"
REGION="us-central1"
SERVICE_NAME="short-term-landlord"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI (gcloud) is not installed."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed."
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with Google Cloud. Run 'gcloud auth login'."
        exit 1
    fi
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    
    log_success "Prerequisites check passed!"
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required APIs..."
    
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    
    log_success "APIs enabled!"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    # Update Dockerfile for Cloud Run
    cat > Dockerfile.cloudrun << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    build-essential \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=main.py
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Create a user to run the app
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Run the application
CMD exec gunicorn main:app --bind :$PORT --workers 1 --threads 8 --timeout 0
EOF
    
    # Build and tag the image
    docker build -f Dockerfile.cloudrun -t "$IMAGE_NAME" .
    
    log_success "Docker image built successfully!"
}

# Push image to Container Registry
push_image() {
    log_info "Pushing image to Google Container Registry..."
    
    # Configure Docker to use gcloud credentials
    gcloud auth configure-docker --quiet
    
    # Push the image
    docker push "$IMAGE_NAME"
    
    log_success "Image pushed to Container Registry!"
}

# Create secrets
setup_secrets() {
    log_info "Setting up secrets..."
    
    # Create admin password secret if it doesn't exist
    if ! gcloud secrets describe admin-password --quiet &> /dev/null; then
        echo "Dashboard_Admin123!" | gcloud secrets create admin-password --data-file=-
        log_success "Created admin-password secret"
    fi
    
    # Create secret key secret if it doesn't exist
    if ! gcloud secrets describe flask-secret-key --quiet &> /dev/null; then
        echo "$(openssl rand -base64 32)" | gcloud secrets create flask-secret-key --data-file=-
        log_success "Created flask-secret-key secret"
    fi
    
    log_success "Secrets setup complete!"
}

# Deploy to Cloud Run
deploy_service() {
    log_info "Deploying to Cloud Run..."
    
    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_NAME" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --port 8080 \
        --memory 2Gi \
        --cpu 2 \
        --max-instances 10 \
        --set-env-vars "DATABASE_URL=sqlite:////tmp/app.db" \
        --set-env-vars "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID" \
        --set-env-vars "FLASK_ENV=production" \
        --set-secrets "ADMIN_PASSWORD=admin-password:latest" \
        --set-secrets "SECRET_KEY=flask-secret-key:latest" \
        --quiet
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
    
    log_success "Deployment successful!"
    log_info "Service URL: $SERVICE_URL"
    
    return 0
}

# Test the deployment
test_deployment() {
    log_info "Testing deployment..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
    
    # Wait for service to be ready
    sleep 15
    
    # Test health endpoint
    if curl -f -s "$SERVICE_URL/health" > /dev/null 2>&1; then
        log_success "Health check passed! Service is responding."
    else
        log_warning "Health check failed. Service might still be starting up."
        log_info "Try accessing: $SERVICE_URL"
    fi
    
    # Test main page
    if curl -f -s "$SERVICE_URL/" > /dev/null 2>&1; then
        log_success "Main page accessible!"
    else
        log_warning "Main page test failed. Check the logs."
    fi
}

# Show logs
show_logs() {
    log_info "Recent deployment logs:"
    gcloud run services logs read "$SERVICE_NAME" --region "$REGION" --limit 20
}

# Main deployment function
main() {
    echo "🏠 Short Term Landlord - Cloud Run Deployment"
    echo "=============================================="
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Service: $SERVICE_NAME"
    echo ""
    
    check_prerequisites
    enable_apis
    setup_secrets
    build_image
    push_image
    deploy_service
    test_deployment
    
    echo ""
    log_success "🎉 Cloud Run deployment completed!"
    echo ""
    
    # Get final service URL
    SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")
    
    log_info "Service Details:"
    echo "  URL: $SERVICE_URL"
    echo "  Admin Login: issac@alfaren.xyz"
    echo "  Password: Available in Secret Manager (admin-password)"
    echo ""
    log_info "Monitoring Commands:"
    echo "  View logs: gcloud run services logs tail $SERVICE_NAME --region $REGION"
    echo "  Check status: gcloud run services describe $SERVICE_NAME --region $REGION"
    echo "  Update service: gcloud run services update $SERVICE_NAME --region $REGION"
}

# Clean up function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f Dockerfile.cloudrun
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function
main