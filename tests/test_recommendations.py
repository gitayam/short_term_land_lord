import pytest
from flask_login import current_user
from app import db, create_app
from app.models import User, Property, RecommendationBlock, UserRoles
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Client that's already logged in as a property owner"""
    with client:
        # Create and log in as property owner
        owner = User(
            email='owner@test.com',
            password_hash=generate_password_hash('password'),
            role=UserRoles.PROPERTY_OWNER.value,
            first_name='Test',
            last_name='Owner'
        )
        db.session.add(owner)
        db.session.commit()
        
        # Create a property for testing
        property = Property(
            name='Test Property',
            address='123 Test St',
            owner_id=owner.id
        )
        db.session.add(property)
        db.session.commit()
        
        # Log in
        client.post('/auth/login', data={
            'email': 'owner@test.com',
            'password': 'password'
        }, follow_redirects=True)
        
        yield client

@pytest.fixture
def admin_client(client):
    """Client that's already logged in as an admin"""
    with client:
        # Create and log in as admin
        admin = User(
            email='admin@test.com',
            password_hash=generate_password_hash('password'),
            role=UserRoles.ADMIN.value,
            first_name='Test',
            last_name='Admin',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        
        # Log in
        client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'password'
        }, follow_redirects=True)
        
        yield client

def test_create_recommendation(auth_client):
    """Test creating a new recommendation"""
    property = Property.query.first()
    
    # Create recommendation
    response = auth_client.post(f'/recommendations/property/{property.id}/new', data={
        'title': 'Test Restaurant',
        'description': 'A great local restaurant',
        'category': 'food',
        'map_link': 'https://maps.google.com/test',
        'best_time_to_go': 'Evening',
        'recommended_meal': 'Dinner',
        'wifi_name': 'Restaurant WiFi',
        'wifi_password': 'testpass',
        'parking_details': 'Street parking available',
        'add_to_guide': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Recommendation added successfully!' in response.data
    
    # Verify recommendation was created
    recommendation = RecommendationBlock.query.filter_by(title='Test Restaurant').first()
    assert recommendation is not None
    assert recommendation.in_guide_book is True
    assert recommendation.category == 'food'
    assert recommendation.best_time_to_go == 'Evening'

def test_edit_recommendation(auth_client):
    """Test editing an existing recommendation"""
    property = Property.query.first()
    
    # Create recommendation first
    recommendation = RecommendationBlock(
        property_id=property.id,
        title='Original Title',
        description='Original description',
        category='food',
        map_link='https://maps.google.com/original',
        in_guide_book=False
    )
    db.session.add(recommendation)
    db.session.commit()
    
    # Edit recommendation
    response = auth_client.post(f'/recommendations/{recommendation.id}/edit', data={
        'title': 'Updated Title',
        'description': 'Updated description',
        'category': 'food',
        'map_link': 'https://maps.google.com/updated',
        'best_time_to_go': 'Morning',
        'recommended_meal': 'Breakfast',
        'add_to_guide': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Recommendation updated successfully!' in response.data
    
    # Verify changes
    updated = RecommendationBlock.query.get(recommendation.id)
    assert updated.title == 'Updated Title'
    assert updated.description == 'Updated description'
    assert updated.in_guide_book is True
    assert updated.best_time_to_go == 'Morning'

def test_delete_recommendation(auth_client):
    """Test deleting a recommendation"""
    property = Property.query.first()
    
    # Create recommendation first
    recommendation = RecommendationBlock(
        property_id=property.id,
        title='Test Delete',
        description='To be deleted',
        category='food',
        map_link='https://maps.google.com/delete',
        in_guide_book=True
    )
    db.session.add(recommendation)
    db.session.commit()
    
    # Delete recommendation
    response = auth_client.post(f'/recommendations/{recommendation.id}/delete', 
                              follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Recommendation deleted successfully!' in response.data
    
    # Verify deletion
    deleted = RecommendationBlock.query.get(recommendation.id)
    assert deleted is None

def test_admin_access(admin_client):
    """Test that admins can manage recommendations for any property"""
    # Create a property owned by someone else
    owner = User(
        email='other@test.com',
        password_hash=generate_password_hash('password'),
        role=UserRoles.PROPERTY_OWNER.value
    )
    db.session.add(owner)
    db.session.commit()
    
    property = Property(
        name='Other Property',
        address='456 Other St',
        owner_id=owner.id
    )
    db.session.add(property)
    db.session.commit()
    
    # Try to create recommendation as admin
    response = admin_client.post(f'/recommendations/property/{property.id}/new', data={
        'title': 'Admin Test',
        'description': 'Created by admin',
        'category': 'food',
        'map_link': 'https://maps.google.com/admin',
        'add_to_guide': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Recommendation added successfully!' in response.data
    
    # Verify recommendation was created
    recommendation = RecommendationBlock.query.filter_by(title='Admin Test').first()
    assert recommendation is not None

def test_unauthorized_access(client):
    """Test that unauthorized users cannot manage recommendations"""
    # Create property and recommendation
    owner = User(
        email='owner2@test.com',
        password_hash=generate_password_hash('password'),
        role=UserRoles.PROPERTY_OWNER.value
    )
    db.session.add(owner)
    db.session.commit()
    
    property = Property(
        name='Protected Property',
        address='789 Protected St',
        owner_id=owner.id
    )
    db.session.add(property)
    db.session.commit()
    
    # Try to access without login
    response = client.get(f'/recommendations/property/{property.id}/new')
    assert response.status_code == 302  # Should redirect to login
    
    # Create unauthorized user
    unauth_user = User(
        email='unauth@test.com',
        password_hash=generate_password_hash('password'),
        role=UserRoles.SERVICE_STAFF.value
    )
    db.session.add(unauth_user)
    db.session.commit()
    
    # Log in as unauthorized user
    client.post('/auth/login', data={
        'email': 'unauth@test.com',
        'password': 'password'
    })
    
    # Try to create recommendation
    response = client.post(f'/recommendations/property/{property.id}/new', data={
        'title': 'Unauthorized Test',
        'description': 'Should not work',
        'category': 'food',
        'map_link': 'https://maps.google.com/unauth'
    }, follow_redirects=True)
    
    assert b'You do not have permission' in response.data
    
    # Verify no recommendation was created
    recommendation = RecommendationBlock.query.filter_by(title='Unauthorized Test').first()
    assert recommendation is None 