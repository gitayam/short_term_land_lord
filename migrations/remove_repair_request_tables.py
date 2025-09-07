"""Remove repair request tables and ensure tasks have necessary fields

This migration removes the repair_request and repair_request_media tables since repair requests
will now just be tasks with a repair_request tag.
"""

from flask import current_app
import sqlalchemy as sa
from alembic import op

def upgrade():
    """Remove repair request tables and ensure tasks have necessary fields."""
    current_app.logger.info("Starting repair request tables removal")
    
    # Connect to the database
    from app import db
    engine = db.engine
    
    with engine.begin() as conn:
        # First, ensure task table has all necessary fields
        inspector = sa.inspect(engine)
        task_columns = [c['name'] for c in inspector.get_columns('task')]
        
        # Add location field if it doesn't exist
        if 'location' not in task_columns:
            conn.execute(sa.text(
                "ALTER TABLE task ADD COLUMN location VARCHAR(255)"
            ))
        
        # Add severity field if it doesn't exist
        if 'severity' not in task_columns:
            conn.execute(sa.text(
                "ALTER TABLE task ADD COLUMN severity VARCHAR(50)"
            ))
        
        # Ensure tags field exists
        if 'tags' not in task_columns:
            conn.execute(sa.text(
                "ALTER TABLE task ADD COLUMN tags TEXT"
            ))
        
        # Now migrate any existing repair requests to tasks
        conn.execute(sa.text("""
            UPDATE task 
            SET tags = CASE 
                WHEN tags IS NULL THEN 'repair_request'
                WHEN tags NOT LIKE '%repair_request%' THEN CONCAT(tags, ',repair_request')
                ELSE tags
            END,
            location = r.location,
            severity = r.severity::text
            FROM repair_request r
            WHERE task.id = r.task_id
        """))
        
        # Drop the repair request media table first (due to foreign key)
        conn.execute(sa.text("DROP TABLE IF EXISTS repair_request_media"))
        
        # Drop the repair request table
        conn.execute(sa.text("DROP TABLE IF EXISTS repair_request"))
        
        # Drop the enums if they exist
        conn.execute(sa.text("""
            DO $$ BEGIN
                DROP TYPE IF EXISTS repairrequeststatus;
                DROP TYPE IF EXISTS repairrequestseverity;
            EXCEPTION WHEN others THEN END $$;
        """))
    
    current_app.logger.info("Repair request tables removal completed successfully")

def downgrade():
    """Downgrade is not supported as data would be lost."""
    pass 