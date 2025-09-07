"""add multiple guide books

Revision ID: add_multiple_guide_books
Revises: add_recommendation_votes
Create Date: 2024-04-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_multiple_guide_books'
down_revision = 'add_recommendation_votes'
branch_labels = None
depends_on = None

def upgrade():
    # Create guide_books table
    op.create_table('guide_books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('access_token', sa.String(64), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['property_id'], ['property.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create guide_book_recommendations association table
    op.create_table('guide_book_recommendations',
        sa.Column('guide_book_id', sa.Integer(), nullable=False),
        sa.Column('recommendation_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['guide_book_id'], ['guide_books.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendation_blocks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('guide_book_id', 'recommendation_id')
    )
    
    # Create indexes
    op.create_index('idx_guide_books_property_id', 'guide_books', ['property_id'])
    op.create_index('idx_guide_books_access_token', 'guide_books', ['access_token'])
    op.create_index('idx_guide_book_recommendations_guide_book_id', 'guide_book_recommendations', ['guide_book_id'])
    op.create_index('idx_guide_book_recommendations_recommendation_id', 'guide_book_recommendations', ['recommendation_id'])
    
    # Create default guide book for each property and migrate existing in_guide_book recommendations
    conn = op.get_bind()
    
    # Get all properties
    properties = conn.execute('SELECT id FROM property').fetchall()
    
    for property_id in properties:
        # Create default guide book
        conn.execute(
            'INSERT INTO guide_books (property_id, name, description, is_public) VALUES (:property_id, :name, :description, :is_public)',
            property_id=property_id[0],
            name='Default Guide Book',
            description='Default property guide book',
            is_public=True
        )
        guide_book_id = conn.execute('SELECT last_insert_rowid()').scalar()
        
        # Migrate existing recommendations marked as in_guide_book
        conn.execute(
            '''INSERT INTO guide_book_recommendations (guide_book_id, recommendation_id)
               SELECT :guide_book_id, id FROM recommendation_blocks 
               WHERE property_id = :property_id AND in_guide_book = 1''',
            guide_book_id=guide_book_id,
            property_id=property_id[0]
        )
    
    # Remove in_guide_book column from recommendation_blocks
    op.drop_column('recommendation_blocks', 'in_guide_book')

def downgrade():
    # Add back in_guide_book column
    op.add_column('recommendation_blocks',
        sa.Column('in_guide_book', sa.Boolean(), nullable=False, server_default='0')
    )
    
    # Migrate guide book recommendations back to in_guide_book flag
    conn = op.get_bind()
    conn.execute(
        '''UPDATE recommendation_blocks 
           SET in_guide_book = 1 
           WHERE id IN (SELECT DISTINCT recommendation_id FROM guide_book_recommendations)'''
    )
    
    # Drop tables and indexes
    op.drop_index('idx_guide_book_recommendations_recommendation_id', 'guide_book_recommendations')
    op.drop_index('idx_guide_book_recommendations_guide_book_id', 'guide_book_recommendations')
    op.drop_index('idx_guide_books_access_token', 'guide_books')
    op.drop_index('idx_guide_books_property_id', 'guide_books')
    op.drop_table('guide_book_recommendations')
    op.drop_table('guide_books') 