from datetime import datetime, timedelta
import enum
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class UserRoles(enum.Enum):
    PROPERTY_OWNER = "property_owner"
    CLEANER = "cleaner"
    MAINTENANCE = "maintenance"
    ADMIN = "admin"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

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
    OTHER = "other"

class InventoryCatalogItem(db.Model):
    """Global inventory catalog item that can be used across properties"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.Enum(ItemCategory), default=ItemCategory.GENERAL, nullable=False)
    unit_of_measure = db.Column(db.String(20), default="units", nullable=False)
    
    # Detailed information
    sku = db.Column(db.String(50), nullable=True)
    barcode = db.Column(db.String(100), nullable=True, index=True)
    description = db.Column(db.Text, nullable=True)
    unit_cost = db.Column(db.Float, nullable=True)
    purchase_link = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Creator information
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_catalog_items')
    inventory_instances = db.relationship('InventoryItem', back_populates='catalog_item', lazy='dynamic')
    
    def __repr__(self):
        return f'<InventoryCatalogItem {self.name} ({self.unit_of_measure})>'

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
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(512))
    role = db.Column(db.Enum(UserRoles), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    password_resets = db.relationship('PasswordReset', backref='user', lazy='dynamic')
    properties = db.relationship('Property', backref='owner', lazy='dynamic')
    assigned_tasks = db.relationship('TaskAssignment', backref='assignee', lazy='dynamic')
    cleaning_sessions = db.relationship('CleaningSession', foreign_keys='CleaningSession.cleaner_id', backref='assigned_cleaner', lazy='dynamic')
    user_notifications = db.relationship('Notification', backref='recipient', lazy='dynamic', foreign_keys='Notification.user_id')
    task_assignments = db.relationship('TaskAssignment', foreign_keys='TaskAssignment.user_id', lazy='dynamic', overlaps="assigned_tasks,assignee")
    # This relationship is added by the InventoryCatalogItem model: created_catalog_items
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_property_owner(self):
        return self.role == UserRoles.PROPERTY_OWNER
    
    def is_cleaner(self):
        return self.role == UserRoles.CLEANER
    
    def is_maintenance(self):
        return self.role == UserRoles.MAINTENANCE
    
    def is_admin(self):
        return self.role == UserRoles.ADMIN

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Address information
    street_address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(50), default='United States')
    
    # Property specifications
    property_type = db.Column(db.String(50))  # House, Apartment, Condo, etc.
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Float)  # To allow for half bathrooms (1.5, 2.5, etc.)
    square_feet = db.Column(db.Integer)
    year_built = db.Column(db.Integer)
    
    # Direct calendar URL
    ical_url = db.Column(db.String(500), nullable=True)
    
    # Cleaner-specific information
    total_beds = db.Column(db.Integer, comment='Total number of beds in the property')
    bed_sizes = db.Column(db.String(255), comment='Description of bed sizes (e.g., "1 King, 2 Queen, 1 Twin")')
    number_of_tvs = db.Column(db.Integer, comment='Number of TVs in the property')
    number_of_showers = db.Column(db.Integer, comment='Number of showers')
    number_of_tubs = db.Column(db.Integer, comment='Number of bathtubs')
    cleaning_supplies_location = db.Column(db.Text, comment='Description of where cleaning supplies are stored')
    wifi_network = db.Column(db.String(100), comment='WiFi network name')
    wifi_password = db.Column(db.String(100), comment='WiFi password')
    special_instructions = db.Column(db.Text, comment='Any special instructions for cleaners')
    entry_instructions = db.Column(db.Text, comment='Instructions for entering the property (key codes, etc.)')
    
    # Guest-specific information - comment these out as they don't exist in the database yet
    guest_access_token = db.Column(db.String(64), unique=True, nullable=True, comment='Unique token for guest access link')
    guest_rules = db.Column(db.Text, nullable=True, comment='House rules for guests')
    guest_checkin_instructions = db.Column(db.Text, nullable=True, comment='Check-in instructions for guests')
    guest_checkout_instructions = db.Column(db.Text, nullable=True, comment='Check-out instructions for guests')
    guest_wifi_instructions = db.Column(db.Text, nullable=True, comment='WiFi instructions for guests')
    local_attractions = db.Column(db.Text, nullable=True, comment='Information about local attractions')
    emergency_contact = db.Column(db.String(255), nullable=True, comment='Emergency contact information')
    guest_access_enabled = db.Column(db.Boolean, default=False, comment='Whether guest access is enabled')
    
    # Ownership and timestamps
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    calendars = db.relationship('PropertyCalendar', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('TaskProperty', back_populates='property', cascade='all, delete-orphan')
    rooms = db.relationship('Room', back_populates='property', lazy='dynamic', cascade='all, delete-orphan')
    cleaning_sessions = db.relationship('CleaningSession', foreign_keys='CleaningSession.property_id', lazy='dynamic', cascade='all, delete-orphan')
    inventory_items = db.relationship('InventoryItem', back_populates='property', lazy='dynamic', cascade='all, delete-orphan')
    repair_requests = db.relationship('RepairRequest', backref='associated_property', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Property {self.name}>'
    
    def get_primary_image_url(self):
        primary_image = self.images.filter_by(is_primary=True).first()
        if primary_image:
            return primary_image.image_path
        # Return first image if no primary image is set
        first_image = self.images.first()
        if first_image:
            return first_image.image_path
        # Return a default image if no images exist
        return '/static/img/default-property.jpg'
    
    def get_full_address(self):
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}, {self.country}"
    
    def is_visible_to(self, user):
        """Check if property is visible to the given user"""
        # Property owners can see their own properties
        if self.owner_id == user.id:
            return True
        # Cleaners and maintenance staff can see all properties
        if user.is_cleaner() or user.is_maintenance():
            return True
        return False
    
    def generate_guest_access_token(self):
        """Generate a unique token for guest access"""
        if not self.guest_access_token:
            self.guest_access_token = secrets.token_urlsafe(32)
        return self.guest_access_token
    
    def get_guest_access_url(self):
        """Get the full URL for guest access"""
        if not self.guest_access_token:
            return None
        return f"/guest/{self.guest_access_token}"

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
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    
    # Room details
    name = db.Column(db.String(100), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # bedroom, living_room, dining_room, kitchen, bathroom, etc.
    square_feet = db.Column(db.Integer, nullable=True)
    
    # For bedrooms
    bed_type = db.Column(db.String(50), nullable=True)  # king, queen, full, twin, bunk, sofa, etc.
    
    # For rooms with TVs
    has_tv = db.Column(db.Boolean, default=False)
    tv_details = db.Column(db.String(100), nullable=True)
    
    # For bathrooms
    has_shower = db.Column(db.Boolean, default=False)
    has_tub = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    property = db.relationship('Property', back_populates='rooms')
    
    def __repr__(self):
        return f'<Room {self.name} ({self.room_type}) in {self.property.name}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    notes = db.Column(db.Text)
    
    # Recurrence information
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.Enum(RecurrencePattern), default=RecurrencePattern.NONE)
    recurrence_interval = db.Column(db.Integer, default=1)  # e.g., every 2 weeks
    recurrence_end_date = db.Column(db.DateTime, nullable=True)
    
    # Calendar event link
    linked_to_checkout = db.Column(db.Boolean, default=False)
    calendar_id = db.Column(db.Integer, db.ForeignKey('property_calendar.id'), nullable=True)
    
    # Dynamic assignment to next cleaner
    assign_to_next_cleaner = db.Column(db.Boolean, default=False)
    
    # Creator information
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_tasks')
    calendar = db.relationship('PropertyCalendar', backref='linked_tasks')
    assignments = db.relationship('TaskAssignment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    properties = db.relationship('TaskProperty', back_populates='task', cascade='all, delete-orphan')
    associated_cleaning_sessions = db.relationship('CleaningSession', foreign_keys='CleaningSession.task_id', lazy='dynamic', cascade='all, delete-orphan')
    task_notifications = db.relationship('Notification', backref='related_task', lazy='dynamic', foreign_keys='Notification.task_id')
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def mark_completed(self, user_id=None):
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        # If this is a recurring task, create the next occurrence
        if self.is_recurring and self.recurrence_pattern != RecurrencePattern.NONE:
            self.create_next_occurrence()
    
    def create_next_occurrence(self):
        # Calculate the next due date based on recurrence pattern
        if not self.due_date:
            return None
            
        next_due_date = None
        if self.recurrence_pattern == RecurrencePattern.DAILY:
            next_due_date = self.due_date + timedelta(days=self.recurrence_interval)
        elif self.recurrence_pattern == RecurrencePattern.WEEKLY:
            next_due_date = self.due_date + timedelta(weeks=self.recurrence_interval)
        elif self.recurrence_pattern == RecurrencePattern.MONTHLY:
            # Add months - this is a simplification
            next_due_date = self.due_date + timedelta(days=30 * self.recurrence_interval)
        elif self.recurrence_pattern == RecurrencePattern.CUSTOM:
            # For custom patterns (which includes the cleaning-specific patterns),
            # the next occurrence will be created when a cleaning is scheduled
            return None
        
        # Check if we've reached the end date
        if self.recurrence_end_date and next_due_date > self.recurrence_end_date:
            return None
            
        # Create a new task instance
        new_task = Task(
            title=self.title,
            description=self.description,
            due_date=next_due_date,
            priority=self.priority,
            notes=self.notes,
            is_recurring=self.is_recurring,
            recurrence_pattern=self.recurrence_pattern,
            recurrence_interval=self.recurrence_interval,
            recurrence_end_date=self.recurrence_end_date,
            linked_to_checkout=self.linked_to_checkout,
            calendar_id=self.calendar_id,
            assign_to_next_cleaner=self.assign_to_next_cleaner,
            creator_id=self.creator_id
        )
        
        # Copy property associations
        for task_property in self.properties:
            new_task_property = TaskProperty(property_id=task_property.property_id)
            new_task.properties.append(new_task_property)
        
        # Copy assignments
        for assignment in self.assignments:
            new_assignment = TaskAssignment(
                user_id=assignment.user_id,
                external_name=assignment.external_name,
                external_phone=assignment.external_phone
            )
            new_task.assignments.append(new_assignment)
            
        db.session.add(new_task)
        return new_task

class TaskAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    
    # Assignment can be to a user OR to an external person (not in the system)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    external_name = db.Column(db.String(100), nullable=True)
    external_phone = db.Column(db.String(20), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        if self.user_id:
            return f'<TaskAssignment to User {self.user_id}>'
        else:
            return f'<TaskAssignment to {self.external_name}>'

class TaskProperty(db.Model):
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', back_populates='properties')
    property = db.relationship('Property', back_populates='tasks')

class CleaningSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cleaner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Request details
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)  # Location within the property
    severity = db.Column(db.Enum(RepairRequestSeverity), default=RepairRequestSeverity.MEDIUM, nullable=False)
    status = db.Column(db.Enum(RepairRequestStatus), default=RepairRequestStatus.PENDING, nullable=False)
    
    # Optional fields
    additional_notes = db.Column(db.Text, nullable=True)
    
    # If this request was converted to a task
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property = db.relationship('Property', foreign_keys=[property_id])
    reporter = db.relationship('User', backref='submitted_repair_requests')
    task = db.relationship('Task', backref='source_repair_request')
    media = db.relationship('RepairRequestMedia', backref='repair_request', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<RepairRequest {self.id}: {self.title} ({self.status.value})>'

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
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    catalog_item_id = db.Column(db.Integer, db.ForeignKey('inventory_catalog_item.id'), nullable=False)
    
    # Property-specific information
    current_quantity = db.Column(db.Float, default=0, nullable=False)
    storage_location = db.Column(db.String(100), nullable=True)
    reorder_threshold = db.Column(db.Float, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property = db.relationship('Property', back_populates='inventory_items')
    catalog_item = db.relationship('InventoryCatalogItem', back_populates='inventory_instances')
    transactions = db.relationship('InventoryTransaction', back_populates='item', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<InventoryItem {self.catalog_item.name} ({self.current_quantity} {self.catalog_item.unit_of_measure}) at {self.property.name}>'
    
    def is_low_stock(self):
        """Check if the item is below its reorder threshold"""
        if self.reorder_threshold is None:
            return False
        return self.current_quantity <= self.reorder_threshold
    
    def update_quantity(self, amount, transaction_type):
        """Update the item quantity based on transaction type"""
        if transaction_type in [TransactionType.RESTOCK, TransactionType.TRANSFER_IN]:
            self.current_quantity += amount
        elif transaction_type in [TransactionType.USAGE, TransactionType.TRANSFER_OUT]:
            self.current_quantity = max(0, self.current_quantity - amount)
        elif transaction_type == TransactionType.ADJUSTMENT:
            self.current_quantity = amount
        
        self.updated_at = datetime.utcnow()

class InventoryTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    previous_quantity = db.Column(db.Float, nullable=False)
    new_quantity = db.Column(db.Float, nullable=False)
    
    # For transfers between properties
    source_property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
    destination_property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
    
    # User who performed the transaction
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    item = db.relationship('InventoryItem', back_populates='transactions')
    user = db.relationship('User', foreign_keys=[user_id])
    source_property = db.relationship('Property', foreign_keys=[source_property_id], backref='outgoing_transfers')
    destination_property = db.relationship('Property', foreign_keys=[destination_property_id], backref='incoming_transfers')
    
    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type.value} of {self.quantity} {self.item.catalog_item.unit_of_measure} of {self.item.catalog_item.name}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships - fixed overlapping issues
    user = db.relationship('User', foreign_keys=[user_id], overlaps="recipient,user_notifications")
    task = db.relationship('Task', foreign_keys=[task_id], overlaps="related_task,task_notifications")
    
    def __repr__(self):
        return f'<Notification {self.id} to {self.user.email} via {self.channel.value}>'
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))