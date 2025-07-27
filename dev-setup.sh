#!/bin/bash

# Short Term Landlord - Local Development Setup
# This script sets up the development environment

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🏠 Short Term Landlord - Development Setup"
echo "=========================================="

# Check Python version
log_info "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
log_info "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating .env file..."
    cat > .env << EOF
# Development Environment Variables
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Database (SQLite for development)
DATABASE_URL=sqlite:///app.db

# Email (console backend for development)
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=false
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@localhost

# Admin user (created automatically)
ADMIN_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_FIRST_NAME=Admin
ADMIN_LAST_NAME=User

# Features
NOTIFICATION_EMAIL_ENABLED=false
NOTIFICATION_SMS_ENABLED=false

# Optional development settings
CACHE_TYPE=simple
SESSION_TYPE=filesystem
RATELIMIT_ENABLED=false
EOF
    log_success ".env file created with development defaults"
else
    log_warning ".env file already exists - not overwriting"
fi

# Initialize database
log_info "Initializing database..."
export FLASK_APP=main.py
flask db init || log_warning "Database already initialized"
flask db migrate -m "Initial migration" || log_warning "Migration may already exist"
flask db upgrade

# Create admin user
log_info "Setting up admin user..."
python3 -c "
from app import create_app, db
from app.models import User
import os

app = create_app()
with app.app_context():
    # Check if admin user exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            email='admin@example.com',
            username='admin',
            first_name='Admin',
            last_name='User',
            is_admin=True,
            is_property_owner=True,
            is_property_manager=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created: admin@example.com / admin123')
    else:
        print('ℹ️ Admin user already exists')
"

# Create sample data (optional)
read -p "Do you want to create sample data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Creating sample data..."
    python3 -c "
from app import create_app, db
from app.models import User, Property
from datetime import datetime

app = create_app()
with app.app_context():
    # Get admin user
    admin = User.query.filter_by(email='admin@example.com').first()
    
    # Create sample property
    if not Property.query.filter_by(name='Sample Property').first():
        property = Property(
            name='Sample Property',
            address='123 Main St, Anytown, USA',
            description='A beautiful sample property for testing',
            property_type='house',
            owner_id=admin.id,
            bedrooms=3,
            bathrooms=2,
            checkin_time='3:00 PM',
            checkout_time='11:00 AM'
        )
        # Generate tokens for testing
        property.generate_guest_access_token()
        property.generate_worker_calendar_token()
        property.guest_access_enabled = True
        
        db.session.add(property)
        db.session.commit()
        print('✅ Sample property created')
        print(f'   Guest guidebook: /guest/1/guidebook?token={property.guest_access_token}')
        print(f'   Worker calendar: /worker-calendar/{property.worker_calendar_token}')
    else:
        print('ℹ️ Sample data already exists')
"
fi

echo ""
log_success "🎉 Development setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start development server: python main.py"
echo "3. Visit: http://127.0.0.1:8080"
echo "4. Admin login: admin@example.com / admin123"
echo ""
echo "Development URLs:"
echo "- Main app: http://127.0.0.1:8080"
echo "- Health check: http://127.0.0.1:8080/health"
echo ""
echo "To deploy to GCP:"
echo "./deploy.sh --project-id your-project-id"