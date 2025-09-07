"""add guide books

Revision ID: add_guide_books
Revises: add_recommendation_votes
Create Date: 2024-03-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_guide_books'
down_revision = 'add_recommendation_votes'
branch_labels = None
depends_on = None


def upgrade():
    # Create guide_books table
    op.create_table('guide_books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create guide_book_recommendations association table
    op.create_table('guide_book_recommendations',
        sa.Column('guide_book_id', sa.Integer(), nullable=False),
        sa.Column('recommendation_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['guide_book_id'], ['guide_books.id'], ),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation_blocks.id'], ),
        sa.PrimaryKeyConstraint('guide_book_id', 'recommendation_id')
    )

    # Create indexes for faster lookups
    op.create_index(op.f('ix_guide_books_property_id'), 'guide_books', ['property_id'], unique=False)
    op.create_index(op.f('ix_guide_book_recommendations_recommendation_id'), 'guide_book_recommendations', ['recommendation_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_guide_book_recommendations_recommendation_id'), table_name='guide_book_recommendations')
    op.drop_index(op.f('ix_guide_books_property_id'), table_name='guide_books')
    
    # Drop tables
    op.drop_table('guide_book_recommendations')
    op.drop_table('guide_books') 