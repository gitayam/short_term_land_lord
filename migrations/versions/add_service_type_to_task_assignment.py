"""Add service_type to task_assignment and update user roles

Revision ID: 9f8a2c3b4d5e
Revises: 42f118876149
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9f8a2c3b4d5e'
down_revision = '42f118876149'
branch_labels = None
depends_on = None

def upgrade():
    # Create ServiceType enum
    service_type_enum = postgresql.ENUM('cleaning', 'handyman', 'lawn_care', 'pool_maintenance', 'general_maintenance', 'other', name='servicetype')
    service_type_enum.create(op.get_bind())
    
    # Add service_type column to task_assignment table
    op.add_column('task_assignment', sa.Column('service_type', sa.Enum('cleaning', 'handyman', 'lawn_care', 'pool_maintenance', 'general_maintenance', 'other', name='servicetype'), nullable=True))
    
    # Update existing task assignments for cleaners to have service_type='cleaning'
    op.execute("""
    UPDATE task_assignment
    SET service_type = 'cleaning'
    FROM "user"
    WHERE task_assignment.user_id = "user".id AND "user".role = 'cleaner'
    """)
    
    # Update existing task assignments for maintenance to have service_type='general_maintenance'
    op.execute("""
    UPDATE task_assignment
    SET service_type = 'general_maintenance'
    FROM "user"
    WHERE task_assignment.user_id = "user".id AND "user".role = 'maintenance'
    """)
    
    # Create temporary enum with new values
    temp_enum = postgresql.ENUM('property_owner', 'service_staff', 'property_manager', 'admin', name='userroles_new')
    temp_enum.create(op.get_bind())
    
    # Update user roles: cleaner -> service_staff
    op.execute("""
    ALTER TABLE "user" 
    ALTER COLUMN role TYPE userroles_new 
    USING CASE 
        WHEN role::text = 'cleaner' THEN 'service_staff'::userroles_new
        WHEN role::text = 'maintenance' THEN 'service_staff'::userroles_new
        ELSE role::text::userroles_new
    END
    """)
    
    # Drop old enum
    op.execute('DROP TYPE userroles')
    
    # Rename new enum to old name
    op.execute('ALTER TYPE userroles_new RENAME TO userroles')

def downgrade():
    # Create temporary enum with old values
    temp_enum = postgresql.ENUM('property_owner', 'cleaner', 'maintenance', 'admin', name='userroles_old')
    temp_enum.create(op.get_bind())
    
    # This is a lossy conversion - all service_staff will become cleaners
    op.execute("""
    ALTER TABLE "user" 
    ALTER COLUMN role TYPE userroles_old 
    USING CASE 
        WHEN role::text = 'service_staff' THEN 'cleaner'::userroles_old
        WHEN role::text = 'property_manager' THEN 'property_owner'::userroles_old
        ELSE role::text::userroles_old
    END
    """)
    
    # Drop new enum
    op.execute('DROP TYPE userroles')
    
    # Rename old enum to original name
    op.execute('ALTER TYPE userroles_old RENAME TO userroles')
    
    # Remove service_type column from task_assignment
    op.drop_column('task_assignment', 'service_type')
    
    # Drop ServiceType enum
    op.execute('DROP TYPE servicetype')
