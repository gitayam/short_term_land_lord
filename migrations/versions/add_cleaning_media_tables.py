"""add cleaning media tables

Revision ID: 8a9b7c6d5e4f
Revises: c30ca987c580
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8a9b7c6d5e4f'
down_revision = 'c30ca987c580'
branch_labels = None
depends_on = None


def upgrade():
    # Create MediaType enum
    media_type = postgresql.ENUM('photo', 'video', name='mediatype')
    media_type.create(op.get_bind())
    
    # Create StorageBackend enum
    storage_backend = postgresql.ENUM('local', 's3', 'rclone', name='storagebackend')
    storage_backend.create(op.get_bind())
    
    # Create cleaning_media table
    op.create_table('cleaning_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cleaning_session_id', sa.Integer(), nullable=False),
        sa.Column('media_type', sa.Enum('photo', 'video', name='mediatype'), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('storage_backend', sa.Enum('local', 's3', 'rclone', name='storagebackend'), nullable=False, server_default='local'),
        sa.Column('is_start_video', sa.Boolean(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['cleaning_session_id'], ['cleaning_session.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cleaning_media_cleaning_session_id'), 'cleaning_media', ['cleaning_session_id'], unique=False)
    
    # Create issue_report table
    op.create_table('issue_report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cleaning_session_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['cleaning_session_id'], ['cleaning_session.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issue_report_cleaning_session_id'), 'issue_report', ['cleaning_session_id'], unique=False)
    
    # Create issue_media junction table
    op.create_table('issue_media',
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['issue_id'], ['issue_report.id'], ),
        sa.ForeignKeyConstraint(['media_id'], ['cleaning_media.id'], ),
        sa.PrimaryKeyConstraint('issue_id', 'media_id')
    )


def downgrade():
    # Drop tables
    op.drop_table('issue_media')
    op.drop_table('issue_report')
    op.drop_index(op.f('ix_cleaning_media_cleaning_session_id'), table_name='cleaning_media')
    op.drop_table('cleaning_media')
    
    # Drop enums
    op.execute('DROP TYPE storagebackend')
    op.execute('DROP TYPE mediatype')
