import pytest
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskAssignment, TaskStatus,
                      TaskPriority, TaskProperty, Property, RecurrencePattern,
                      ServiceType)
from flask import url_for
from app.tasks.routes import can_view_task, can_edit_task, can_delete_task, can_complete_task
from config import TestConfig


@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(TestConfig)  # Use TestConfig for testing

    # Disable CSRF protection for testing
    app.config['WTF_CSRF_ENABLED'] = False

    # Create context
    with app.app_context():
        db.create_all()
        yield app  # Return app to the test
        db.drop_all()  # Clean up after the test


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client(use_cookies=True)


@pytest.fixture(scope='function')
def _db(app):
    """Provide the database for testing."""
    return db


@pytest.fixture(scope='function')
def users(app, _db):
    """Create test users for various roles."""
    owner = User(
        first_name='Test',
        last_name='Owner',
        email='owner@example.com',
        role=UserRoles.PROPERTY_OWNER.value
    )
    owner.set_password('password')

    staff = User(
        first_name='Test',
        last_name='Staff',
        email='staff@example.com',
        role=UserRoles.SERVICE_STAFF.value
    )
    staff.set_password('password')

    manager = User(
        first_name='Test',
        last_name='Manager',
        email='manager@example.com',
        role=UserRoles.PROPERTY_MANAGER.value
    )
    manager.set_password('password')

    admin = User(
        first_name='Test',
        last_name='Admin',
        email='admin@example.com',
        role=UserRoles.ADMIN.value
    )
    admin.set_password('password')

    _db.session.add_all([owner, staff, manager, admin])
    _db.session.commit()

    return {
        'owner': owner,
        'staff': staff,
        'manager': manager,
        'admin': admin
    }


@pytest.fixture(scope='function')
def property_fixture(app, _db, users):
    """Create a test property."""
    property = Property(
        name='Test Property',
        description='A test property',
        street_address='123 Test St',
        city='Test City',
        state='Test State',
        zip_code='12345',
        country='Test Country',
        address='123 Test St, Test City, Test State 12345, Test Country',
        owner_id=users['owner'].id
    )

    _db.session.add(property)
    _db.session.commit()

    return property


@pytest.fixture(scope='function')
def task_fixture(app, _db, users, property_fixture):
    """Create a test task with property association and staff assignment."""
    task = Task(
        title='Test Task',
        description='A test task',
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        is_recurring=False,
        recurrence_pattern=RecurrencePattern.NONE,
        creator_id=users['owner'].id
    )
    _db.session.add(task)
    _db.session.commit()

    task_property = TaskProperty(
        task_id=task.id,
        property_id=property_fixture.id
    )
    _db.session.add(task_property)

    assignment = TaskAssignment(
        task=task,
        user_id=users['staff'].id,
        service_type=ServiceType.CLEANING
    )
    _db.session.add(assignment)

    _db.session.commit()

    return task


@pytest.fixture(scope='function')
def authenticated_client(client, users):
    """Create an authenticated client session with the owner user."""
    client.post('/auth/login', data={
        'email': users['owner'].email,
        'password': 'password'
    }, follow_redirects=True)

    return client


@pytest.fixture(scope='function')
def staff_authenticated_client(client, users):
    """Create an authenticated client session with the staff user."""
    client.post('/auth/login', data={
        'email': users['staff'].email,
        'password': 'password'
    }, follow_redirects=True)

    return client