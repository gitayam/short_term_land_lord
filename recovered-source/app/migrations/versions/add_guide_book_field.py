"""Add guide book field to recommendations

Revision ID: add_guide_book_field
Create Date: 2024-03-24 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_guide_book_field'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add in_guide_book column to recommendation_blocks table
    op.add_column('recommendation_blocks',
        sa.Column('in_guide_book', sa.Boolean(), nullable=False, server_default='0')
    )

def downgrade():
    # Remove in_guide_book column from recommendation_blocks table
    op.drop_column('recommendation_blocks', 'in_guide_book') 