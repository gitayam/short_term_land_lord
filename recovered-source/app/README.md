# Short Term Land Lord

A comprehensive property management system designed specifically for short-term rental properties. This platform streamlines the coordination between property owners, cleaners, and maintenance staff while providing enhanced calendar integration with popular booking platforms like Airbnb and VRBO.

**🚀 Production Deployment**: Currently deployed on Google App Engine at [https://short-term-landlord-dot-speech-memorization.uc.r.appspot.com](https://short-term-landlord-dot-speech-memorization.uc.r.appspot.com)

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

## Production Features ⭐

### Deployed Infrastructure
- **Google App Engine**: Serverless deployment with auto-scaling
- **Redis Caching**: 80-90% faster dashboard response times
- **Google Cloud Secret Manager**: Secure credential management
- **Health Monitoring**: Comprehensive system health checks and error tracking
- **Production Security**: Input validation, XSS prevention, CSRF protection

### Performance Optimizations
- **Database Connection Pooling**: Stable performance under load
- **Intelligent Caching**: User dashboard data (10min), property stats (30min), task summaries (15min)
- **Slow Query Detection**: Automatic detection and logging of queries >500ms
- **Error Tracking**: Real-time issue detection and monitoring

## Development Setup

### Prerequisites

- Git
- Docker and Docker Compose (recommended)
- If not using Docker, you will need Python 3.9+ and PostgreSQL
- For production deployment: Google Cloud SDK

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
   SECRET_KEY=your_secret_key
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

## Production Deployment 🚀

### Google App Engine Deployment

The application is configured for deployment to Google App Engine as a separate service.

1. **Setup Google Cloud SDK**:
   ```bash
   gcloud auth login
   gcloud config set project your-project-id
   ```

2. **Configure Secrets**:
   ```bash
   # Store application secrets in Google Cloud Secret Manager
   gcloud secrets create landlord-app-secrets --data-file=secrets.json
   ```

3. **Deploy to App Engine**:
   ```bash
   gcloud app deploy app_simple.yaml --project=your-project --version=production
   ```

### Production Configuration

The application uses different configurations for production:

- **Database**: SQLite with startup initialization (ephemeral but auto-recreating)
- **Caching**: Redis-based caching for performance
- **Sessions**: Secure session management
- **Logging**: Structured JSON logging with request correlation
- **Monitoring**: Health checks available at `/health` endpoint

### Debug Features

For troubleshooting production issues:

- `/debug-admin`: Check admin user status and password validation
- `/recreate-admin`: Force recreate admin user if needed
- Structured logging for error tracking

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
├── app/                    # Main application package
│   ├── models/            # Database models
│   ├── templates/         # Jinja2 templates
│   ├── static/           # Static assets
│   └── views/            # Route handlers
├── migrations/            # Database migrations
├── tests/                # Test suite
├── docs/                 # Documentation
├── docker-compose.yml    # Docker services configuration
├── Dockerfile           # Application container definition
└── requirements.txt     # Python dependencies
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

## System Architecture 🏗️

### Production Stack
- **Frontend**: Jinja2 templates with Bootstrap 5 and FullCalendar v6
- **Backend**: Flask with Blueprint architecture
- **Database**: SQLAlchemy ORM with SQLite (development) / PostgreSQL (production ready)
- **Caching**: Redis with Flask-Caching
- **Authentication**: Flask-Login with role-based access control
- **Security**: Marshmallow validation, bleach sanitization, CSRF protection
- **Deployment**: Google App Engine with Cloud Secret Manager

### Key Design Patterns
- **Application Factory Pattern**: Clean configuration management
- **Blueprint Architecture**: Modular route organization
- **Repository Pattern**: Database abstraction layer
- **Decorator Pattern**: Caching and validation decorators
- **Observer Pattern**: Event-driven task notifications

## Documentation 📚

- **[Lessons Learned](Lessons_Learned.md)**: Deployment insights and technical decisions
- **[Phase 1 Implementation](PHASE_1_IMPLEMENTATION_SUMMARY.md)**: Production infrastructure details
- **[Calendar Integration](README_CALENDARS.md)**: Multi-platform booking sync setup

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
