import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (User, UserRoles, Task, TaskAssignment, TaskStatus, 
                       TaskPriority, TaskProperty, Property, RecurrencePattern)
from app.tasks.routes import (can_view_task, can_edit_task, can_delete_task, 
                            can_complete_task, assign_tasks_to_next_cleaner)
from config import TestConfig


class TestTaskServiceFunctions(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app(TestConfig)  # Use TestConfig for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test users
        self.owner = User(
            first_name='Test',
            last_name='Owner',
            email='owner@example.com',
            role=UserRoles.PROPERTY_OWNER
        )
        
        self.staff = User(
            first_name='Test',
            last_name='Staff',
            email='staff@example.com',
            role=UserRoles.SERVICE_STAFF
        )
        
        self.other_owner = User(
            first_name='Other',
            last_name='Owner',
            email='other_owner@example.com',
            role=UserRoles.PROPERTY_OWNER
        )
        
        self.other_staff = User(
            first_name='Other',
            last_name='Staff',
            email='other_staff@example.com',
            role=UserRoles.SERVICE_STAFF
        )
        
        db.session.add_all([self.owner, self.staff, self.other_owner, self.other_staff])
        db.session.commit()
        
        # Create properties
        self.property = Property(
            name='Test Property',
            description='A test property',
            street_address='123 Test St',
            city='Test City',
            state='Test State',
            zip_code='12345',
            country='Test Country',
            owner_id=self.owner.id
        )
        
        self.other_property = Property(
            name='Other Property',
            description='Another test property',
            street_address='456 Other St',
            city='Other City',
            state='Other State',
            zip_code='67890',
            country='Other Country',
            owner_id=self.other_owner.id
        )
        
        db.session.add_all([self.property, self.other_property])
        db.session.commit()
        
        # Create a basic task
        self.task = Task(
            title='Test Task',
            description='A test task',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            is_recurring=False,
            recurrence_pattern=RecurrencePattern.NONE,
            creator_id=self.owner.id
        )
        db.session.add(self.task)
        
        # Link task to property
        self.task_property = TaskProperty(
            task=self.task,
            property=self.property
        )
        db.session.add(self.task_property)
        
        # Create assignment for the staff
        self.assignment = TaskAssignment(
            task=self.task,
            user_id=self.staff.id
        )
        db.session.add(self.assignment)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_can_view_task(self):
        """Test the can_view_task function."""
        # Creator can view
        self.assertTrue(can_view_task(self.task, self.owner))
        
        # Assigned staff can view
        self.assertTrue(can_view_task(self.task, self.staff))
        
        # Property owner can view tasks for their properties
        # Since we're testing the function directly, need to create a task for the other owner's property
        other_task = Task(
            title='Other Task',
            description='Another test task',
            creator_id=self.other_owner.id
        )
        db.session.add(other_task)
        
        other_task_property = TaskProperty(
            task=other_task,
            property=self.other_property
        )
        db.session.add(other_task_property)
        db.session.commit()
        
        # Other owner can view their task
        self.assertTrue(can_view_task(other_task, self.other_owner))
        
        # Owner cannot view other owner's task
        self.assertFalse(can_view_task(other_task, self.owner))
        
        # Unassigned staff cannot view
        self.assertFalse(can_view_task(other_task, self.other_staff))
    
    def test_can_edit_task(self):
        """Test the can_edit_task function."""
        # Creator can edit
        self.assertTrue(can_edit_task(self.task, self.owner))
        
        # Property owner can edit tasks for their properties
        # Create a task by staff but for owner's property
        staff_created_task = Task(
            title='Staff Created Task',
            description='A task created by staff for owner property',
            creator_id=self.staff.id
        )
        db.session.add(staff_created_task)
        
        staff_task_property = TaskProperty(
            task=staff_created_task,
            property=self.property  # Owner's property
        )
        db.session.add(staff_task_property)
        db.session.commit()
        
        # Owner can edit tasks for their property even if not creator
        self.assertTrue(can_edit_task(staff_created_task, self.owner))
        
        # Assigned staff cannot edit (unless they are the creator)
        self.assertFalse(can_edit_task(self.task, self.staff))
        
        # Staff can edit task they created
        self.assertTrue(can_edit_task(staff_created_task, self.staff))
        
        # Other owner cannot edit
        self.assertFalse(can_edit_task(self.task, self.other_owner))
    
    def test_can_delete_task(self):
        """Test the can_delete_task function."""
        # Creator can delete
        self.assertTrue(can_delete_task(self.task, self.owner))
        
        # Non-creator cannot delete, even if property owner
        staff_created_task = Task(
            title='Staff Created Task',
            description='A task created by staff',
            creator_id=self.staff.id
        )
        db.session.add(staff_created_task)
        
        staff_task_property = TaskProperty(
            task=staff_created_task,
            property=self.property  # Owner's property
        )
        db.session.add(staff_task_property)
        db.session.commit()
        
        # Owner cannot delete staff-created task
        self.assertFalse(can_delete_task(staff_created_task, self.owner))
        
        # Staff cannot delete owner-created task
        self.assertFalse(can_delete_task(self.task, self.staff))
        
        # Staff can delete task they created
        self.assertTrue(can_delete_task(staff_created_task, self.staff))
    
    def test_can_complete_task(self):
        """Test the can_complete_task function."""
        # Creator can complete
        self.assertTrue(can_complete_task(self.task, self.owner))
        
        # Assigned staff can complete
        self.assertTrue(can_complete_task(self.task, self.staff))
        
        # Unassigned staff cannot complete
        self.assertFalse(can_complete_task(self.task, self.other_staff))
        
        # Other owner cannot complete
        self.assertFalse(can_complete_task(self.task, self.other_owner))
    
    def test_assign_tasks_to_next_cleaner(self):
        """Test the assign_tasks_to_next_cleaner function."""
        # Create tasks marked for next cleaner
        next_cleaner_task1 = Task(
            title='Next Cleaner Task 1',
            description='A task for the next cleaner',
            status=TaskStatus.PENDING,
            creator_id=self.owner.id,
            assign_to_next_cleaner=True
        )
        db.session.add(next_cleaner_task1)
        
        next_cleaner_task1_property = TaskProperty(
            task=next_cleaner_task1,
            property=self.property
        )
        db.session.add(next_cleaner_task1_property)
        
        next_cleaner_task2 = Task(
            title='Next Cleaner Task 2',
            description='Another task for the next cleaner',
            status=TaskStatus.PENDING,
            creator_id=self.owner.id,
            assign_to_next_cleaner=True
        )
        db.session.add(next_cleaner_task2)
        
        next_cleaner_task2_property = TaskProperty(
            task=next_cleaner_task2,
            property=self.property
        )
        db.session.add(next_cleaner_task2_property)
        
        # Create a task that's already completed
        completed_task = Task(
            title='Completed Task',
            description='A completed task for the next cleaner',
            status=TaskStatus.COMPLETED,
            creator_id=self.owner.id,
            assign_to_next_cleaner=True
        )
        db.session.add(completed_task)
        
        completed_task_property = TaskProperty(
            task=completed_task,
            property=self.property
        )
        db.session.add(completed_task_property)
        
        db.session.commit()
        
        # Run the function to assign tasks
        assigned_count = assign_tasks_to_next_cleaner(self.property.id, self.other_staff.id)
        
        # Should assign 2 tasks (not the completed one)
        self.assertEqual(assigned_count, 2)
        
        # Verify assignments were created
        assignments = TaskAssignment.query.filter_by(user_id=self.other_staff.id).all()
        self.assertEqual(len(assignments), 2)
        
        # Verify the right tasks were assigned
        assigned_task_ids = [a.task_id for a in assignments]
        self.assertIn(next_cleaner_task1.id, assigned_task_ids)
        self.assertIn(next_cleaner_task2.id, assigned_task_ids)
        self.assertNotIn(completed_task.id, assigned_task_ids)
        
        # Running again should not create duplicate assignments
        new_assigned_count = assign_tasks_to_next_cleaner(self.property.id, self.other_staff.id)
        self.assertEqual(new_assigned_count, 2)  # Returns count of all tasks, not newly assigned
        
        new_assignments = TaskAssignment.query.filter_by(user_id=self.other_staff.id).all()
        self.assertEqual(len(new_assignments), 2)  # Still just 2 assignments


if __name__ == '__main__':
    unittest.main() 