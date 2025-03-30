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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.Enum(UserRoles), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    password_resets = db.relationship('PasswordReset', backref='user', lazy='dynamic')
    properties = db.relationship('Property', backref='owner', lazy='dynamic')
    assigned_tasks = db.relationship('TaskAssignment', backref='assignee', lazy='dynamic')
    
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
    
    # Ownership and timestamps
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    calendars = db.relationship('PropertyCalendar', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    tasks = db.relationship('TaskProperty', back_populates='property', cascade='all, delete-orphan')
    rooms = db.relationship('Room', back_populates='property', lazy='dynamic', cascade='all, delete-orphan')
    
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
    
    # Relationship to user (if assigned to a user)
    user = db.relationship('User', backref='task_assignments')
    
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

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))