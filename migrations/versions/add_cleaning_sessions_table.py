"""add cleaning sessions table

Revision ID: 7a8b9c0d1e2f
Revises: 1e7861017ca8
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '1e7861017ca8'
branch_labels = None
depends_on = None


def upgrade():
    # Create cleaning_session table
    op.create_table('cleaning_session',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cleaner_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cleaner_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['property.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # Add index for faster lookups
    op.create_index(op.f('ix_cleaning_session_cleaner_id'), 'cleaning_session', ['cleaner_id'], unique=False)
    op.create_index(op.f('ix_cleaning_session_property_id'), 'cleaning_session', ['property_id'], unique=False)
    op.create_index(op.f('ix_cleaning_session_task_id'), 'cleaning_session', ['task_id'], unique=False)


def downgrade():
    # Drop the cleaning_session table
    op.drop_index(op.f('ix_cleaning_session_task_id'), table_name='cleaning_session')
    op.drop_index(op.f('ix_cleaning_session_property_id'), table_name='cleaning_session')
    op.drop_index(op.f('ix_cleaning_session_cleaner_id'), table_name='cleaning_session')
    op.drop_table('cleaning_session')
