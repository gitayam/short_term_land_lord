#!/bin/bash

# Short Term Landlord - GCP App Engine Deployment Script
# This script automates the deployment process to Google App Engine

set -e  # Exit on any error

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID:-"short-term-landlord"}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"default"}
APP_VERSION=${APP_VERSION:-"v$(date +%Y%m%d-%H%M%S)"}

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
        log_error "Google Cloud CLI (gcloud) is not installed. Please install it first."
        log_info "Visit: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if user is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "You are not authenticated with Google Cloud. Please run 'gcloud auth login' first."
        exit 1
    fi
    
    # Check if project exists and user has access
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Project '$PROJECT_ID' does not exist or you don't have access to it."
        log_info "Available projects:"
        gcloud projects list --format="table(projectId,name)"
        exit 1
    fi
    
    # Check if app.yaml exists
    if [ ! -f "app.yaml" ]; then
        log_error "app.yaml not found. Make sure you're in the project root directory."
        exit 1
    fi
    
    log_success "Prerequisites check passed!"
}

# Set up project and APIs
setup_project() {
    log_info "Setting up project '$PROJECT_ID'..."
    
    # Set the project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required APIs..."
    gcloud services enable appengine.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable sqladmin.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable logging.googleapis.com
    gcloud services enable monitoring.googleapis.com
    
    # Initialize App Engine if not already initialized
    if ! gcloud app describe &> /dev/null; then
        log_info "Initializing App Engine..."
        gcloud app create --region="$REGION"
    fi
    
    log_success "Project setup complete!"
}

# Setup Cloud SQL if needed
setup_cloud_sql() {
    log_info "Checking Cloud SQL setup..."
    
    INSTANCE_NAME="${PROJECT_ID}-postgres"
    
    # Check if instance exists
    if ! gcloud sql instances describe "$INSTANCE_NAME" &> /dev/null; then
        log_warning "Cloud SQL instance not found. Creating new instance..."
        
        # Create Cloud SQL instance
        gcloud sql instances create "$INSTANCE_NAME" \
            --database-version=POSTGRES_14 \
            --tier=db-f1-micro \
            --region="$REGION" \
            --storage-type=SSD \
            --storage-size=10GB \
            --backup-start-time=03:00
        
        # Create database
        gcloud sql databases create "landlord_db" --instance="$INSTANCE_NAME"
        
        # Create user
        gcloud sql users create "app_user" \
            --instance="$INSTANCE_NAME" \
            --password="$(openssl rand -base64 32)"
        
        log_success "Cloud SQL instance created: $INSTANCE_NAME"
        log_warning "Please update the DATABASE_URL in app.yaml with the connection string"
    else
        log_success "Cloud SQL instance exists: $INSTANCE_NAME"
    fi
}

# Setup secrets in Secret Manager
setup_secrets() {
    log_info "Setting up secrets in Secret Manager..."
    
    # Create secret for Django secret key if it doesn't exist
    if ! gcloud secrets describe "flask-secret-key" &> /dev/null; then
        echo "$(openssl rand -base64 32)" | gcloud secrets create "flask-secret-key" --data-file=-
        log_success "Created secret: flask-secret-key"
    fi
    
    # Create secret for database password if it doesn't exist
    if ! gcloud secrets describe "database-password" &> /dev/null; then
        echo "$(openssl rand -base64 32)" | gcloud secrets create "database-password" --data-file=-
        log_success "Created secret: database-password"
    fi
    
    log_info "Secrets setup complete!"
}

# Run database migrations
run_migrations() {
    log_info "Preparing database migrations..."
    
    # Check if migrations directory exists
    if [ -d "migrations" ]; then
        log_info "Database migrations will be run after deployment via Cloud Build"
    else
        log_warning "No migrations directory found. Database tables will be created on first run"
    fi
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check Python syntax
    log_info "Checking Python syntax..."
    python3 -m py_compile main.py
    python3 -m py_compile config.py
    
    # Check if requirements files exist
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    # Validate app.yaml
    log_info "Validating app.yaml..."
    gcloud app deploy --dry-run app.yaml
    
    log_success "Pre-deployment checks passed!"
}

# Deploy to App Engine
deploy() {
    log_info "Deploying to App Engine..."
    
    # Deploy the application
    gcloud app deploy app.yaml \
        --version="$APP_VERSION" \
        --promote \
        --stop-previous-version \
        --quiet
    
    # Get the service URL
    SERVICE_URL=$(gcloud app describe --format="value(defaultHostname)")
    SERVICE_URL="https://$SERVICE_URL"
    
    log_success "Deployment successful!"
    log_info "Service URL: $SERVICE_URL"
    
    # Test the deployment
    log_info "Testing deployment..."
    sleep 10  # Wait for deployment to be ready
    
    if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" | grep -q "200"; then
        log_success "Health check passed! Service is responding."
    else
        log_warning "Health check failed. Check the logs:"
        log_info "gcloud app logs tail --service=default"
    fi
}

# Setup monitoring (optional)
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Create uptime check
    if ! gcloud alpha monitoring uptime list --filter="displayName:short-term-landlord-uptime" --format="value(name)" | grep -q .; then
        log_info "Creating uptime monitoring check..."
        # Note: This requires alpha API and proper configuration
        log_info "Manual setup required for uptime monitoring via Cloud Console"
    fi
    
    log_info "Monitoring setup complete!"
}

# Main deployment function
main() {
    echo "🏠 Short Term Landlord - App Engine Deployment"
    echo "=============================================="
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Version: $APP_VERSION"
    echo ""
    
    # Check if user wants to proceed
    read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled."
        exit 0
    fi
    
    # Run deployment steps
    check_prerequisites
    setup_project
    setup_cloud_sql
    setup_secrets
    run_migrations
    pre_deployment_checks
    deploy
    setup_monitoring
    
    echo ""
    log_success "🎉 Deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    log_info "1. Visit your application: https://${PROJECT_ID}.appspot.com"
    log_info "2. Configure environment variables in app.yaml if needed"
    log_info "3. Set up custom domain (optional)"
    log_info "4. Configure monitoring alerts"
    log_info "5. Set up backup strategy for Cloud SQL"
    echo ""
    log_info "For troubleshooting, check logs with: gcloud app logs tail"
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --version)
            APP_VERSION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project-id PROJECT_ID    Google Cloud project ID"
            echo "  --region REGION           Google Cloud region (default: us-central1)"
            echo "  --version VERSION         App version (default: v<timestamp>)"
            echo "  --help                    Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  GOOGLE_CLOUD_PROJECT_ID   Google Cloud project ID"
            echo "  GOOGLE_CLOUD_REGION       Google Cloud region"
            echo "  APP_VERSION               App version"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main