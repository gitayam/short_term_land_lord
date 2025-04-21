#!/usr/bin/env python
"""
Test script for TaskTemplate model functionality.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text, inspect
from app.models import User, TaskTemplate

def test_task_template():
    """Test the TaskTemplate model functionality"""
    print("Starting TaskTemplate model test...")

    # Create app context
    app = create_app()

    with app.app_context():
        # Test database dialect detection
        dialect = db.engine.dialect.name
        print(f"Detected database dialect: {dialect}")

        # Test table name
        print(f"\nTaskTemplate model table name: {TaskTemplate.__tablename__}")

        # Test direct table access
        print("\nTesting direct table access...")
        try:
            # Count templates
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {TaskTemplate.__tablename__}"))
            count = result.scalar()
            print(f"Found {count} task templates in table")

            # List templates
            result = db.session.execute(text(f"SELECT id, title FROM {TaskTemplate.__tablename__} LIMIT 5"))
            templates = result.fetchall()
            if templates:
                print("\nFirst 5 task templates:")
                for template in templates:
                    print(f"- ID: {template.id}, Title: {template.title}")
            else:
                print("No task templates found in table")
        except Exception as e:
            print(f"Error accessing task template table directly: {e}")

        # Test ORM access
        print("\nTesting ORM access...")
        try:
            templates = TaskTemplate.query.all()
            print(f"Found {len(templates)} task templates via ORM")
            if templates:
                print("\nFirst 5 task templates via ORM:")
                for template in templates[:5]:
                    print(f"- ID: {template.id}, Title: {template.title}")
        except Exception as e:
            print(f"Error accessing task templates via ORM: {e}")

        # Test template creation
        print("\nTesting task template creation...")
        try:
            # Create a test user if none exists
            test_user = User.query.filter_by(email="test@example.com").first()
            if not test_user:
                test_user = User(
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                    password_hash="test"
                )
                db.session.add(test_user)
                db.session.commit()

            # Create a new task template
            new_template = TaskTemplate(
                title="Test Template",
                description="This is a test task template",
                priority="medium",
                estimated_duration=timedelta(hours=2),
                creator_id=test_user.id
            )
            db.session.add(new_template)
            db.session.commit()
            print(f"Created new task template: {new_template.title} (ID: {new_template.id})")

            # Test template retrieval
            retrieved_template = TaskTemplate.query.get(new_template.id)
            print(f"Retrieved template: {retrieved_template.title}")
            print(f"Template creator: {retrieved_template.creator.email}")

        except Exception as e:
            print(f"Error creating/retrieving task template: {e}")

        print("\nTaskTemplate model test complete!")

if __name__ == "__main__":
    test_task_template()