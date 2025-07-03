import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskStatus, TaskPriority, 
                       Property, RepairRequestSeverity)
from config import TestConfig
import os
import shutil


class TestRepairRequests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )
        
        self.tenant = User(
            first_name='Test',
            last_name='Tenant',
            email='tenant@example.com',
            role=UserRoles.TENANT.value
        )
        
        db.session.add_all([self.owner, self.tenant])
        db.session.commit()
        
        # Create test property
        self.property = Property(
            name='Test Property',
            description='A test property',
            address='123 Test St, Test City, Test State 12345',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.owner.id
        )
        
        db.session.add(self.property)
        db.session.commit()
        
        # Create uploads directory for testing
        self.upload_dir = os.path.join(self.app.root_path, 'static', 'uploads', 'repair_requests')
        os.makedirs(self.upload_dir, exist_ok=True)
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        # Clean up test upload directory
        if os.path.exists(self.upload_dir):
            shutil.rmtree(self.upload_dir)
    
    def test_create_repair_request(self):
        """Test creating a repair request task"""
        repair_request = Task(
            title='Broken Window',
            description='Window in living room is broken',
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            severity=RepairRequestSeverity.URGENT.value,
            creator_id=self.tenant.id,
            property_id=self.property.id,
            location='Living Room',
            notes='Glass needs to be replaced'
        )
        repair_request.photo_paths_list = ['test_photo1.jpg', 'test_photo2.jpg']
        
        db.session.add(repair_request)
        db.session.commit()
        
        # Verify the repair request was created correctly
        retrieved_request = Task.query.get(repair_request.id)
        self.assertEqual(retrieved_request.title, 'Broken Window')
        self.assertEqual(retrieved_request.severity, RepairRequestSeverity.URGENT.value)
        self.assertEqual(len(retrieved_request.photo_paths_list), 2)
        self.assertEqual(retrieved_request.location, 'Living Room')
    
    def test_repair_request_status_updates(self):
        """Test updating repair request status"""
        repair_request = Task(
            title='Leaky Faucet',
            description='Kitchen faucet is leaking',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            severity=RepairRequestSeverity.MEDIUM.value,
            creator_id=self.tenant.id,
            property_id=self.property.id
        )
        
        db.session.add(repair_request)
        db.session.commit()
        
        # Update status to in progress
        repair_request.status = TaskStatus.IN_PROGRESS
        db.session.commit()
        self.assertEqual(repair_request.status, TaskStatus.IN_PROGRESS)
        
        # Mark as completed
        repair_request.mark_completed(self.owner.id)
        db.session.commit()
        self.assertEqual(repair_request.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(repair_request.completed_at)
    
    def test_repair_request_with_photos(self):
        """Test repair request with photo uploads"""
        # Create test photo files
        test_photos = ['test1.jpg', 'test2.jpg']
        for photo in test_photos:
            with open(os.path.join(self.upload_dir, photo), 'w') as f:
                f.write('test photo content')
        
        repair_request = Task(
            title='Damaged Wall',
            description='Wall damage in bedroom',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            severity=RepairRequestSeverity.MEDIUM.value,
            creator_id=self.tenant.id,
            property_id=self.property.id
        )
        repair_request.photo_paths_list = test_photos
        
        db.session.add(repair_request)
        db.session.commit()
        
        # Verify photos are associated with the request
        retrieved_request = Task.query.get(repair_request.id)
        self.assertEqual(len(retrieved_request.photo_paths_list), 2)
        for photo in test_photos:
            self.assertIn(photo, retrieved_request.photo_paths_list)
            self.assertTrue(os.path.exists(os.path.join(self.upload_dir, photo)))
    
    def test_repair_request_validation(self):
        """Test repair request validation"""
        # Test that valid severity values work
        valid_task = Task(
            title='Valid Request',
            description='Test valid severity',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            severity=RepairRequestSeverity.MEDIUM.value,
            creator_id=self.tenant.id,
            property_id=self.property.id
        )
        
        db.session.add(valid_task)
        db.session.commit()
        
        # Verify the task was created successfully
        retrieved_task = Task.query.get(valid_task.id)
        self.assertEqual(retrieved_task.severity, RepairRequestSeverity.MEDIUM.value)
        
        # Test missing required fields - SQLAlchemy will raise IntegrityError for missing NOT NULL fields
        from sqlalchemy.exc import IntegrityError
        with self.assertRaises(IntegrityError):
            invalid_task = Task(
                # Missing title (NOT NULL field)
                description='Missing title',
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                severity=RepairRequestSeverity.MEDIUM.value,
                creator_id=self.tenant.id,
                property_id=self.property.id
            )
            db.session.add(invalid_task)
            db.session.commit()


if __name__ == '__main__':
    unittest.main() 