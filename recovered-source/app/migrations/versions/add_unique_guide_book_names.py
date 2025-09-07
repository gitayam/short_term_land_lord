"""add unique guide book names per property

Revision ID: add_unique_guide_book_names
Revises: add_multiple_guide_books
Create Date: 2024-04-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_unique_guide_book_names'
down_revision = 'add_multiple_guide_books'
branch_labels = None
depends_on = None

def upgrade():
    # Create a unique constraint for guide book names within a property
    op.create_unique_constraint(
        'uq_guide_books_property_id_name',
        'guide_books',
        ['property_id', 'name']
    )

def downgrade():
    # Remove the unique constraint
    op.drop_constraint(
        'uq_guide_books_property_id_name',
        'guide_books',
        type_='unique'
    ) 