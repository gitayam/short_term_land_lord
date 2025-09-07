"""add guide book token

Revision ID: add_guide_book_token
Revises: add_wifi_and_parking
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_guide_book_token'
down_revision = 'add_wifi_and_parking'
branch_labels = None
depends_on = None

def upgrade():
    # Add guide_book_token column
    op.add_column('properties', sa.Column('guide_book_token', sa.String(64), unique=True))

def downgrade():
    # Remove guide_book_token column
    op.drop_column('properties', 'guide_book_token') 