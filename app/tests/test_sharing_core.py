"""
Core tests for repair request sharing functionality.
Focuses on the most critical features without complex Flask routing tests.
"""

import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Property, Task, RepairRequestShare, ShareAccessLog, UserRoles, TaskStatus, TaskPriority
from app.services.share_service import ShareService
from config import TestConfig


class TestSharingCore(unittest.TestCase):
    """Core test cases for repair request sharing features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test users
        self.property_owner = User(
            username='owner',
            first_name='Property',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER.value,
            is_active=True
        )
        self.property_owner.set_password('testpass123')
        
        db.session.add(self.property_owner)
        db.session.commit()
        
        # Create test property
        self.property = Property(
            name='Test Property',
            address='123 Test Street',
            street_address='123 Test Street',
            city='Test City',
            state='Test State',
            zip_code='12345',
            owner_id=self.property_owner.id,
            status='active'
        )
        db.session.add(self.property)
        db.session.commit()
        
        # Create test repair request task
        self.repair_task = Task(
            title='Garbage disposal not working',
            description='won\'t turn on. I have tried to turn it with an Allen wrench but didn\'t work.',
            location='kitchen',
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            creator_id=self.property_owner.id,
            due_date=datetime.utcnow() + timedelta(days=1),
            tags='repair_request'
        )
        db.session.add(self.repair_task)
        db.session.commit()
        
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_public_share(self):
        """Test creating a public share link"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=24*7
        )
        
        self.assertIsNotNone(share)
        self.assertEqual(share.task_id, self.repair_task.id)
        self.assertEqual(share.share_type, 'public')
        self.assertTrue(share.is_active)
        self.assertIsNotNone(share.share_token)
        self.assertGreaterEqual(len(share.share_token), 32)
        
    def test_create_password_protected_share(self):
        """Test creating a password-protected share"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            password='secret123',
            notes='Test password share'
        )
        
        self.assertEqual(share.share_type, 'password')
        self.assertIsNotNone(share.password_hash)
        self.assertTrue(share.check_password('secret123'))
        self.assertFalse(share.check_password('wrong_password'))
        
    def test_share_expiration(self):
        """Test share expiration logic"""
        # Create expired share
        expired_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=-1
        )
        
        self.assertTrue(expired_share.is_expired())
        self.assertFalse(expired_share.is_valid())
        
        # Create valid share
        valid_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=24
        )
        
        self.assertFalse(valid_share.is_expired())
        self.assertTrue(valid_share.is_valid())
        
    def test_access_verification_scenarios(self):
        """Test various access verification scenarios"""
        # Public share - should succeed
        public_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        success, error = ShareService.verify_share_access(
            public_share, None, '192.168.1.1', 'Test Browser'
        )
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Password share with correct password
        password_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            password='secret123'
        )
        
        success, error = ShareService.verify_share_access(
            password_share, 'secret123', '192.168.1.1', 'Test Browser'
        )
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Password share with wrong password
        success, error = ShareService.verify_share_access(
            password_share, 'wrong_password', '192.168.1.1', 'Test Browser'
        )
        self.assertFalse(success)
        self.assertIsNotNone(error)
        
    def test_access_logging(self):
        """Test that access attempts are logged"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        # Access the share
        ShareService.verify_share_access(
            share, None, '192.168.1.100', 'Mozilla/5.0 Test'
        )
        
        # Check access log
        logs = ShareAccessLog.query.filter_by(share_id=share.id).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].ip_address, '192.168.1.100')
        self.assertTrue(logs[0].access_granted)
        
    def test_view_count_tracking(self):
        """Test that view counts are properly tracked"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        initial_count = share.view_count
        self.assertEqual(initial_count, 0)
        
        # Access multiple times
        for i in range(3):
            ShareService.verify_share_access(
                share, None, f'192.168.1.{i}', f'Browser {i}'
            )
        
        # Refresh from database
        db.session.refresh(share)
        self.assertEqual(share.view_count, 3)
        self.assertIsNotNone(share.last_viewed_at)
        
    def test_share_revocation(self):
        """Test share link revocation"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        self.assertTrue(share.is_active)
        
        # Revoke the share
        share.revoke()
        self.assertFalse(share.is_active)
        
        # Test access to revoked share
        success, error = ShareService.verify_share_access(
            share, None, '192.168.1.1', 'Test Browser'
        )
        self.assertFalse(success)
        self.assertIn('revoked', error.lower())
        
    def test_share_serialization(self):
        """Test share object serialization"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=48,
            notes='Test serialization'
        )
        
        share_dict = share.to_dict()
        
        required_fields = [
            'id', 'share_token', 'created_at', 'expires_at',
            'is_active', 'view_count', 'share_type', 'notes'
        ]
        
        for field in required_fields:
            self.assertIn(field, share_dict)
            
        self.assertEqual(share_dict['share_type'], 'public')
        self.assertEqual(share_dict['notes'], 'Test serialization')
        
    def test_token_uniqueness(self):
        """Test that generated tokens are unique"""
        tokens = set()
        
        for i in range(10):
            share = ShareService.create_share(
                task_id=self.repair_task.id,
                created_by=self.property_owner.id
            )
            tokens.add(share.share_token)
            
        # All tokens should be unique
        self.assertEqual(len(tokens), 10)
        
    def test_shared_item_property(self):
        """Test the shared_item property returns correct object"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        shared_item = share.shared_item
        self.assertIsNotNone(shared_item)
        self.assertEqual(shared_item.id, self.repair_task.id)
        self.assertEqual(shared_item.title, 'Garbage disposal not working')
        
    def test_property_address_anonymization(self):
        """Test property address anonymization for privacy"""
        # This test verifies the property has anonymization methods
        anonymized = self.property.get_anonymized_address()
        self.assertIsNotNone(anonymized)
        
        # Should contain general location info but not exact address
        self.assertIn('Test City', anonymized)
        self.assertIn('Test State', anonymized)


if __name__ == '__main__':
    unittest.main()