"""add guest access fields

Revision ID: add_guest_access_fields
Revises: add_repair_request_tables
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_guest_access_fields'
down_revision = 'add_repair_request_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add guest-specific fields to the property table
    op.add_column('property', sa.Column('guest_access_token', sa.String(64), nullable=True, unique=True))
    op.add_column('property', sa.Column('guest_rules', sa.Text(), nullable=True))
    op.add_column('property', sa.Column('guest_checkin_instructions', sa.Text(), nullable=True))
    op.add_column('property', sa.Column('guest_checkout_instructions', sa.Text(), nullable=True))
    op.add_column('property', sa.Column('guest_wifi_instructions', sa.Text(), nullable=True))
    op.add_column('property', sa.Column('local_attractions', sa.Text(), nullable=True))
    op.add_column('property', sa.Column('emergency_contact', sa.String(255), nullable=True))
    op.add_column('property', sa.Column('guest_access_enabled', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create an index on the guest_access_token for faster lookups
    op.create_index(op.f('ix_property_guest_access_token'), 'property', ['guest_access_token'], unique=True)


def downgrade():
    # Remove the guest-specific fields
    op.drop_index(op.f('ix_property_guest_access_token'), table_name='property')
    op.drop_column('property', 'guest_access_enabled')
    op.drop_column('property', 'emergency_contact')
    op.drop_column('property', 'local_attractions')
    op.drop_column('property', 'guest_wifi_instructions')
    op.drop_column('property', 'guest_checkout_instructions')
    op.drop_column('property', 'guest_checkin_instructions')
    op.drop_column('property', 'guest_rules')
    op.drop_column('property', 'guest_access_token')
