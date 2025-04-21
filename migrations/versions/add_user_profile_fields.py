"""add user profile fields

Revision ID: add_user_profile_fields
Revises: previous_revision
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_profile_fields'
down_revision = None  # Update this with the previous migration's revision ID
branch_labels = None
depends_on = None

def upgrade():
    # Add new profile fields
    op.add_column('users', sa.Column('profile_image', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(50), server_default='UTC'))
    op.add_column('users', sa.Column('language', sa.String(10), server_default='en'))
    op.add_column('users', sa.Column('theme_preference', sa.String(20), server_default='light'))
    op.add_column('users', sa.Column('default_dashboard_view', sa.String(20), server_default='tasks'))
    op.add_column('users', sa.Column('default_calendar_view', sa.String(20), server_default='month'))
    op.add_column('users', sa.Column('default_task_sort', sa.String(20), server_default='due_date'))
    
    # Add notification preferences
    op.add_column('users', sa.Column('email_notifications', sa.Boolean(), server_default='true'))
    op.add_column('users', sa.Column('sms_notifications', sa.Boolean(), server_default='false'))
    op.add_column('users', sa.Column('in_app_notifications', sa.Boolean(), server_default='true'))
    op.add_column('users', sa.Column('notification_frequency', sa.String(20), server_default='immediate'))
    
    # Add security settings
    op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), server_default='false'))
    op.add_column('users', sa.Column('two_factor_method', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('last_password_change', sa.DateTime(), nullable=True))
    
    # Add connected services
    op.add_column('users', sa.Column('google_calendar_connected', sa.Boolean(), server_default='false'))
    op.add_column('users', sa.Column('google_calendar_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('twilio_phone_verified', sa.Boolean(), server_default='false'))
    op.add_column('users', sa.Column('slack_workspace_id', sa.String(100), nullable=True))

def downgrade():
    # Remove all added columns
    op.drop_column('users', 'profile_image')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'language')
    op.drop_column('users', 'theme_preference')
    op.drop_column('users', 'default_dashboard_view')
    op.drop_column('users', 'default_calendar_view')
    op.drop_column('users', 'default_task_sort')
    op.drop_column('users', 'email_notifications')
    op.drop_column('users', 'sms_notifications')
    op.drop_column('users', 'in_app_notifications')
    op.drop_column('users', 'notification_frequency')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'two_factor_method')
    op.drop_column('users', 'last_password_change')
    op.drop_column('users', 'google_calendar_connected')
    op.drop_column('users', 'google_calendar_token')
    op.drop_column('users', 'twilio_phone_verified')
    op.drop_column('users', 'slack_workspace_id') 