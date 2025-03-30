# Short Term Land Lord

A comprehensive property management system designed specifically for short-term rental properties. This platform streamlines the coordination between property owners, cleaners, and maintenance staff while providing enhanced calendar integration with popular booking platforms like Airbnb and VRBO.

## Features

- **Calendar Management**: Import calendar events from Airbnb, VRBO, and other booking platforms
- **Property Management**: Track property details, amenities, and access information
- **Task Management**: Assign and track cleaning and maintenance tasks
- **User Role System**: Different interfaces and permissions for property owners, cleaners, and maintenance staff
- **Inventory Management**: Track supplies and assets for each property
- **Cleaning Sessions**: Document cleaning with before/after videos and photos
- **Maintenance Requests**: Report and track maintenance issues
- **Guest Access Portal**: Provide information to guests with customizable access

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL
- Git

### Local Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/gitayam/short_term_land_lord.git
   cd short_term_land_lord
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

5. Configure your environment variables in `.env`:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://username:password@localhost/stll_db
   SECRET_KEY=your_secret_key
   ```

6. Initialize the database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. Run the application:
   ```bash
   flask run
   ```

8. Access the application at http://localhost:5000

## Docker Setup

Using Docker is the recommended way to run the application as it ensures consistency across environments.

### Prerequisites

- Docker
- Docker Compose

### Running with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/gitayam/short_term_land_lord.git
   cd short_term_land_lord
   ```

2. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

3. The application will be available at http://localhost:5001

4. To view logs:
   ```bash
   docker-compose logs -f
   ```

5. To stop the containers:
   ```bash
   docker-compose down
   ```

### Database Migrations with Docker

To run database migrations in the Docker environment:

```bash
docker-compose exec web flask db upgrade
```

If you need to create a new migration:

```bash
docker-compose exec web flask db migrate -m "Description of changes"
```

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
