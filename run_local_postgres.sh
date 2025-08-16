#!/bin/bash
# Run the Flask application locally with PostgreSQL

echo "🚀 Starting Short Term Landlord with PostgreSQL..."

# Export PostgreSQL configuration
export FLASK_ENV=development
export DATABASE_URL="postgresql://landlord:password@127.0.0.1:5432/landlord_prod"
export SECRET_KEY="dev-secret-key-$(date +%s)"
export FLASK_APP=app

# Check if PostgreSQL is running
if ! docker ps | grep -q landlord_postgres; then
    echo "⚠️  PostgreSQL is not running. Starting Docker containers..."
    docker-compose -f docker-compose.postgres.yml up -d
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Install psycopg2 if not installed
pip show psycopg2-binary > /dev/null 2>&1 || pip install -q psycopg2-binary

echo "🔧 Using PostgreSQL configuration..."
echo "🗄️  Database: landlord_prod"
echo "👤 Users: admin@landlord.com / admin123"

# Run the Flask application
echo "🌐 Starting Flask application..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🏠 Short Term Landlord is starting..."
echo ""
echo "📍 Main URLs:"
echo "   🏠 Homepage:           http://localhost:5000"
echo "   🔐 Login:              http://localhost:5000/auth/login"
echo "   📊 Dashboard:          http://localhost:5000/dashboard"
echo "   📅 Calendar:           http://localhost:5000/combined-calendar"
echo "   🏘️  Properties:         http://localhost:5000/properties"
echo "   ✅ Tasks:              http://localhost:5000/tasks"
echo "   📦 Inventory:          http://localhost:5000/inventory"
echo "   💰 Invoices:           http://localhost:5000/invoices"
echo ""
echo "🔧 Admin Tools:"
echo "   👤 Admin Panel:        http://localhost:5000/admin"
echo "   🗄️  pgAdmin:           http://localhost:5050"
echo ""
echo "📱 Guest Portal:"
echo "   🔑 Guest Access:       http://localhost:5000/guest"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run Flask with PostgreSQL config
python3 -c "
from app import create_app
app = create_app('postgres_dev')
app.run(host='0.0.0.0', port=5000, debug=True)
"