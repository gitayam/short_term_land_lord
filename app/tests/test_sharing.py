"""
Tests for the repair request sharing functionality.
"""

import unittest
from datetime import datetime, timedelta
from flask import url_for
from app import create_app, db
from app.models import User, Property, Task, RepairRequestShare, ShareAccessLog, UserRoles, TaskStatus, TaskPriority
from app.services.share_service import ShareService
from config import TestConfig


class TestSharingFunctionality(unittest.TestCase):
    """Test cases for repair request sharing features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Configure test client
        self.client = self.app.test_client()
        
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
        
        self.service_staff = User(
            username='staff',
            first_name='Service',
            last_name='Staff',
            email='staff@example.com',
            role=UserRoles.SERVICE_STAFF.value,
            is_active=True
        )
        self.service_staff.set_password('testpass123')
        
        db.session.add(self.property_owner)
        db.session.add(self.service_staff)
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
            tags='repair_request'  # Tags as comma-separated string
        )
        db.session.add(self.repair_task)
        db.session.commit()
        
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_user(self, user):
        """Helper method to log in a user"""
        return self.client.post('/auth/login', data={
            'username': user.username,
            'password': 'testpass123'
        }, follow_redirects=True)
    
    def test_share_service_create_share_for_task(self):
        """Test creating a share link for a task-based repair request"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=24*7
        )
        
        self.assertIsNotNone(share)
        self.assertEqual(share.task_id, self.repair_task.id)
        self.assertIsNone(share.repair_request_id)
        self.assertEqual(share.created_by, self.property_owner.id)
        self.assertEqual(share.share_type, 'public')
        self.assertTrue(share.is_active)
        self.assertIsNotNone(share.share_token)
        self.assertIsNotNone(share.expires_at)
    
    def test_share_service_create_password_protected_share(self):
        """Test creating a password-protected share link"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            password='secret123',
            notes='Shared with contractor'
        )
        
        self.assertIsNotNone(share)
        self.assertEqual(share.share_type, 'password')
        self.assertIsNotNone(share.password_hash)
        self.assertTrue(share.check_password('secret123'))
        self.assertFalse(share.check_password('wrong_password'))
        self.assertEqual(share.notes, 'Shared with contractor')
    
    def test_share_service_token_generation(self):
        """Test that share tokens are unique and secure"""
        share1 = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        share2 = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        self.assertNotEqual(share1.share_token, share2.share_token)
        self.assertGreaterEqual(len(share1.share_token), 32)  # Secure length
        self.assertGreaterEqual(len(share2.share_token), 32)
    
    def test_share_expiration(self):
        """Test share link expiration functionality"""
        # Create expired share
        expired_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=-1  # Already expired
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
    
    def test_share_access_verification(self):
        """Test share access verification with different scenarios"""
        # Test public share access
        public_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        success, error = ShareService.verify_share_access(
            public_share, None, '192.168.1.1', 'Test User Agent'
        )
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Test password-protected share access
        password_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            password='secret123'
        )
        
        # Wrong password
        success, error = ShareService.verify_share_access(
            password_share, 'wrong_password', '192.168.1.1', 'Test User Agent'
        )
        self.assertFalse(success)
        self.assertIsNotNone(error)
        
        # Correct password
        success, error = ShareService.verify_share_access(
            password_share, 'secret123', '192.168.1.1', 'Test User Agent'
        )
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Test expired share
        expired_share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=-1
        )
        
        success, error = ShareService.verify_share_access(
            expired_share, None, '192.168.1.1', 'Test User Agent'
        )
        self.assertFalse(success)
        self.assertIn('expired', error.lower())
    
    def test_share_access_logging(self):
        """Test that share access is properly logged"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        # Verify access (should create log entry)
        ShareService.verify_share_access(
            share, None, '192.168.1.100', 'Mozilla/5.0 Test Browser'
        )
        
        # Check that access log was created
        access_logs = ShareAccessLog.query.filter_by(share_id=share.id).all()
        self.assertEqual(len(access_logs), 1)
        
        log = access_logs[0]
        self.assertEqual(log.ip_address, '192.168.1.100')
        self.assertEqual(log.user_agent, 'Mozilla/5.0 Test Browser')
        self.assertTrue(log.access_granted)
        self.assertIsNone(log.failure_reason)
    
    def test_share_view_count_increment(self):
        """Test that view count is incremented on access"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        initial_count = share.view_count
        self.assertEqual(initial_count, 0)
        
        # Verify access (should increment view count)
        ShareService.verify_share_access(share, None, '192.168.1.1', 'Test Agent')
        
        # Refresh from database
        db.session.refresh(share)
        self.assertEqual(share.view_count, initial_count + 1)
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
        self.assertFalse(share.is_valid())
        
        # Test access to revoked share
        success, error = ShareService.verify_share_access(
            share, None, '192.168.1.1', 'Test Agent'
        )
        self.assertFalse(success)
        self.assertIn('revoked', error.lower())
    
    def test_create_share_api_endpoint(self):
        """Test the API endpoint for creating share links"""
        # Login as property owner
        self.login_user(self.property_owner)
        
        # Test creating public share
        response = self.client.post(f'/share/api/repair/{self.repair_task.id}/share',
                                  json={
                                      'expiration': '7d',
                                      'notes': 'Test share'
                                  })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('share', data)
        self.assertIn('share_token', data['share'])
        
        # Test creating password-protected share
        response = self.client.post(f'/share/api/repair/{self.repair_task.id}/share',
                                  json={
                                      'expiration': '24h',
                                      'password': 'secret123',
                                      'notes': 'Password protected'
                                  })
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['share']['share_type'], 'password')
    
    def test_share_api_permission_check(self):
        """Test that only authorized users can create shares"""
        # Login as service staff (not owner)
        self.login_user(self.service_staff)
        
        response = self.client.post(f'/share/api/repair/{self.repair_task.id}/share',
                                  json={'expiration': 'never'})
        
        self.assertEqual(response.status_code, 403)
    
    def test_view_shared_repair_request(self):
        """Test viewing a shared repair request"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        # Test accessing public share
        response = self.client.get(f'/share/repair/{share.share_token}')
        self.assertEqual(response.status_code, 200)
        
        # Check that repair request details are in response
        html_content = response.get_data(as_text=True)
        self.assertIn('garbage disposal not working', html_content.lower())
        self.assertIn('kitchen', html_content.lower())
        self.assertIn('high', html_content.lower())
    
    def test_password_protected_share_view(self):
        """Test viewing a password-protected shared repair request"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            password='secret123'
        )
        
        # Test accessing without password (should show password prompt)
        response = self.client.get(f'/share/repair/{share.share_token}')
        self.assertEqual(response.status_code, 200)
        html_content = response.get_data(as_text=True)
        self.assertIn('password', html_content.lower())
        
        # Test submitting correct password
        response = self.client.post(f'/share/repair/{share.share_token}/verify',
                                  data={'password': 'secret123'})
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Test submitting wrong password
        response = self.client.post(f'/share/repair/{share.share_token}/verify',
                                  data={'password': 'wrong_password'})
        self.assertEqual(response.status_code, 200)  # Stay on password page
        html_content = response.get_data(as_text=True)
        self.assertIn('invalid password', html_content.lower())
    
    def test_invalid_share_token(self):
        """Test accessing non-existent share token"""
        response = self.client.get('/share/repair/invalid_token_12345')
        self.assertEqual(response.status_code, 404)
    
    def test_share_to_dict_serialization(self):
        """Test share object serialization for API responses"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id,
            expires_in_hours=48,
            notes='Test serialization'
        )
        
        share_dict = share.to_dict()
        
        self.assertIn('id', share_dict)
        self.assertIn('share_token', share_dict)
        self.assertIn('created_at', share_dict)
        self.assertIn('expires_at', share_dict)
        self.assertIn('is_active', share_dict)
        self.assertIn('view_count', share_dict)
        self.assertIn('share_type', share_dict)
        self.assertIn('notes', share_dict)
        self.assertIn('share_url', share_dict)
        
        self.assertEqual(share_dict['share_type'], 'public')
        self.assertEqual(share_dict['notes'], 'Test serialization')
        self.assertTrue(share_dict['is_active'])
    
    def test_property_address_anonymization(self):
        """Test that property addresses are properly anonymized in shared views"""
        share = ShareService.create_share(
            task_id=self.repair_task.id,
            created_by=self.property_owner.id
        )
        
        response = self.client.get(f'/share/repair/{share.share_token}')
        html_content = response.get_data(as_text=True)
        
        # Should show anonymized address (without house number)
        self.assertIn('Test City', html_content)
        self.assertIn('Test State', html_content)
        # Should NOT show exact house number for privacy
        self.assertNotIn('123 Test Street', html_content)


if __name__ == '__main__':
    unittest.main()