#!/bin/bash

# Short Term Landlord - Local Development Setup
# Sets up complete local development environment for faster iteration

set -e

echo "🏠 Setting up Short Term Landlord Local Development Environment"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

# 1. Create Python virtual environment
log_info "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# 2. Activate virtual environment and install dependencies
log_info "Installing Python dependencies..."
source venv/bin/activate

# Install basic requirements first
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dev dependencies
log_info "Installing development dependencies..."
pip install flask-migrate alembic python-dotenv

log_success "Python dependencies installed"

# 3. Create local environment file
log_info "Setting up environment variables..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///local_development.db

# Admin User Configuration
ADMIN_EMAIL=admin@localhost.com
ADMIN_PASSWORD=admin123
ADMIN_USERNAME=admin

# Zillow Scraper Configuration (optional)
# SCRAPERAPI_KEY=your_scraperapi_key_here
# RENTCAST_API_KEY=your_rentcast_key_here
# ATTOM_API_KEY=your_attom_key_here

# Development Settings
DEBUG=True
TESTING=False

# Email Settings (optional for dev)
MAIL_SERVER=localhost
MAIL_PORT=25
MAIL_USE_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=

# External Services (optional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Cloud Storage (optional for dev)
GOOGLE_CLOUD_PROJECT_ID=
GOOGLE_APPLICATION_CREDENTIALS=

# Cache Settings
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300
EOF
    log_success "Environment file created (.env)"
else
    log_info "Environment file already exists"
fi

# 4. Initialize database
log_info "Initializing local database..."

# Create database and tables
python3 -c "
import os
from app import create_app, db
from app.models import User, UserRoles

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:///local_development.db'
os.environ['FLASK_ENV'] = 'development'

app = create_app()
with app.app_context():
    # Create all tables
    db.create_all()
    print('✅ Database tables created')
    
    # Create admin user if not exists
    admin = User.query.filter_by(email='admin@localhost.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@localhost.com',
            first_name='Admin',
            last_name='User',
            role=UserRoles.ADMIN.value
        )
        admin.set_password('admin123')
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin user created: admin@localhost.com / admin123')
    else:
        print('✅ Admin user already exists')
"

log_success "Database initialized"

# 5. Test basic Flask app startup
log_info "Testing Flask application startup..."
python3 -c "
from app import create_app
app = create_app()
print('✅ Flask application loads successfully')
print(f'✅ App name: {app.name}')
print(f'✅ Debug mode: {app.debug}')
"

# 6. Create run script
log_info "Creating run script..."
cat > run_local.sh << 'EOF'
#!/bin/bash
# Quick start script for local development

export FLASK_APP=main.py
export FLASK_ENV=development

# Activate virtual environment
source venv/bin/activate

# Start Flask development server
echo "🚀 Starting Short Term Landlord local development server..."
echo "📱 Admin login: admin@localhost.com / admin123"
echo "🌐 URL: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

flask run --host=0.0.0.0 --port=5000 --debug
EOF

chmod +x run_local.sh
log_success "Run script created (run_local.sh)"

# 7. Create testing script for Zillow scraper
log_info "Creating Zillow scraper test script..."
cat > test_zillow_scraper.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for the enhanced Zillow scraper
Usage: python3 test_zillow_scraper.py [address_or_url]
"""

import sys
import os
sys.path.append('.')

def test_scraper_basic():
    """Test the basic scraper functionality without external dependencies."""
    print("🧪 Testing Zillow Scraper V2 - Basic Mode")
    print("=" * 50)
    
    try:
        from app.utils.zillow_scraper_v2 import ZillowScraperV2
        
        # Initialize scraper
        scraper = ZillowScraperV2(headless=True)
        print("✅ Scraper initialized successfully")
        
        # Test URL (from user's issue)
        test_url = "https://www.zillow.com/homedetails/824-Carol-St-Fayetteville-NC-28303/53646204_zpid/"
        if len(sys.argv) > 1:
            test_url = sys.argv[1]
        
        print(f"🎯 Testing URL: {test_url}")
        print()
        
        # Try basic requests method first
        print("📡 Testing basic requests method...")
        try:
            result = scraper._extract_with_requests(test_url)
            if result and result.get('address'):
                print("✅ SUCCESS: Basic requests method worked!")
                print_property_data(result)
                return True
            else:
                print("⚠️  No data extracted with basic method")
        except Exception as e:
            print(f"❌ Basic method failed: {e}")
        
        print()
        
        # Try the full scraper
        print("🔄 Testing full scraper with fallback strategies...")
        try:
            result = scraper.fetch_property_details(test_url)
            if result:
                print("✅ SUCCESS: Full scraper worked!")
                print_property_data(result)
                return True
            else:
                print("❌ Full scraper returned no data")
        except Exception as e:
            print(f"❌ Full scraper failed: {e}")
        
        return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try installing dependencies: pip install playwright requests beautifulsoup4")
        return False

def print_property_data(data):
    """Print property data in a nice format."""
    print()
    print("🏠 PROPERTY DATA EXTRACTED:")
    print("-" * 30)
    for key, value in data.items():
        if value:
            print(f"  {key.replace('_', ' ').title()}: {value}")
    print()

if __name__ == "__main__":
    success = test_scraper_basic()
    if success:
        print("🎉 Zillow scraper test PASSED!")
        sys.exit(0)
    else:
        print("💥 Zillow scraper test FAILED!")
        sys.exit(1)
EOF

chmod +x test_zillow_scraper.py
log_success "Zillow scraper test script created"

# 8. Final setup verification
echo ""
log_success "🎉 Local development environment setup complete!"
echo ""
echo "📋 NEXT STEPS:"
echo "=============="
echo "1. 🚀 Start the development server:"
echo "   ./run_local.sh"
echo ""
echo "2. 🧪 Test the Zillow scraper:"
echo "   python3 test_zillow_scraper.py"
echo ""
echo "3. 🌐 Access the application:"
echo "   http://localhost:5000"
echo ""
echo "4. 🔐 Login as admin:"
echo "   Email: admin@localhost.com"
echo "   Password: admin123"
echo ""
echo "5. 🧪 Test the new Zillow endpoint:"
echo "   POST http://localhost:5000/api/zillow/property-data"
echo ""
echo "📁 FILES CREATED:"
echo "  ✅ venv/ (Python virtual environment)"
echo "  ✅ .env (Environment variables)"
echo "  ✅ local_development.db (SQLite database)"
echo "  ✅ run_local.sh (Quick start script)"
echo "  ✅ test_zillow_scraper.py (Scraper testing)"
echo ""
log_info "Happy coding! 🚀"