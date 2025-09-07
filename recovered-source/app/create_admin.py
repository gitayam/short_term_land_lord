#!/usr/bin/env python3
"""
Script to manually create an admin user from environment variables.
Run this script with: flask --app create_admin.py create-admin
"""
from flask import Flask
from flask.cli import with_appcontext
import click
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    """Create a minimal Flask app for running the command"""
    app = Flask(__name__)
    
    # Configure the app with database settings
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:"
        f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@"
        f"{os.environ.get('POSTGRES_HOST', 'db')}/"
        f"{os.environ.get('POSTGRES_DB', 'flask_app')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Import and initialize extensions
    from app import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register the command
    app.cli.add_command(create_admin_command)
    
    return app

@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Create an admin user from environment variables."""
    from app.models import User, UserRoles
    from app import db
    
    # Get admin credentials from environment
    admin_email = os.environ.get('ADMIN_EMAIL')
    admin_username = os.environ.get('ADMIN_USERNAME')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    admin_first_name = os.environ.get('ADMIN_FIRST_NAME', 'System')
    admin_last_name = os.environ.get('ADMIN_LAST_NAME', 'Administrator')
    
    if not admin_email or not admin_password:
        click.echo('Admin credentials not fully specified in environment variables.')
        click.echo('Please set ADMIN_EMAIL and ADMIN_PASSWORD in your .env file.')
        return
    
    # Check if admin user already exists
    from sqlalchemy import or_
    query = User.query.filter(User.email == admin_email)
    if admin_username:
        query = query.union(User.query.filter(User.username == admin_username))
    
    existing_admin = query.first()
    
    if existing_admin:
        click.echo(f"Admin user already exists: {existing_admin.email}")
        # Update admin role if needed
        if existing_admin.role != UserRoles.ADMIN.value:
            existing_admin.role = UserRoles.ADMIN.value
            existing_admin.is_admin = True
            db.session.commit()
            click.echo(f"Updated user {existing_admin.email} to admin role")
        return
    
    # Create new admin user
    admin_user = User(
        email=admin_email,
        first_name=admin_first_name,
        last_name=admin_last_name,
        role=UserRoles.ADMIN.value,
        is_admin=True
    )
    
    # Set username if provided
    if admin_username:
        admin_user.username = admin_username
    
    admin_user.set_password(admin_password)
    
    db.session.add(admin_user)
    db.session.commit()
    click.echo(f"Created admin user: {admin_email}")

if __name__ == '__main__':
    app = create_app()
    app.app_context().push()
    create_admin_command()
