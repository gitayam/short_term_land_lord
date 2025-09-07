import pytest
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
def setup_data(client):
    """Set up test data including property, recommendations, and users"""
    with client:
        # Create property owner
        owner = User(
            email='owner@test.com',
            password_hash=generate_password_hash('password'),
            role=UserRoles.PROPERTY_OWNER.value,
            first_name='Test',
            last_name='Owner'
        )
        db.session.add(owner)
        db.session.commit()
        
        # Create property
        property = Property(
            name='Test Property',
            address='123 Test St',
            owner_id=owner.id
        )
        db.session.add(property)
        db.session.commit()
        
        # Create some recommendations, some in guide book and some not
        recommendations = [
            RecommendationBlock(
                property_id=property.id,
                title='Guide Restaurant 1',
                description='In guide book',
                category='food',
                map_link='https://maps.google.com/guide1',
                in_guide_book=True,
                best_time_to_go='Evening',
                recommended_meal='Dinner'
            ),
            RecommendationBlock(
                property_id=property.id,
                title='Regular Restaurant',
                description='Not in guide book',
                category='food',
                map_link='https://maps.google.com/regular',
                in_guide_book=False
            ),
            RecommendationBlock(
                property_id=property.id,
                title='Guide Park',
                description='In guide book',
                category='outdoors',
                map_link='https://maps.google.com/guide2',
                in_guide_book=True,
                best_time_to_go='Morning'
            )
        ]
        
        for rec in recommendations:
            db.session.add(rec)
        db.session.commit()
        
        # Log in as owner
        client.post('/auth/login', data={
            'email': 'owner@test.com',
            'password': 'password'
        }, follow_redirects=True)
        
        return {'owner': owner, 'property': property, 'recommendations': recommendations}

def test_guide_book_filter(client, setup_data):
    """Test filtering recommendations to show only guide book entries"""
    property = setup_data['property']
    
    # Get recommendations with guide book filter
    response = client.get(f'/recommendations/property/{property.id}/list?in_guide_book=true')
    assert response.status_code == 200
    
    # Should show guide book recommendations
    assert b'Guide Restaurant 1' in response.data
    assert b'Guide Park' in response.data
    # Should not show non-guide book recommendations
    assert b'Regular Restaurant' not in response.data

def test_guide_book_toggle(client, setup_data):
    """Test toggling a recommendation in/out of the guide book"""
    property = setup_data['property']
    recommendations = setup_data['recommendations']
    regular_rec = next(r for r in recommendations if r.title == 'Regular Restaurant')
    
    # Add to guide book
    response = client.post(f'/recommendations/{regular_rec.id}/edit', data={
        'title': regular_rec.title,
        'description': regular_rec.description,
        'category': regular_rec.category,
        'map_link': regular_rec.map_link,
        'add_to_guide': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Recommendation updated successfully!' in response.data
    
    # Verify it's now in guide book
    updated_rec = RecommendationBlock.query.get(regular_rec.id)
    assert updated_rec.in_guide_book is True
    
    # Remove from guide book
    response = client.post(f'/recommendations/{regular_rec.id}/edit', data={
        'title': regular_rec.title,
        'description': regular_rec.description,
        'category': regular_rec.category,
        'map_link': regular_rec.map_link,
        'add_to_guide': False
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Verify it's no longer in guide book
    updated_rec = RecommendationBlock.query.get(regular_rec.id)
    assert updated_rec.in_guide_book is False

def test_guide_book_categories(client, setup_data):
    """Test filtering guide book recommendations by category"""
    property = setup_data['property']
    
    # Filter for food category in guide book
    response = client.get(f'/recommendations/property/{property.id}/list?category=food&in_guide_book=true')
    assert response.status_code == 200
    
    # Should show food recommendations in guide book
    assert b'Guide Restaurant 1' in response.data
    # Should not show other categories or non-guide book items
    assert b'Guide Park' not in response.data
    assert b'Regular Restaurant' not in response.data
    
    # Filter for outdoors category in guide book
    response = client.get(f'/recommendations/property/{property.id}/list?category=outdoors&in_guide_book=true')
    assert response.status_code == 200
    
    # Should show outdoors recommendations in guide book
    assert b'Guide Park' in response.data
    # Should not show other categories
    assert b'Guide Restaurant 1' not in response.data

def test_guide_book_search(client, setup_data):
    """Test searching within guide book recommendations"""
    property = setup_data['property']
    
    # Search for 'Restaurant' within guide book
    response = client.get(f'/recommendations/property/{property.id}/list?search=Restaurant&in_guide_book=true')
    assert response.status_code == 200
    
    # Should show matching guide book recommendations
    assert b'Guide Restaurant 1' in response.data
    # Should not show non-matching or non-guide book items
    assert b'Guide Park' not in response.data
    assert b'Regular Restaurant' not in response.data

def test_bulk_guide_book_update(client, setup_data):
    """Test adding/removing multiple recommendations to/from guide book"""
    property = setup_data['property']
    recommendations = setup_data['recommendations']
    
    # Get IDs of all recommendations
    rec_ids = [r.id for r in recommendations]
    
    # Add all to guide book
    response = client.post(f'/recommendations/property/{property.id}/bulk_guide_update', data={
        'recommendation_ids': rec_ids,
        'add_to_guide': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify all are in guide book
    for rec_id in rec_ids:
        rec = RecommendationBlock.query.get(rec_id)
        assert rec.in_guide_book is True
    
    # Remove all from guide book
    response = client.post(f'/recommendations/property/{property.id}/bulk_guide_update', data={
        'recommendation_ids': rec_ids,
        'add_to_guide': False
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify none are in guide book
    for rec_id in rec_ids:
        rec = RecommendationBlock.query.get(rec_id)
        assert rec.in_guide_book is False 