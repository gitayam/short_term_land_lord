"""add recommendation votes

Revision ID: add_recommendation_votes
Revises: None
Create Date: 2024-03-21 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_recommendation_votes'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add staff_pick column to recommendation_blocks
    op.add_column('recommendation_blocks', sa.Column('staff_pick', sa.Boolean(), nullable=False, server_default='0'))
    
    # Create recommendation_votes table
    op.create_table('recommendation_votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recommendation_id', sa.Integer(), nullable=False),
        sa.Column('guest_token', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation_blocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index for faster lookups
    op.create_index('idx_recommendation_votes_recommendation_id', 'recommendation_votes', ['recommendation_id'])
    op.create_index('idx_recommendation_votes_guest_token', 'recommendation_votes', ['guest_token'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_recommendation_votes_recommendation_id', 'recommendation_votes')
    op.drop_index('idx_recommendation_votes_guest_token', 'recommendation_votes')
    
    # Drop recommendation_votes table
    op.drop_table('recommendation_votes')
    
    # Remove staff_pick column
    op.drop_column('recommendation_blocks', 'staff_pick') 