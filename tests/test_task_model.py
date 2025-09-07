#!/usr/bin/env python
"""
Test script for Task model functionality.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import text, inspect
from app.models import User, Task, TaskAssignment, TaskProperty

def test_task_model():
    """Test the Task model functionality"""
    print("Starting Task model test...")
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Test database dialect detection
        dialect = db.engine.dialect.name
        print(f"Detected database dialect: {dialect}")
        
        # Test table names
        print(f"\nTask model table name: {Task.__tablename__}")
        print(f"TaskAssignment model table name: {TaskAssignment.__tablename__}")
        print(f"TaskProperty model table name: {TaskProperty.__tablename__}")
        
        # Test direct table access
        print("\nTesting direct table access...")
        try:
            # Count tasks
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {Task.__tablename__}"))
            count = result.scalar()
            print(f"Found {count} tasks in table")
            
            # List tasks
            result = db.session.execute(text(f"SELECT id, title, status FROM {Task.__tablename__} LIMIT 5"))
            tasks = result.fetchall()
            if tasks:
                print("\nFirst 5 tasks:")
                for task in tasks:
                    print(f"- ID: {task.id}, Title: {task.title}, Status: {task.status}")
            else:
                print("No tasks found in table")
        except Exception as e:
            print(f"Error accessing task table directly: {e}")
        
        # Test ORM access
        print("\nTesting ORM access...")
        try:
            tasks = Task.query.all()
            print(f"Found {len(tasks)} tasks via ORM")
            if tasks:
                print("\nFirst 5 tasks via ORM:")
                for task in tasks[:5]:
                    print(f"- ID: {task.id}, Title: {task.title}, Status: {task.status}")
        except Exception as e:
            print(f"Error accessing tasks via ORM: {e}")
        
        # Test task creation
        print("\nTesting task creation...")
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
            
            # Create a new task
            new_task = Task(
                title="Test Task",
                description="This is a test task",
                status="pending",
                priority="medium",
                due_date=datetime.utcnow() + timedelta(days=7),
                creator_id=test_user.id
            )
            db.session.add(new_task)
            db.session.commit()
            print(f"Created new task: {new_task.title} (ID: {new_task.id})")
            
            # Test task assignment
            assignment = TaskAssignment(
                task_id=new_task.id,
                user_id=test_user.id
            )
            db.session.add(assignment)
            db.session.commit()
            print(f"Created task assignment for user {test_user.id}")
            
        except Exception as e:
            print(f"Error creating task: {e}")
        
        print("\nTask model test complete!")

if __name__ == "__main__":
    test_task_model() 