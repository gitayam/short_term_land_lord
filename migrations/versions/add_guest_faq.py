"""add guest faq field to property model

Revision ID: b9c7e123456b
Revises: a9c7e123456a
Create Date: 2023-07-15 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9c7e123456b'
down_revision = 'a9c7e123456a'
branch_labels = None
depends_on = None


def upgrade():
    # Add guest_faq column to property table
    op.add_column('property', sa.Column('guest_faq', sa.Text(), nullable=True, 
                                       comment='Frequently asked questions and answers for guests'))


def downgrade():
    # Remove guest_faq column from property table
    op.drop_column('property', 'guest_faq') 