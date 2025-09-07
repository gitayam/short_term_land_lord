"""
Migration to add 'general_maintenance' to the servicetype enum in PostgreSQL.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_general_maintenance_to_servicetype'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add 'general_maintenance' to the servicetype enum
    op.execute("ALTER TYPE servicetype ADD VALUE IF NOT EXISTS 'general_maintenance';")

def downgrade():
    # Downgrade is not supported for removing enum values in PostgreSQL
    pass 