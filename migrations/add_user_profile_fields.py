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
    with op.batch_alter_table('users') as batch_op:
        # Check if columns exist before adding them
        columns = [
            ('profile_image', sa.String(255), True),
            ('timezone', sa.String(50), 'UTC'),
            ('language', sa.String(10), 'en'),
            ('theme_preference', sa.String(20), 'light'),
            ('default_dashboard_view', sa.String(20), 'tasks'),
            ('default_calendar_view', sa.String(20), 'month'),
            ('default_task_sort', sa.String(20), 'due_date'),
            ('email_notifications', sa.Boolean(), True),
            ('sms_notifications', sa.Boolean(), False),
            ('in_app_notifications', sa.Boolean(), True),
            ('notification_frequency', sa.String(20), 'immediate'),
            ('two_factor_enabled', sa.Boolean(), False),
            ('two_factor_method', sa.String(20), None),
            ('last_password_change', sa.DateTime(), None),
            ('google_calendar_connected', sa.Boolean(), False),
            ('google_calendar_token', sa.Text(), None),
            ('twilio_phone_verified', sa.Boolean(), False),
            ('slack_workspace_id', sa.String(100), None)
        ]
        
        for column_name, column_type, default in columns:
            try:
                batch_op.add_column(sa.Column(column_name, column_type, 
                    server_default=str(default) if default is not None else None,
                    nullable=True))
            except Exception as e:
                print(f"Column {column_name} might already exist: {e}")

def downgrade():
    # Remove all added columns
    with op.batch_alter_table('users') as batch_op:
        columns = [
            'profile_image', 'timezone', 'language', 'theme_preference',
            'default_dashboard_view', 'default_calendar_view', 'default_task_sort',
            'email_notifications', 'sms_notifications', 'in_app_notifications',
            'notification_frequency', 'two_factor_enabled', 'two_factor_method',
            'last_password_change', 'google_calendar_connected', 'google_calendar_token',
            'twilio_phone_verified', 'slack_workspace_id'
        ]
        
        for column_name in columns:
            try:
                batch_op.drop_column(column_name)
            except Exception as e:
                print(f"Column {column_name} might not exist: {e}") 