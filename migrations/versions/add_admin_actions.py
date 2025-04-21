"""add admin actions

Revision ID: add_admin_actions
Revises: None
Create Date: 2025-04-21 04:07:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_admin_actions'
down_revision = None

def upgrade():
    # Add is_suspended column to users table
    op.add_column('users', sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='0'))
    
    # Create admin_actions table
    op.create_table('admin_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('action_details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_admin_actions_admin_id'), 'admin_actions', ['admin_id'], unique=False)
    op.create_index(op.f('ix_admin_actions_target_user_id'), 'admin_actions', ['target_user_id'], unique=False)
    op.create_index(op.f('ix_admin_actions_created_at'), 'admin_actions', ['created_at'], unique=False)

def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_admin_actions_created_at'), table_name='admin_actions')
    op.drop_index(op.f('ix_admin_actions_target_user_id'), table_name='admin_actions')
    op.drop_index(op.f('ix_admin_actions_admin_id'), table_name='admin_actions')
    
    # Drop admin_actions table
    op.drop_table('admin_actions')
    
    # Drop is_suspended column from users table
    op.drop_column('users', 'is_suspended') 