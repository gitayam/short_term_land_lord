"""Add missing columns to users table

Revision ID: add_missing_user_columns
Revises: 23258794272e
Create Date: 2023-06-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'add_missing_user_columns'
down_revision = '23258794272e'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table to work with both SQLite and PostgreSQL
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Add username column if it doesn't exist
        try:
            batch_op.add_column(sa.Column('username', sa.String(length=64), nullable=True))
            batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)
            print("Added username column")
        except Exception as e:
            print(f"Error adding username column: {e}")
        
        # Add authentik_id column if it doesn't exist
        try:
            batch_op.add_column(sa.Column('authentik_id', sa.String(length=64), nullable=True))
            print("Added authentik_id column")
        except Exception as e:
            print(f"Error adding authentik_id column: {e}")
        
        # Add signal_identity column if it doesn't exist
        try:
            batch_op.add_column(sa.Column('signal_identity', sa.String(length=64), nullable=True))
            print("Added signal_identity column")
        except Exception as e:
            print(f"Error adding signal_identity column: {e}")
        
        # Add attributes column if it doesn't exist
        # This is more complex as it's a JSONB in PostgreSQL and TEXT in SQLite
        from sqlalchemy.engine.reflection import Inspector
        conn = op.get_bind()
        inspector = Inspector.from_engine(conn)
        columns = [c['name'] for c in inspector.get_columns('user')]
        
        if 'attributes' not in columns:
            try:
                # First try to add as JSONB for PostgreSQL
                try:
                    if conn.dialect.name == 'postgresql':
                        batch_op.add_column(sa.Column('attributes', JSONB, nullable=True))
                    else:
                        batch_op.add_column(sa.Column('attributes', sa.Text(), nullable=True))
                    print("Added attributes column")
                except Exception as e:
                    # Fallback to Text for SQLite
                    print(f"Error adding attributes as JSONB: {e}")
                    batch_op.add_column(sa.Column('attributes', sa.Text(), nullable=True))
                    print("Added attributes column as Text")
            except Exception as e:
                print(f"Error adding attributes column: {e}")

    # After all columns are added, set defaults
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        try:
            conn.execute(sa.text("UPDATE \"user\" SET attributes = '{}' WHERE attributes IS NULL"))
            print("Set default for attributes column")
        except Exception as e:
            print(f"Error setting default for attributes: {e}")


def downgrade():
    # Use batch_alter_table to work with both SQLite and PostgreSQL
    with op.batch_alter_table('user', schema=None) as batch_op:
        try:
            batch_op.drop_index(batch_op.f('ix_user_username'))
            batch_op.drop_column('username')
            batch_op.drop_column('authentik_id')
            batch_op.drop_column('signal_identity')
            batch_op.drop_column('attributes')
        except Exception as e:
            print(f"Error during downgrade: {e}") 