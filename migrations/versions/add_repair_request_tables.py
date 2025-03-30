"""Add repair request tables

Revision ID: add_repair_request_tables
Revises: fd582bab23f5
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_repair_request_tables'
down_revision = 'fd582bab23f5'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    repair_request_status = postgresql.ENUM('pending', 'approved', 'rejected', 'converted_to_task', name='repairrequeststatus')
    repair_request_status.create(op.get_bind())
    
    repair_request_severity = postgresql.ENUM('low', 'medium', 'high', 'urgent', name='repairrequestseverity')
    repair_request_severity.create(op.get_bind())
    
    # Add REPAIR_REQUEST to notification_type enum
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'repair_request'")
    
    # Create repair_request table
    op.create_table('repair_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('reporter_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'urgent', name='repairrequestseverity'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'converted_to_task', name='repairrequeststatus'), nullable=False),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['property.id'], ),
        sa.ForeignKeyConstraint(['reporter_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create repair_request_media table
    op.create_table('repair_request_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repair_request_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('storage_backend', sa.Enum('local', 's3', 'rclone', name='storagebackend'), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['repair_request_id'], ['repair_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_repair_request_property_id'), 'repair_request', ['property_id'], unique=False)
    op.create_index(op.f('ix_repair_request_reporter_id'), 'repair_request', ['reporter_id'], unique=False)
    op.create_index(op.f('ix_repair_request_status'), 'repair_request', ['status'], unique=False)
    op.create_index(op.f('ix_repair_request_severity'), 'repair_request', ['severity'], unique=False)


def downgrade():
    # Drop tables
    op.drop_table('repair_request_media')
    op.drop_table('repair_request')
    
    # Drop enum types
    op.execute("DROP TYPE repairrequeststatus")
    op.execute("DROP TYPE repairrequestseverity")
