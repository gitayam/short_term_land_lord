"""add cleaning feedback table

Revision ID: add_cleaning_feedback
Revises: abbd6437d1df
Create Date: 2023-07-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cleaning_feedback'
down_revision = 'abbd6437d1df'
branch_labels = None
depends_on = None


def upgrade():
    # Create cleaning_feedback table
    op.create_table('cleaning_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cleaning_session_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cleaning_session_id'], ['cleaning_session.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cleaning_session_id')
    )


def downgrade():
    # Drop cleaning_feedback table
    op.drop_table('cleaning_feedback')
