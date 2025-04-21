import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskAssignment, TaskStatus,
                       TaskPriority, TaskProperty, Property)
from config import TestConfig


class TestTaskModelUpdate(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app(TestConfig)  # Use TestConfig for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test user
        self.user = User(
            first_name='Test',
            last_name='User',
            email='user@example.com',
            role=UserRoles.PROPERTY_OWNER.value
        )

        db.session.add(self.user)
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
            owner_id=self.user.id
        )

        db.session.add(self.property)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_task_assign_to_next_cleaner(self):
        """Test the assign_to_next_cleaner field"""
        # Create a task with assign_to_next_cleaner set to True
        task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.user.id,
            property_id=self.property.id,
            assign_to_next_cleaner=True
        )

        db.session.add(task)
        db.session.commit()

        # Retrieve the task and check the field
        retrieved_task = Task.query.get(task.id)
        self.assertTrue(retrieved_task.assign_to_next_cleaner)

    def test_mark_completed(self):
        """Test the mark_completed method"""
        # Create a task
        task = Task(
            title='Test Completion',
            description='A task to test completion',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            creator_id=self.user.id,
            property_id=self.property.id
        )

        db.session.add(task)
        db.session.commit()

        # Mark as completed
        task.mark_completed(self.user.id)
        db.session.commit()

        # Retrieve the task and check its status and completed_at field
        retrieved_task = Task.query.get(task.id)
        self.assertEqual(retrieved_task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(retrieved_task.completed_at)

    def test_is_overdue(self):
        """Test the is_overdue method"""
        # Create a task with due date in the past
        past_due = Task(
            title='Past Due Task',
            description='A task that is past due',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            due_date=datetime.utcnow() - timedelta(days=1),
            creator_id=self.user.id,
            property_id=self.property.id
        )

        # Create a task with due date in the future
        future_due = Task(
            title='Future Due Task',
            description='A task that is due in the future',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            due_date=datetime.utcnow() + timedelta(days=1),
            creator_id=self.user.id,
            property_id=self.property.id
        )

        db.session.add(past_due)
        db.session.add(future_due)
        db.session.commit()

        # Test is_overdue method
        self.assertTrue(past_due.is_overdue())
        self.assertFalse(future_due.is_overdue())

    def test_display_methods(self):
        """Test the get_status_display and get_priority_display methods"""
        task = Task(
            title='Test Display',
            description='A task to test display methods',
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            creator_id=self.user.id,
            property_id=self.property.id
        )

        # Test the display methods
        self.assertEqual(task.get_status_display(), "In Progress")
        self.assertEqual(task.get_priority_display(), "High")


if __name__ == '__main__':
    unittest.main()