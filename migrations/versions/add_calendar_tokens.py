"""add calendar tokens

Revision ID: add_calendar_tokens  
Revises: add_user_profile_fields
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_calendar_tokens'
down_revision = 'add_user_profile_fields'
branch_labels = None
depends_on = None

def upgrade():
    """Add worker calendar token and booking calendar fields to property table"""
    
    # Add worker calendar token field
    op.add_column('property', sa.Column('worker_calendar_token', sa.String(64), nullable=True))
    
    # Add booking calendar fields
    op.add_column('property', sa.Column('booking_calendar_token', sa.String(64), nullable=True))
    op.add_column('property', sa.Column('booking_calendar_enabled', sa.Boolean(), server_default='false'))
    
    # Create unique indexes for the token fields
    op.create_index('ix_property_worker_calendar_token', 'property', ['worker_calendar_token'], unique=True)
    op.create_index('ix_property_booking_calendar_token', 'property', ['booking_calendar_token'], unique=True)

def downgrade():
    """Remove calendar token fields"""
    
    # Drop indexes first
    op.drop_index('ix_property_booking_calendar_token', table_name='property')
    op.drop_index('ix_property_worker_calendar_token', table_name='property')
    
    # Drop columns
    op.drop_column('property', 'booking_calendar_enabled')
    op.drop_column('property', 'booking_calendar_token')
    op.drop_column('property', 'worker_calendar_token')