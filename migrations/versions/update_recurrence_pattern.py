"""Update RecurrencePattern enum

Revision ID: update_recurrence_pattern
Create Date: 2025-03-30 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_recurrence_pattern'
down_revision = 'fd582bab23f5'  # Use your latest migration here
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary type with all values
    op.execute("ALTER TYPE recurrencepattern ADD VALUE IF NOT EXISTS 'every_cleaning'")
    op.execute("ALTER TYPE recurrencepattern ADD VALUE IF NOT EXISTS 'weekly_cleaning'")
    op.execute("ALTER TYPE recurrencepattern ADD VALUE IF NOT EXISTS 'monthly_cleaning'")


def downgrade():
    # Cannot easily remove enum values in PostgreSQL
    pass 