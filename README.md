# Property Management Calendar System

A web-based property management system centered around a calendar system for scheduling and tracking property-related work.

## Phase 1: User Authentication

This initial phase focuses on establishing the user authentication system with role-based access control.

### Features

- User registration system that collects necessary information (name, email, password, role selection)
- Secure login functionality with password hashing and session management
- Three distinct user roles with different permissions:
  * Property owners: Can view and manage their properties and associated schedules
  * Cleaners: Can view assigned cleaning tasks and schedules
  * Maintenance personnel: Can view assigned maintenance tasks and schedules
- Basic user profile management (view/edit profile information)
- Password reset functionality

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd property-management-calendar
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file with your specific configuration.

6. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

7. Run the application:
   ```
   flask run
   ```

8. Access the application at http://localhost:5000

## Project Structure

- `app/` - Main application package
  - `__init__.py` - Application factory
  - `models.py` - Database models
  - `auth/` - Authentication blueprint
  - `main/` - Main routes blueprint
  - `profile/` - User profile management blueprint
  - `templates/` - HTML templates
- `config.py` - Application configuration
- `app.py` - Application entry point

## Future Development

Phase 2 will include:
- Calendar import functionality from Airbnb and Zillow
- Automatic scheduling of cleaning tasks
- Advanced calendar views and interactions
- Property management features
