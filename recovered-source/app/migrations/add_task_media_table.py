"""
Migration script to add the task_media table for TaskMedia model.
"""
from flask import current_app
import sqlalchemy as sa
from alembic import op

def upgrade():
    current_app.logger.info("Creating task_media table")
    op.create_table(
        'task_media',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('task_id', sa.Integer, sa.ForeignKey('task.id'), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('media_type', sa.Enum('photo', 'video', name='mediatype'), nullable=False),
        sa.Column('storage_backend', sa.Enum('local', 's3', 'rclone', name='storagebackend'), nullable=False, server_default='local'),
        sa.Column('original_filename', sa.String(255), nullable=True),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('uploaded_by', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )

def downgrade():
    current_app.logger.info("Dropping task_media table")
    op.drop_table('task_media') 