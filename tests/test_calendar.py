import pytest
from flask import url_for
from app.models import Property, PropertyCalendar
from datetime import datetime, timedelta, date

def test_property_calendar_access(client, users, property_fixture):
    """Test access to property calendar"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # User should be able to access their own property calendar
    response = client.get(url_for('calendar.property_calendar', property_id=property_fixture.id))
    assert response.status_code == 200
    assert f'Calendar - {property_fixture.name}' in response.data.decode('utf-8')

def test_availability_calendar_access(client, users):
    """Test access to availability calendar"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # User should be able to access the availability calendar
    response = client.get(url_for('calendar.availability_calendar'))
    assert response.status_code == 200
    assert 'Property Availability Calendar' in response.data.decode('utf-8')

def test_availability_calendar_mock_data(client, users):
    """Test availability calendar with mock data"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # Access calendar with mock data
    response = client.get(url_for('calendar.availability_calendar', mock='true'))
    assert response.status_code == 200
    assert 'Using mock data' in response.data.decode('utf-8')

def test_property_tasks_api(client, users, property_fixture):
    """Test property tasks API endpoint"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # User should be able to access the property tasks API
    response = client.get(url_for('calendar.property_tasks_api', property_id=property_fixture.id))
    assert response.status_code == 200
    # Response should be JSON
    assert response.content_type == 'application/json' 