import unittest
from datetime import datetime
from io import BytesIO
from app import create_app, db
from app.models import (User, UserRoles, Property, RecommendationBlock, MediaType)
from config import TestConfig
import os


class TestRecommendationRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
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
        self.owner.set_password('test_password')
        
        self.tenant = User(
            first_name='Test',
            last_name='Tenant',
            email='tenant@example.com',
            role=UserRoles.TENANT.value
        )
        self.tenant.set_password('test_password')
        
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
        self.upload_dir = os.path.join(self.app.root_path, 'static', 'uploads', 'recommendations')
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, email, password):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_recommendation_list_access(self):
        """Test access to recommendations list"""
        # Login as owner
        self.login('owner@example.com', 'test_password')
        
        # Access recommendations list
        response = self.client.get(f'/recommendations/property/{self.property.id}/list')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Recommendations', response.data)
    
    def test_create_recommendation(self):
        """Test creating a recommendation"""
        # Login as owner
        self.login('owner@example.com', 'test_password')
        
        # Create test photo
        photo = (BytesIO(b'test photo content'), 'test.jpg')
        
        # Submit recommendation
        data = {
            'title': 'Test Restaurant',
            'description': 'A great place to eat',
            'category': 'food',
            'map_link': 'https://maps.google.com/test',
            'hours': '9am-5pm',
            'photo': photo
        }
        
        response = self.client.post(f'/recommendations/property/{self.property.id}/new', 
                                  data=data,
                                  content_type='multipart/form-data',
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify recommendation was created
        recommendation = RecommendationBlock.query.filter_by(title='Test Restaurant').first()
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation.description, 'A great place to eat')
        self.assertEqual(recommendation.category, 'food')
        self.assertEqual(recommendation.map_link, 'https://maps.google.com/test')
        self.assertEqual(recommendation.hours, '9am-5pm')
        self.assertIsNotNone(recommendation.photo_path)
    
    def test_edit_recommendation(self):
        """Test editing a recommendation"""
        # Create a recommendation first
        recommendation = RecommendationBlock(
            property_id=self.property.id,
            title='Original Title',
            description='Original description',
            category='food',
            map_link='https://maps.google.com/original',
            hours='9am-5pm'
        )
        db.session.add(recommendation)
        db.session.commit()
        
        # Login as owner
        self.login('owner@example.com', 'test_password')
        
        # Edit recommendation
        data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'category': 'shopping',
            'map_link': 'https://maps.google.com/updated',
            'hours': '10am-6pm'
        }
        
        response = self.client.post(f'/recommendations/{recommendation.id}/edit',
                                  data=data,
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify changes
        updated = RecommendationBlock.query.get(recommendation.id)
        self.assertEqual(updated.title, 'Updated Title')
        self.assertEqual(updated.description, 'Updated description')
        self.assertEqual(updated.category, 'shopping')
        self.assertEqual(updated.map_link, 'https://maps.google.com/updated')
        self.assertEqual(updated.hours, '10am-6pm')
    
    def test_delete_recommendation(self):
        """Test deleting a recommendation"""
        # Create a recommendation first
        recommendation = RecommendationBlock(
            property_id=self.property.id,
            title='To Delete',
            description='Will be deleted',
            category='food',
            map_link='https://maps.google.com/delete',
            hours='9am-5pm'
        )
        db.session.add(recommendation)
        db.session.commit()
        
        # Login as owner
        self.login('owner@example.com', 'test_password')
        
        # Delete recommendation
        response = self.client.post(f'/recommendations/{recommendation.id}/delete',
                                  follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        deleted = RecommendationBlock.query.get(recommendation.id)
        self.assertIsNone(deleted)
    
    def test_recommendation_permissions(self):
        """Test recommendation access permissions"""
        # Create a recommendation
        recommendation = RecommendationBlock(
            property_id=self.property.id,
            title='Test Permission',
            description='Testing permissions',
            category='food',
            map_link='https://maps.google.com/test',
            hours='9am-5pm'
        )
        db.session.add(recommendation)
        db.session.commit()
        
        # Login as tenant
        self.login('tenant@example.com', 'test_password')
        
        # Try to access edit page
        response = self.client.get(f'/recommendations/{recommendation.id}/edit')
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Try to delete
        response = self.client.post(f'/recommendations/{recommendation.id}/delete')
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Verify recommendation still exists
        exists = RecommendationBlock.query.get(recommendation.id)
        self.assertIsNotNone(exists)


if __name__ == '__main__':
    unittest.main() 