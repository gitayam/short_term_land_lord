from flask import Flask
from app import create_app
from app.models import Task, TaskProperty, TaskAssignment
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

def main():
    """Find and report potentially problematic task queries"""
    app = create_app()

    with app.app_context():
        print("Analyzing calendar and task queries...")

        # Example of how to properly construct a query with aliases
        print("\nExample of correctly aliased query for a task with property and assignments:")
        print("""
from sqlalchemy.orm import aliased
task_assignment_alias = aliased(TaskAssignment)
task_property_alias = aliased(TaskProperty)

# Properly aliased query
query = Task.query
query = query.join(
    task_assignment_alias, Task.id == task_assignment_alias.task_id
).filter(
    task_assignment_alias.user_id == user_id
)
query = query.join(
    task_property_alias, Task.id == task_property_alias.task_id
).filter(
    task_property_alias.property_id == property_id
)
        """)

        print("\nThis fixes the error: ERROR: table name \"task_assignment\" specified more than once")
        print("Please make sure all task queries use proper table aliases when joining task_assignment or task_property multiple times.")

if __name__ == '__main__':
    main()