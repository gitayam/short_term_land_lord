# Short Term Land Lord

A comprehensive, production-ready property management system designed specifically for short-term rental properties. This platform streamlines the coordination between property owners, cleaners, and maintenance staff while providing enhanced calendar integration with popular booking platforms like Airbnb and VRBO.

## 🚀 Production Ready Features

This system is designed to scale to **thousands of concurrent users** with enterprise-grade features:

- **High Performance**: Redis caching, connection pooling, query optimization
- **Security**: Advanced input validation, XSS protection, SQL injection prevention
- **Monitoring**: Prometheus metrics, Sentry error tracking, structured logging
- **Reliability**: Health checks, automated backups, disaster recovery
- **Scalability**: Microservices architecture, horizontal scaling capabilities

## Features
![main-page](docs/media/main-page.png)


- **Calendar Management**: Import and sync calendar events from Airbnb, VRBO, and other booking platforms
- **Property Management**: Track property details, amenities, and access information
- **Task Management**: Assign and track cleaning and maintenance tasks
- **User Role System**: Different interfaces and permissions for property owners, cleaners, and maintenance staff
- **Inventory Management**: Track supplies and assets for each property
- **Cleaning Sessions**: Document cleaning with before/after videos and photos
- **Maintenance Requests**: Report and track maintenance issues
- **Guest Access Portal**: Provide information to guests with customizable access

![property-edit](docs/media/property-edit.png)

## Development Setup

### Prerequisites

- Git
- Docker and Docker Compose (recommended)
- **For Production**: Redis, PostgreSQL 14+, Python 3.9+
- **External Services** (optional): AWS S3, Sentry, Prometheus/Grafana
- If not using Docker, you will need Python 3.9+ and PostgreSQL

### Docker Setup (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/gitayam/short_term_land_lord.git
   cd short_term_land_lord
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. Configure your environment variables in `.env`:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://postgres:postgres@db:5432/stll_db
   REDIS_URL=redis://redis:6379/0
   SECRET_KEY=your_secret_key
   
   # Production settings (optional for development)
   SENTRY_DSN=your_sentry_dsn
   AWS_S3_BUCKET=your_backup_bucket
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   ```

4. Build and start the containers:
   ```bash
   docker-compose up -d --build
   ```

5. Access the application at http://localhost:5001

### Local Installation (Alternative)

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/gitayam/short_term_land_lord.git
   cd short_term_land_lord
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment (see Docker setup step 2-3)

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Run the application:
   ```bash
   flask run
   ```

## 🏭 Production Deployment

### Production Docker Setup

For production deployment with all enterprise features:

1. **Configure Production Environment**:
   ```bash
   cp .env.example .env.production
   # Edit .env.production with production values
   ```

2. **Deploy with Production Compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **Production Services Included**:
   - **Application**: Security-hardened Flask app with gunicorn
   - **Database**: PostgreSQL 14 with performance tuning
   - **Cache**: Redis for sessions and caching
   - **Monitoring**: Prometheus + Grafana dashboards
   - **Backups**: Automated database and file backups to S3

### Production Environment Variables

Required for production deployment:

```bash
# Core Application
FLASK_ENV=production
SECRET_KEY=your_very_secure_secret_key
DATABASE_URL=postgresql://username:password@host:5432/database
REDIS_URL=redis://redis:6379/0

# Database Performance
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600

# Security
SESSION_COOKIE_SECURE=true
SSL_REDIRECT=true

# Monitoring & Logging
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
LOG_FORMAT=json
PROMETHEUS_METRICS=true

# Backup Configuration
AWS_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
BACKUP_RETENTION_DAYS=7

# External Services
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
MAIL_SERVER=your-smtp-server
```

### Performance Targets

The production setup is designed to handle:

- **Response Time**: < 200ms for 95% of requests
- **Throughput**: 1000+ concurrent users
- **Uptime**: 99.9% availability
- **Database**: < 100ms query response time
- **Cache Hit Rate**: > 90% for frequently accessed data

### Health Monitoring

Access monitoring endpoints:

- **Health Check**: `GET /health` - Overall system health
- **Liveness Probe**: `GET /health/live` - Application responsiveness
- **Readiness Probe**: `GET /health/ready` - Ready to serve traffic
- **Metrics**: `GET /metrics` - Prometheus metrics
- **Grafana Dashboard**: `http://your-domain:3000` (admin/password from env)

## Development Workflow

### Database Management

The application uses PostgreSQL and follows these practices:

- Development environment uses Docker volumes for persistence
- Database can be reset using: `docker-compose down --volumes && docker-compose up -d`
- Migrations are stored in the `migrations/` directory
- New migrations can be created with: `flask db migrate -m "Description"`
- Apply migrations with: `flask db upgrade`

### Running Tests

```bash
# Ensure your virtual environment is activated
python3 -m pytest tests/
```

### Project Structure

```
.
├── app/                          # Main application package
│   ├── models/                  # Database models
│   ├── templates/               # Jinja2 templates
│   ├── static/                  # Static assets
│   ├── utils/                   # Production utilities
│   │   ├── backup_manager.py    # Automated backup system
│   │   ├── cache_manager.py     # Redis caching layer
│   │   ├── db_optimizer.py      # Database performance optimization
│   │   ├── health_checks.py     # System health monitoring
│   │   ├── monitoring.py        # Prometheus metrics & Sentry
│   │   ├── structured_logging.py # JSON logging with context
│   │   └── validation.py        # Advanced input validation
│   └── views/                   # Route handlers
├── migrations/                   # Database migrations
├── tests/                       # Test suite
├── docs/                        # Documentation
├── scripts/                     # Deployment scripts
│   └── backup.sh               # Automated backup script
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── Dockerfile                  # Development container
├── Dockerfile.prod             # Production container (security hardened)
├── Dockerfile.backup           # Backup service container
├── requirements.txt            # Python dependencies
└── PRODUCTION_READINESS_PLAN.md # Detailed production guide
```

## 📦 Dependencies & Architecture

### Core Dependencies

**Application Framework:**
- Flask 2.0+ with production WSGI server (Gunicorn)
- SQLAlchemy with PostgreSQL 14+ for database
- Redis 7+ for caching and session storage

**Production Features:**
- **Monitoring**: Prometheus metrics, Sentry error tracking
- **Security**: Marshmallow validation, Bleach XSS protection, Flask-Limiter rate limiting
- **Performance**: Flask-Caching with Redis, psutil for system monitoring
- **Backup**: Boto3 for S3 integration, automated PostgreSQL backups
- **Logging**: Structured JSON logging with request context

**External Integrations:**
- **Calendar**: iCalendar, python-dateutil for multi-platform sync
- **Communication**: Twilio for SMS, Flask-Mail for email
- **Media**: Pillow for image processing, python-magic for file validation
- **Analytics**: Pandas, NumPy for data analysis and reporting

### Production Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │     Redis       │    │   PostgreSQL    │
│  (Cloudflare)   │    │   (Caching)     │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │◄───┤   Monitoring    │    │     Backup      │
│  (Gunicorn)     │    │ Prometheus/Sentry│    │   (S3 + Local)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Calendar Integration

The system supports calendar integration with various booking platforms. For detailed setup instructions, see [README_CALENDARS.md](README_CALENDARS.md).

Key features include:
- Multi-platform calendar sync (Airbnb, VRBO, Booking.com)
- Automated synchronization
- Visual booking management
- Platform-specific color coding

## User Guides

### Property Owner

As a property owner, you can:

- **Dashboard**: View an overview of all properties, upcoming bookings, and pending tasks
- **Property Management**: Add and edit property details, amenities, and access information
- **Calendar**: Import and view bookings from various platforms (Airbnb, VRBO, etc.)
- **Tasks**: Create cleaning and maintenance tasks, assign them to staff
- **Inventory**: Track supplies and assets for each property
- **Reports**: View cleaning session reports and maintenance history
- **Guest Access**: Configure guest access portal with property-specific information

### Cleaner

As a cleaner, you can:

- **Dashboard**: View your upcoming cleaning assignments
- **Cleaning Sessions**: Start/end cleaning sessions with before/after documentation
- **Checklists**: Follow property-specific cleaning checklists
- **Inventory**: Report low inventory items
- **Issues**: Report maintenance issues discovered during cleaning
- **History**: View your completed cleaning sessions and feedback

### Maintenance Staff

As maintenance staff, you can:

- **Dashboard**: View maintenance requests assigned to you
- **Requests**: Accept, update, and complete maintenance requests
- **Documentation**: Upload photos of repairs and maintenance work
- **Tasks**: View recurring maintenance tasks assigned to you
- **History**: Track your completed maintenance tasks

### Guest Access

Guests with a property-specific access link can:

- View property details and photos
- Access check-in and check-out instructions
- Find WiFi information
- View house rules and emergency contacts
- Discover local attractions and recommendations

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
