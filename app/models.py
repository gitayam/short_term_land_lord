from datetime import datetime, timedelta
import enum
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy import text

def get_user_table_name():
    """Get the appropriate table name based on the database dialect."""
    try:
        if db.engine.dialect.name == 'postgresql':
            return 'users'
        return 'user'
    except RuntimeError:
        # If we're outside an application context, default to 'users'
        return 'users'

class UserRoles(enum.Enum):
    PROPERTY_OWNER = "property_owner"
    SERVICE_STAFF = "service_staff"
    PROPERTY_MANAGER = "property_manager"
    ADMIN = "admin"

class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class RecurrencePattern(enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
    # Comment out the problematic values for now
    # EVERY_CLEANING = "every_cleaning"
    # WEEKLY_CLEANING = "weekly_cleaning"
    # MONTHLY_CLEANING = "monthly_cleaning"
    
    # Instead, use the existing values but interpret them differently in the UI
    # This preserves database compatibility
    
    @classmethod
    def get_cleaning_patterns(cls):
        """Return cleaning-specific patterns for display in the UI"""
        return [
            {"value": cls.CUSTOM.value, "name": "Every Cleaning", "description": "Task applies to every cleaning session"},
            {"value": cls.WEEKLY.value, "name": "Weekly Cleaning", "description": "Task recurs weekly if there's a cleaning scheduled"},
            {"value": cls.MONTHLY.value, "name": "Monthly Cleaning", "description": "Task recurs monthly if there's a cleaning scheduled"},
        ]

class MediaType(enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"

class StorageBackend(enum.Enum):
    LOCAL = "local"
    S3 = "s3"
    RCLONE = "rclone"

class ItemCategory(enum.Enum):
    CLEANING = "cleaning"
    BATHROOM = "bathroom"
    KITCHEN = "kitchen"
    BEDROOM = "bedroom"
    LAUNDRY = "laundry"
    GENERAL = "general"
    APPLIANCES = "appliances"
    CLEANING_TOOLS = "cleaning_tools"
    LINENS = "linens" 
    ELECTRONICS = "electronics"
    OUTDOOR = "outdoor"
    FURNITURE = "furniture"
    DECOR = "decor"
    SAFETY = "safety"
    MAINTENANCE = "maintenance"
    OTHER = "other"

class ServiceType(enum.Enum):
    CLEANING = "cleaning"
    HANDYMAN = "handyman"
    LAWN_CARE = "lawn_care"
    POOL_MAINTENANCE = "pool_maintenance"
    GENERAL_MAINTENANCE = "general_maintenance"
    OTHER = "other"

class GuestReviewRating(enum.Enum):
    BAD = "BAD"
    OK = "OK"
    GOOD = "GOOD"

class InventoryCatalogItem(db.Model):
    __tablename__ = 'inventory_catalog_item'
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(32), nullable=False)  # e.g., 'piece', 'box', 'kg'
    unit_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_catalog_items')
    
    def __repr__(self):
        return f'<InventoryCatalogItem {self.name}>'

class TransactionType(enum.Enum):
    RESTOCK = "restock"
    USAGE = "usage"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    ADJUSTMENT = "adjustment"

class RepairRequestStatus(enum.Enum):
    PENDING = "pending_status"
    APPROVED = "approved_status"
    REJECTED = "rejected_status"
    CONVERTED = "converted_to_task_status"

class RepairRequestSeverity(enum.Enum):
    LOW = "low_severity"
    MEDIUM = "medium_severity"
    HIGH = "high_severity"
    URGENT = "urgent_severity"

class NotificationType(enum.Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_REMINDER = "task_reminder"
    CALENDAR_UPDATE = "calendar_update"
    TASK_COMPLETED = "task_completed"
    INVENTORY_LOW = "inventory_low"
    REPAIR_REQUEST = "repair_request"

class NotificationChannel(enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(32), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def is_property_owner(self):
        """Check if the user has the property owner role."""
        return self.role == UserRoles.PROPERTY_OWNER.value
    
    def __repr__(self):
        return f'<User {self.email}>'

class Property(db.Model):
    __tablename__ = 'property'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    property_type = db.Column(db.String(32), nullable=False)  # e.g., 'apartment', 'house', 'condo'
    status = db.Column(db.Enum('active', 'inactive', 'maintenance', name='property_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_properties')
    property_tasks = db.relationship('Task', backref='property')
    property_rooms = db.relationship('Room', backref='property')
    property_inventory = db.relationship('InventoryItem', backref='property')
    
    def __repr__(self):
        return f'<Property {self.name}>'

class PropertyImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    caption = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PropertyImage {self.image_path}>'

class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def create_token(cls, user, expiration=3600):
        # Generate a secure token
        token = secrets.token_urlsafe(32)
        
        # Delete any existing tokens for this user
        cls.query.filter_by(user_id=user.id).delete()
        
        # Create new token
        reset = cls(
            token=token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(seconds=expiration)
        )
        db.session.add(reset)
        
        return token
    
    @classmethod
    def verify_token(cls, token):
        reset = cls.query.filter_by(token=token).first()
        if reset is None or reset.expires_at < datetime.utcnow():
            return None
        
        return reset.user

class PropertyCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    
    # Calendar information
    name = db.Column(db.String(100), nullable=False)
    ical_url = db.Column(db.String(500), nullable=False)
    
    # Whether this calendar covers the entire property or just a specific room
    is_entire_property = db.Column(db.Boolean, default=True)
    room_name = db.Column(db.String(100), nullable=True)  # Optional, only if is_entire_property is False
    
    # Source of the calendar
    SERVICE_CHOICES = [
        ('airbnb', 'Airbnb'),
        ('vrbo', 'VRBO'),
        ('booking', 'Booking.com'),
        ('other', 'Other')
    ]
    service = db.Column(db.String(20), nullable=False, default='other')
    
    # Last synchronization information
    last_synced = db.Column(db.DateTime, nullable=True)
    sync_status = db.Column(db.String(50), nullable=True)
    sync_error = db.Column(db.String(255), nullable=True)
    
    # When the calendar was added
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PropertyCalendar {self.name} for {self.property.name}>'
    
    def get_service_display(self):
        """Return a user-friendly display name for the calendar service"""
        service_map = dict(self.SERVICE_CHOICES)
        return service_map.get(self.service, 'Other')

    def is_synced_recently(self):
        """Check if the calendar has been synced in the last 24 hours"""
        if not self.last_synced:
            return False
        return (datetime.utcnow() - self.last_synced) < timedelta(hours=24)

class Room(db.Model):
    __tablename__ = 'room'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    room_type = db.Column(db.String(64))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room_furniture = db.relationship('RoomFurniture', backref='room')
    
    def __repr__(self):
        return f'<Room {self.name}>'

class RoomFurniture(db.Model):
    __tablename__ = 'room_furniture'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    furniture_type = db.Column(db.String(64))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RoomFurniture {self.name}>'

class Task(db.Model):
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'cancelled', name='task_status'), default='pending')
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='task_priority'), default='medium')
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_tasks')
    assignments = db.relationship('TaskAssignment', backref='task', lazy='dynamic')
    task_properties = db.relationship('TaskProperty', backref='task')
    
    def __repr__(self):
        return f'<Task {self.title}>'

class TaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    # Assignment can be to a user OR to an external person (not in the system)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    external_name = db.Column(db.String(100), nullable=True)
    external_phone = db.Column(db.String(20), nullable=True)
    external_email = db.Column(db.String(120), nullable=True)
    
    # Service type for service staff assignments
    service_type = db.Column(db.Enum(ServiceType), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        if self.user_id:
            service_info = f" ({self.service_type.value})" if self.service_type else ""
            return f'<TaskAssignment to User {self.user_id}{service_info}>'
        else:
            contact_info = []
            if self.external_phone:
                contact_info.append(f"Phone: {self.external_phone}")
            if self.external_email:
                contact_info.append(f"Email: {self.external_email}")
            contact_str = f" ({', '.join(contact_info)})" if contact_info else ""
            return f'<TaskAssignment to {self.external_name}{contact_str}>'

class TaskProperty(db.Model):
    __tablename__ = 'task_property'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaskProperty task_id={self.task_id} property_id={self.property_id}>'

class CleaningSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cleaner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with clear distinct names
    associated_property = db.relationship('Property', foreign_keys=[property_id], overlaps="cleaning_sessions")
    associated_task = db.relationship('Task', foreign_keys=[task_id], overlaps="associated_cleaning_sessions")
    
    def __repr__(self):
        if hasattr(self, 'assigned_cleaner') and self.assigned_cleaner:
            cleaner_name = self.assigned_cleaner.get_full_name()
        else:
            cleaner_name = f"User #{self.cleaner_id}"
            
        if hasattr(self, 'associated_property') and self.associated_property:
            property_name = self.associated_property.name
        else:
            property_name = f"Property #{self.property_id}"
            
        return f'<CleaningSession {self.id} by {cleaner_name} at {property_name}>'
    
    def complete(self):
        """Complete the cleaning session and calculate duration"""
        self.end_time = datetime.utcnow()
        if self.start_time:
            # Calculate duration in minutes
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        return self.duration_minutes
    
    def get_duration_display(self):
        """Return a human-readable duration"""
        if not self.duration_minutes:
            return "Unknown"
        
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    @classmethod
    def get_active_session(cls, cleaner_id):
        """Get the active cleaning session for a cleaner if one exists"""
        return cls.query.filter_by(cleaner_id=cleaner_id, end_time=None).first()
    
    @property
    def has_start_video(self):
        """Check if this session has a start video"""
        return CleaningMedia.query.filter_by(
            cleaning_session_id=self.id,
            media_type=MediaType.VIDEO,
            is_start_video=True
        ).first() is not None
    
    @property
    def has_end_video(self):
        """Check if this session has an end video"""
        return CleaningMedia.query.filter_by(
            cleaning_session_id=self.id,
            media_type=MediaType.VIDEO,
            is_start_video=False
        ).first() is not None

class CleaningFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cleaning_session_id = db.Column(db.Integer, db.ForeignKey('cleaning_session.id'), nullable=False, unique=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    cleaning_session = db.relationship('CleaningSession', backref=db.backref('feedback', uselist=False))
    
    def __repr__(self):
        return f'<CleaningFeedback {self.id} for session {self.cleaning_session_id} - Rating: {self.rating}>'

class CleaningMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cleaning_session_id = db.Column(db.Integer, db.ForeignKey('cleaning_session.id'), nullable=False)
    media_type = db.Column(db.Enum(MediaType), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    storage_backend = db.Column(db.Enum(StorageBackend), default=StorageBackend.LOCAL, nullable=False)
    
    # For videos, track if it's a start or end video
    is_start_video = db.Column(db.Boolean, nullable=True)
    
    # Metadata
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    cleaning_session = db.relationship('CleaningSession', backref='media')
    
    def __repr__(self):
        return f'<CleaningMedia {self.id} ({self.media_type.value}) for session {self.cleaning_session_id}>'
    
    def get_url(self):
        """Return the URL to access this media file based on storage backend"""
        if self.storage_backend == StorageBackend.LOCAL:
            return self.file_path
        elif self.storage_backend == StorageBackend.S3:
            # This would be expanded with actual S3 URL construction
            return self.file_path
        elif self.storage_backend == StorageBackend.RCLONE:
            # This would be expanded with actual rclone URL construction
            return self.file_path
        return self.file_path

# Junction table for issue reports and media
issue_media = db.Table('issue_media',
    db.Column('issue_id', db.Integer, db.ForeignKey('issue_report.id'), primary_key=True),
    db.Column('media_id', db.Integer, db.ForeignKey('cleaning_media.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class IssueReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cleaning_session_id = db.Column(db.Integer, db.ForeignKey('cleaning_session.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)  # Location within the property
    additional_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cleaning_session = db.relationship('CleaningSession', backref='issues')
    media = db.relationship('CleaningMedia', secondary='issue_media', backref='issues')
    
    def __repr__(self):
        return f'<IssueReport {self.id} for session {self.cleaning_session_id}>'

class RepairRequest(db.Model):
    __tablename__ = 'repair_request'
    
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'cancelled', name='repair_status'), default='pending')
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='repair_priority'), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reported_repairs')
    associated_property = db.relationship('Property', foreign_keys=[property_id], backref='repair_requests')
    
    def __repr__(self):
        return f'<RepairRequest {self.id}>'

class RepairRequestMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    repair_request_id = db.Column(db.Integer, db.ForeignKey('repair_request.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    storage_backend = db.Column(db.Enum(StorageBackend), default=StorageBackend.LOCAL, nullable=False)
    
    # Metadata
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RepairRequestMedia {self.id} for request {self.repair_request_id}>'
    
    def get_url(self):
        """Return the URL to access this media file based on storage backend"""
        if self.storage_backend == StorageBackend.LOCAL:
            return self.file_path
        elif self.storage_backend == StorageBackend.S3:
            return self.file_path
        elif self.storage_backend == StorageBackend.RCLONE:
            return self.file_path
        return self.file_path

class InventoryItem(db.Model):
    __tablename__ = 'inventory_item'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    item_transactions = db.relationship('InventoryTransaction', backref='item')
    
    def __repr__(self):
        return f'<InventoryItem {self.name}>'

class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(32), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type} {self.quantity}>'

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.message}>'

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'

class GuestReview(db.Model):
    __tablename__ = 'guest_review'
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_guest_reviews')
    guest = db.relationship('Guest', foreign_keys=[guest_id], backref='reviews')
    
    def __repr__(self):
        return f'<GuestReview {self.id}>'

class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a setting value by its key"""
        setting = cls.query.get(key)
        return setting.value if setting else default
    
    @classmethod
    def set_setting(cls, key, value, description=None, visible=True):
        """Create or update a setting"""
        setting = cls.query.get(key)
        
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
            if description:
                setting.description = description
            setting.visible = visible
        else:
            setting = cls(key=key, value=value, description=description, visible=visible)
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @classmethod
    def get_openai_api_key(cls):
        """Get the OpenAI API key from settings"""
        return cls.get_setting('openai_api_key')
    
    @classmethod
    def is_guest_reviews_enabled(cls):
        """Check if guest reviews feature is enabled"""
        value = cls.get_setting('guest_reviews_enabled', 'false')
        return value.lower() == 'true'

def create_admin_user_from_env():
    """Create an admin user from environment variables if one doesn't exist"""
    from flask import current_app
    
    # Check if we have admin credentials in environment
    admin_email = current_app.config.get('ADMIN_EMAIL')
    admin_username = current_app.config.get('ADMIN_USERNAME')
    admin_password = current_app.config.get('ADMIN_PASSWORD')
    
    # If no admin credentials are provided, skip
    if not admin_email or not admin_username or not admin_password:
        current_app.logger.info("Admin credentials not fully specified in environment, skipping admin creation")
        return
    
    # Check if admin user already exists
    existing_admin = User.query.filter(
        (User.email == admin_email) | 
        (User.username == admin_username)
    ).first()
    
    if existing_admin:
        current_app.logger.info(f"Admin user already exists: {existing_admin.email}")
        # Update admin role if needed
        if existing_admin.role != UserRoles.ADMIN:
            existing_admin.role = UserRoles.ADMIN
            db.session.commit()
            current_app.logger.info(f"Updated user {existing_admin.email} to admin role")
        return
    
    # Create new admin user
    admin_user = User(
        username=admin_username,
        email=admin_email,
        first_name=current_app.config.get('ADMIN_FIRST_NAME', 'System'),
        last_name=current_app.config.get('ADMIN_LAST_NAME', 'Administrator'),
        role=UserRoles.ADMIN
    )
    admin_user.set_password(admin_password)
    
    db.session.add(admin_user)
    db.session.commit()
    current_app.logger.info(f"Created admin user: {admin_email}")

def migrate_site_settings():
    """Initialize default site settings if they don't exist"""
    # Initialize guest reviews setting (enabled by default)
    if not SiteSettings.query.get('guest_reviews_enabled'):
        SiteSettings.set_setting('guest_reviews_enabled', 'true', 'Enable guest reviews feature', True)
    
    # Set placeholder for OpenAI API key
    if not SiteSettings.query.get('openai_api_key'):
        SiteSettings.set_setting('openai_api_key', '', 'OpenAI API Key for AI functionality', False)

@login_manager.user_loader
def load_user(id):
    """Load user by ID."""
    try:
        # First try direct SQL query
        sql = text(f"SELECT * FROM {User.__tablename__} WHERE id = :id")
        result = db.session.execute(sql, {'id': id})
        user_data = result.fetchone()
        
        if user_data:
            user = User()
            for key, value in user_data.items():
                setattr(user, key, value)
            return user
        
        # Fallback to ORM query
        return User.query.get(int(id))
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Initialize the table name when the app is created
def init_app(app):
    with app.app_context():
        User.__tablename__ = get_user_table_name()

def get_user_fk_target():
    """Get the appropriate foreign key target for user relationships."""
    try:
        if db.engine.dialect.name == 'postgresql':
            return 'users.id'
        return 'user.id'
    except RuntimeError:
        # Default to 'user.id' if outside application context
        return 'user.id'

class TaskTemplate(db.Model):
    __tablename__ = 'task_template'
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey(get_user_fk_target()), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='task_priority'), default='medium')
    estimated_duration = db.Column(db.Integer)  # in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', 
                            foreign_keys=[creator_id],
                            primaryjoin='TaskTemplate.creator_id == User.id',
                            backref='created_task_templates')
    
    def __repr__(self):
        return f'<TaskTemplate {self.title}>'