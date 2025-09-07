#!/usr/bin/env python3
"""
This script adds the tags column to the task table to support workorders functionality.
The tags column is a comma-separated string that can include 'workorder' and other tags.
"""

import os
import sys
import logging
from sqlalchemy import text, inspect, Column, String
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import db, create_app
from app.models import Task

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_tags_column():
    """Add the tags column to the task table if it doesn't exist."""
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('task')]
        
        if 'tags' not in columns:
            logger.info("Adding 'tags' column to task table")
            
            # For SQLite (development)
            if db.engine.url.drivername.startswith('sqlite'):
                db.session.execute(text("""
                    ALTER TABLE task ADD COLUMN tags VARCHAR(255);
                """))
            # For PostgreSQL (production)
            else:
                db.session.execute(text("""
                    ALTER TABLE task ADD COLUMN IF NOT EXISTS tags VARCHAR(255);
                """))
                
            db.session.commit()
            logger.info("Successfully added 'tags' column to task table")
        else:
            logger.info("'tags' column already exists in task table")

def mark_existing_workorders():
    """Identify existing tasks that are likely workorders and tag them."""
    app = create_app()
    with app.app_context():
        # Get tasks that likely represent workorders based on title or description
        workorder_keywords = ['repair', 'fix', 'replace', 'install', 'maintenance', 'broken', 'leaking']
        
        # Build query to find tasks with workorder-like keywords
        tasks_to_update = []
        for task in Task.query.all():
            title_lower = task.title.lower() if task.title else ""
            desc_lower = task.description.lower() if task.description else ""
            
            is_workorder = any(keyword in title_lower or keyword in desc_lower for keyword in workorder_keywords)
            
            if is_workorder and not task.tags:
                tasks_to_update.append(task.id)
        
        # Update tasks with workorder tag
        if tasks_to_update:
            count = 0
            for task_id in tasks_to_update:
                task = Task.query.get(task_id)
                if task:
                    task.tags = "workorder"
                    count += 1
                    
                    # Commit in smaller batches to avoid long transactions
                    if count % 50 == 0:
                        db.session.commit()
            
            # Final commit for any remaining changes
            db.session.commit()
            logger.info(f"Tagged {count} existing tasks as workorders")
        else:
            logger.info("No existing tasks identified as workorders")

if __name__ == "__main__":
    logger.info("Starting task tags column migration")
    try:
        add_tags_column()
        mark_existing_workorders()
        logger.info("Task tags column migration completed successfully")
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        sys.exit(1) 