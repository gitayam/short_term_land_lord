#!/usr/bin/env python3
"""
Test script for workforce property assignment fix
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Property, Task, TaskAssignment, TaskProperty, UserRoles, ServiceType, TaskStatus
from flask import current_app

def test_assignment_logic():
    """Test the assignment logic without actually running the web interface"""
    app = create_app()
    
    with app.app_context():
        print("Testing workforce assignment logic...")
        
        # Find or create test data
        worker = User.query.filter_by(role=UserRoles.SERVICE_STAFF.value).first()
        if not worker:
            print("No service staff found. Creating test worker...")
            worker = User(
                first_name="Test",
                last_name="Worker",
                email="test.worker@example.com",
                role=UserRoles.SERVICE_STAFF.value
            )
            worker.set_password("testpassword")
            db.session.add(worker)
            db.session.commit()
        
        property = Property.query.first()
        if not property:
            print("No properties found. Creating test property...")
            # Find an admin or property owner to be the owner
            owner = User.query.filter(
                User.role.in_([UserRoles.ADMIN.value, UserRoles.PROPERTY_OWNER.value])
            ).first()
            if not owner:
                print("No admin or property owner found. Creating one...")
                owner = User(
                    first_name="Test",
                    last_name="Owner",
                    email="test.owner@example.com",
                    role=UserRoles.PROPERTY_OWNER.value
                )
                owner.set_password("testpassword")
                db.session.add(owner)
                db.session.commit()
            
            property = Property(
                name="Test Property",
                address="123 Test St",
                owner_id=owner.id,
                property_type="house"
            )
            db.session.add(property)
            db.session.commit()
        
        print(f"Using worker: {worker.get_full_name()} (ID: {worker.id})")
        print(f"Using property: {property.name} (ID: {property.id})")
        
        # Test the assignment logic
        service_type = ServiceType.CLEANING
        
        try:
            # Create a task (similar to the fixed logic)
            task = Task(
                title=f"{service_type.name} Assignment for {property.name}",
                description=f"This task establishes {worker.get_full_name()} as a {service_type.name} for {property.name}.",
                status=TaskStatus.PENDING,
                creator_id=1  # Assuming admin user has ID 1
            )
            
            # Add task to session first to get an ID
            db.session.add(task)
            db.session.flush()  # This will assign an ID to the task without committing
            
            print(f"Created task with ID: {task.id}")
            
            # Validate that task has an ID
            if not task.id:
                raise Exception("Failed to create task - no ID assigned")
            
            # Now create the task_property with the task's ID
            task_property = TaskProperty(
                task_id=task.id,
                property_id=property.id,
                sequence_number=0
            )
            db.session.add(task_property)
            
            # Assign worker to task
            task_assignment = TaskAssignment(
                task_id=task.id,
                user_id=worker.id,
                service_type=service_type
            )
            db.session.add(task_assignment)
            
            # Commit the transaction
            db.session.commit()
            
            print("✅ SUCCESS: Worker assigned to property successfully!")
            print(f"   Task ID: {task.id}")
            print(f"   TaskProperty ID: {task_property.id}")
            print(f"   TaskAssignment ID: {task_assignment.id}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR: {str(e)}")
            return False

if __name__ == "__main__":
    if test_assignment_logic():
        print("\n🎉 Test passed! The workforce assignment fix is working correctly.")
    else:
        print("\n💥 Test failed! There may still be issues with the assignment logic.")