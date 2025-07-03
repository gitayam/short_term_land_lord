import pytest
from flask import url_for
from app.models import Property, PropertyCalendar
from datetime import datetime, timedelta, date

def test_property_calendar_access(client, users, property_fixture):
    """Test access to property calendar"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # User should be able to access their own property calendar
    response = client.get(f'/property/{property_fixture.id}/calendar')
    assert response.status_code == 200
    # Check for the word 'Calendar' which is present in the template
    assert 'Calendar' in response.data.decode('utf-8')

def test_availability_calendar_access(client, users):
    """Test access to availability calendar"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # User should be able to access the combined calendar
    response = client.get('/combined-calendar')
    assert response.status_code == 200
    # Check for the calendar container which is present in the template
    assert 'calendar-container' in response.data.decode('utf-8')

def test_availability_calendar_mock_data(client, users):
    """Test availability calendar with mock data"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # Access combined calendar with mock data
    response = client.get('/combined-calendar?mock=true')
    assert response.status_code == 200
    # Check for the calendar container which is present in the template
    assert 'calendar-container' in response.data.decode('utf-8')

def test_property_tasks_api(client, users, property_fixture):
    """Test property tasks API endpoint"""
    client.post('/auth/login', data={'email': users['owner'].email, 'password': 'password'}, follow_redirects=True)
    
    # User should be able to access the property tasks
    response = client.get(f'/tasks/property/{property_fixture.id}')
    assert response.status_code == 200
    # Response should be HTML for task views
    assert 'text/html' in response.content_type
    # Check for task-related content in the response
    assert 'Tasks' in response.data.decode('utf-8') 