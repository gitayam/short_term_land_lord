"""Add missing fields to repair_request table

This migration adds 'location', 'severity', 'additional_notes', and 'task_id' columns
to the repair_request table, and updates the status column to use the enum type.
"""

from flask import current_app
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum
import sqlalchemy as sa
from app.models import RepairRequestStatus, RepairRequestSeverity

def upgrade():
    """Add missing columns to repair_request table."""
    current_app.logger.info("Starting repair_request table upgrade")
    
    # Connect to the database
    from app import db
    engine = db.engine
    
    # Check if columns already exist (to avoid errors)
    inspector = sa.inspect(engine)
    existing_columns = [c['name'] for c in inspector.get_columns('repair_request')]
    
    with engine.begin() as conn:
        # Add location column if it doesn't exist
        if 'location' not in existing_columns:
            current_app.logger.info("Adding location column to repair_request table")
            conn.execute(sa.text(
                "ALTER TABLE repair_request ADD COLUMN location VARCHAR(255)"
            ))
        
        # Add severity column if it doesn't exist
        if 'severity' not in existing_columns:
            current_app.logger.info("Adding severity column to repair_request table")
            # Create the enum type if it doesn't exist
            conn.execute(sa.text(
                "DO $$ BEGIN "
                "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'repairrequestseverity') THEN "
                "CREATE TYPE repairrequestseverity AS ENUM ('low_severity', 'medium_severity', 'high_severity', 'urgent_severity'); "
                "END IF; "
                "END $$;"
            ))
            # Add the column
            conn.execute(sa.text(
                "ALTER TABLE repair_request ADD COLUMN severity repairrequestseverity DEFAULT 'medium_severity'"
            ))
        
        # Add additional_notes column if it doesn't exist
        if 'additional_notes' not in existing_columns:
            current_app.logger.info("Adding additional_notes column to repair_request table")
            conn.execute(sa.text(
                "ALTER TABLE repair_request ADD COLUMN additional_notes TEXT"
            ))
        
        # Add task_id column if it doesn't exist
        if 'task_id' not in existing_columns:
            current_app.logger.info("Adding task_id column to repair_request table")
            conn.execute(sa.text(
                "ALTER TABLE repair_request ADD COLUMN task_id INTEGER REFERENCES task(id)"
            ))
        
        # Update status column to use enum type
        if 'status' in existing_columns:
            current_app.logger.info("Updating status column in repair_request table")
            # Create the enum type if it doesn't exist
            conn.execute(sa.text(
                "DO $$ BEGIN "
                "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'repairrequeststatus') THEN "
                "CREATE TYPE repairrequeststatus AS ENUM ('pending_status', 'approved_status', 'rejected_status', 'converted_to_task_status'); "
                "END IF; "
                "END $$;"
            ))
            
            # Create a temporary column with the new enum type
            conn.execute(sa.text(
                "ALTER TABLE repair_request ADD COLUMN status_new repairrequeststatus"
            ))
            
            # Migrate data from old to new column
            conn.execute(sa.text(
                "UPDATE repair_request SET status_new = CASE "
                "WHEN status = 'pending' THEN 'pending_status'::repairrequeststatus "
                "WHEN status = 'in_progress' THEN 'approved_status'::repairrequeststatus "
                "WHEN status = 'completed' THEN 'converted_to_task_status'::repairrequeststatus "
                "WHEN status = 'cancelled' THEN 'rejected_status'::repairrequeststatus "
                "ELSE 'pending_status'::repairrequeststatus END"
            ))
            
            # Drop the old column and rename the new one
            conn.execute(sa.text("ALTER TABLE repair_request DROP COLUMN status"))
            conn.execute(sa.text("ALTER TABLE repair_request RENAME COLUMN status_new TO status"))
            
    current_app.logger.info("Repair_request table upgrade completed successfully")

def downgrade():
    """Downgrade is not supported, as data might be lost."""
    pass 