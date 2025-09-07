"""add guide book access token

Revision ID: add_guide_book_access_token
Revises: add_multiple_guide_books
Create Date: 2024-04-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_guide_book_access_token'
down_revision = 'add_multiple_guide_books'
branch_labels = None
depends_on = None

def upgrade():
    # Add access_token column to guide_books table
    op.add_column('guide_books', sa.Column('access_token', sa.String(64), nullable=True, unique=True))
    
    # Create index for faster lookups
    op.create_index('idx_guide_books_access_token', 'guide_books', ['access_token'])

    # Generate tokens for existing public guide books
    conn = op.get_bind()
    conn.execute("""
        UPDATE guide_books 
        SET access_token = substr(hex(randomblob(32)), 1, 64)
        WHERE is_public = 1 AND access_token IS NULL
    """)

def downgrade():
    # Remove index first
    op.drop_index('idx_guide_books_access_token', table_name='guide_books')
    # Then remove the column
    op.drop_column('guide_books', 'access_token') 