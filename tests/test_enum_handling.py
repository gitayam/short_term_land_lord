"""
Test suite for verifying proper enum handling throughout the application.
This ensures enums are used correctly with SQLAlchemy models.
"""

import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (
    Task, RepairRequest, User, Property, TaskProperty,
    TaskStatus, TaskPriority, RecurrencePattern, 
    RepairRequestStatus, RepairRequestSeverity, UserRoles
)


class TestEnumHandling:
    """Test proper enum usage in models and database operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, app, db_session):
        """Set up test fixtures."""
        self.app = app
        self.db = db_session
        
        # Create a test user
        self.user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role=UserRoles.ADMIN  # Using enum directly, not .value
        )
        self.user.set_password('password')
        db_session.add(self.user)
        
        # Create a test property
        self.property = Property(
            name='Test Property',
            address='123 Test St',
            owner_id=self.user.id
        )
        db_session.add(self.property)
        db_session.commit()
    
    def test_task_enum_creation(self, db_session):
        """Test creating a task with proper enum values."""
        task = Task(
            title='Test Task',
            description='Test Description',
            status=TaskStatus.PENDING,  # Should use enum, not .value
            priority=TaskPriority.HIGH,  # Should use enum, not .value
            recurrence_pattern=RecurrencePattern.NONE,  # Should use enum, not .value
            creator_id=self.user.id,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(task)
        db_session.commit()
        
        # Verify the task was created properly
        retrieved_task = Task.query.filter_by(title='Test Task').first()
        assert retrieved_task is not None
        assert retrieved_task.status == TaskStatus.PENDING
        assert retrieved_task.priority == TaskPriority.HIGH
        assert retrieved_task.recurrence_pattern == RecurrencePattern.NONE
    
    def test_task_enum_update(self, db_session):
        """Test updating task enum fields."""
        task = Task(
            title='Update Test',
            description='Test',
            status=TaskStatus.PENDING,
            priority=TaskPriority.LOW,
            creator_id=self.user.id
        )
        db_session.add(task)
        db_session.commit()
        
        # Update with enum values
        task.status = TaskStatus.IN_PROGRESS
        task.priority = TaskPriority.URGENT
        db_session.commit()
        
        # Verify updates
        updated_task = Task.query.get(task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.priority == TaskPriority.URGENT
    
    def test_repair_request_enum_creation(self, db_session):
        """Test creating a repair request with proper enum values."""
        repair = RepairRequest(
            title='Broken Faucet',
            description='Kitchen faucet is leaking',
            property_id=self.property.id,
            reporter_id=self.user.id,
            status=RepairRequestStatus.PENDING,  # Should use enum, not .value
            severity=RepairRequestSeverity.MEDIUM,  # Should use enum, not .value
            priority='high'  # This uses a different enum type
        )
        db_session.add(repair)
        db_session.commit()
        
        # Verify the repair request was created properly
        retrieved = RepairRequest.query.filter_by(title='Broken Faucet').first()
        assert retrieved is not None
        assert retrieved.status == RepairRequestStatus.PENDING
        assert retrieved.severity == RepairRequestSeverity.MEDIUM
    
    def test_enum_query_filtering(self, db_session):
        """Test querying with enum values."""
        # Create tasks with different statuses
        for status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]:
            task = Task(
                title=f'Task {status.name}',
                description='Test',
                status=status,
                priority=TaskPriority.MEDIUM,
                creator_id=self.user.id
            )
            db_session.add(task)
        db_session.commit()
        
        # Query using enum values
        pending_tasks = Task.query.filter_by(status=TaskStatus.PENDING).all()
        assert len(pending_tasks) == 1
        assert pending_tasks[0].title == 'Task PENDING'
        
        # Query using .in_() with enum values
        active_tasks = Task.query.filter(
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).all()
        assert len(active_tasks) == 2
    
    def test_invalid_enum_value_raises_error(self, db_session):
        """Test that using .value instead of enum raises appropriate error."""
        with pytest.raises(Exception) as exc_info:
            task = Task(
                title='Invalid Task',
                description='Test',
                status='pending',  # String value instead of enum - should fail
                priority=TaskPriority.LOW,
                creator_id=self.user.id
            )
            db_session.add(task)
            db_session.commit()
        
        # The error should indicate enum validation failure
        assert 'not among the defined enum values' in str(exc_info.value) or \
               'Invalid enum value' in str(exc_info.value) or \
               'is not a valid' in str(exc_info.value)
    
    def test_recurrence_pattern_none_handling(self, db_session):
        """Test that RecurrencePattern.NONE is handled correctly."""
        task = Task(
            title='Non-recurring Task',
            description='Test',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            is_recurring=False,
            recurrence_pattern=RecurrencePattern.NONE,  # Should work without .value
            creator_id=self.user.id
        )
        db_session.add(task)
        db_session.commit()
        
        retrieved = Task.query.filter_by(title='Non-recurring Task').first()
        assert retrieved is not None
        assert retrieved.recurrence_pattern == RecurrencePattern.NONE
        assert retrieved.is_recurring is False
    
    def test_repair_request_conversion_to_task(self, db_session):
        """Test converting repair request to task maintains proper enum values."""
        repair = RepairRequest(
            title='Fix Door',
            description='Door is stuck',
            property_id=self.property.id,
            reporter_id=self.user.id,
            status=RepairRequestStatus.APPROVED,
            severity=RepairRequestSeverity.HIGH,
            priority='urgent'
        )
        db_session.add(repair)
        db_session.commit()
        
        # Create task from repair request
        task = Task(
            title=repair.title,
            description=repair.description,
            status=TaskStatus.PENDING,  # New task should be pending
            priority=TaskPriority.URGENT,
            creator_id=self.user.id,
            tags='repair_request',
            recurrence_pattern=RecurrencePattern.NONE  # Repair tasks don't recur
        )
        
        # Add property relationship
        task_property = TaskProperty(
            task=task,
            property_id=repair.property_id
        )
        db_session.add(task)
        db_session.add(task_property)
        
        # Update repair request status
        repair.status = RepairRequestStatus.CONVERTED
        repair.task_id = task.id
        
        db_session.commit()
        
        # Verify conversions
        assert repair.status == RepairRequestStatus.CONVERTED
        assert task.recurrence_pattern == RecurrencePattern.NONE
        assert task.priority == TaskPriority.URGENT


@pytest.fixture(scope='module')
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def db_session(app):
    """Create a database session for testing."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Configure session
        db.session.configure(bind=connection)
        
        yield db.session
        
        # Rollback transaction
        transaction.rollback()
        connection.close()
        db.session.remove()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])