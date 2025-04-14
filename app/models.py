from datetime import datetime, timedelta
import enum
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy import text

# Add this function back - needed by invoicing module
def get_user_fk_target():
    """Get the appropriate foreign key target for user relationships."""
    return "users.id"

class UserRoles(enum.Enum):
    PROPERTY_OWNER = "property_owner"
    SERVICE_STAFF = "service_staff"
    PROPERTY_MANAGER = "property_manager"
    ADMIN = "admin"

class TaskStatus(enum.Enum):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'

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
    BAD = 'BAD'
    OK = 'OK'
    GOOD = 'GOOD'

class InventoryCatalogItem(db.Model):
    __tablename__ = 'inventory_catalog_item'
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(32), nullable=False)  # e.g., 'piece', 'box', 'kg'
    unit_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - explicitly define the primaryjoin to handle table name issues
    creator = db.relationship('User', 
                             foreign_keys=[creator_id],
                             backref='created_catalog_items',
                             primaryjoin="InventoryCatalogItem.creator_id == User.id")
    
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

class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class RegistrationRequest(db.Model):
    __tablename__ = 'registration_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # For property owners/managers
    property_name = db.Column(db.String(128), nullable=True)
    property_address = db.Column(db.String(256), nullable=True)
    property_description = db.Column(db.Text, nullable=True)
    
    # Messages and notes
    message = db.Column(db.Text, nullable=True)  # Message from applicant
    admin_notes = db.Column(db.Text, nullable=True)  # Notes from admin during review
    
    # Status tracking
    status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationship with the admin who reviewed the request
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_requests')
    
    def __repr__(self):
        return f'<RegistrationRequest {self.email} ({self.status.value})>'
    
    def approve(self, admin_user):
        """Approve this registration request and create the user account"""
        # Create the user
        user = User(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            phone=self.phone,
            role=self.role,
            password_hash=self.password_hash  # Already hashed during request creation
        )
        
        # Set admin flag if role is admin (unlikely, but possible)
        if user.role == UserRoles.ADMIN.value:
            user.is_admin = True
            
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # If this is a property owner, create their property too
        if self.role == UserRoles.PROPERTY_OWNER.value and self.property_name:
            property = Property(
                name=self.property_name,
                address=self.property_address,
                description=self.property_description,
                owner_id=user.id,
                status='active'
            )
            db.session.add(property)
        
        # Update request status
        self.status = ApprovalStatus.APPROVED
        self.reviewed_by = admin_user.id
        self.updated_at = datetime.utcnow()
        
        db.session.commit()
        return user
    
    def reject(self, admin_user, reason=None):
        """Reject this registration request"""
        self.status = ApprovalStatus.REJECTED
        self.reviewed_by = admin_user.id
        if reason:
            self.admin_notes = reason
        self.updated_at = datetime.utcnow()
        db.session.commit()

class User(UserMixin, db.Model):
    """
    User model representing system users.
    Table name is explicitly set to 'users' for consistency across all environments
    """
    __tablename__ = 'users'  # Always use 'users' as the table name
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256))  # Increased from 128 to 256 to accommodate scrypt hashes
    role = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    authentik_id = db.Column(db.String(36), unique=True, nullable=True)
    signal_identity = db.Column(db.String(36), unique=True, nullable=True)
    attributes = db.Column(db.Text)  # Store JSON as Text instead of JSON type
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships with explicit primary joins - use different backref names to avoid conflicts
    created_tasks = db.relationship('Task', foreign_keys='Task.creator_id', backref='task_creator', lazy='dynamic',
                                   primaryjoin='User.id == Task.creator_id')
    assigned_tasks = db.relationship('TaskAssignment', foreign_keys='TaskAssignment.user_id', backref='user', lazy='dynamic',
                                    primaryjoin='User.id == TaskAssignment.user_id')
    created_templates = db.relationship('TaskTemplate', foreign_keys='TaskTemplate.creator_id', backref='template_creator', lazy='dynamic',
                                       primaryjoin='User.id == TaskTemplate.creator_id')
    properties = db.relationship('Property', foreign_keys='Property.owner_id', backref='owner_user', lazy='dynamic',
                                primaryjoin='User.id == Property.owner_id', overlaps="owned_properties,owner")
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        # Add debug logging for password checks
        from flask import current_app
        
        if self.password_hash is None:
            current_app.logger.warning(f"User {self.email} has no password hash set")
            return False
            
        result = check_password_hash(self.password_hash, password)
        if not result:
            current_app.logger.warning(f"Password check failed for user {self.email}")
        else:
            current_app.logger.info(f"Password check successful for user {self.email}")
        return result
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def is_property_owner(self):
        """Check if the user has the property owner role."""
        return self.role == UserRoles.PROPERTY_OWNER.value
    
    def is_service_staff(self):
        """Check if the user has the service staff role."""
        return self.role == UserRoles.SERVICE_STAFF.value
    
    def is_property_manager(self):
        """Check if the user has the property manager role."""
        return self.role == UserRoles.PROPERTY_MANAGER.value
    
    def is_admin(self):
        """Check if the user has admin privileges."""
        return bool(self._is_admin) or self.role == UserRoles.ADMIN.value

    # Define getters and setters for is_admin to maintain backward compatibility
    @property
    def _is_admin(self):
        return self.__dict__.get('is_admin', False)
    
    @_is_admin.setter
    def _is_admin(self, value):
        self.__dict__['is_admin'] = value
        
    def is_cleaner(self):
        """Check if the user is a cleaner (service staff with cleaning service type)."""
        if not self.is_service_staff():
            return False
        
        # Check if the user has any cleaning service assignments
        # Avoid circular import by using the current module's TaskAssignment and ServiceType
        cleaning_assignments = TaskAssignment.query.filter_by(
            user_id=self.id, 
            service_type=ServiceType.CLEANING
        ).first()
        
        return cleaning_assignments is not None
    
    def is_maintenance(self):
        """Check if the user is maintenance staff (service staff with maintenance service type)."""
        if not self.is_service_staff():
            return False
        
        # Check if the user has any maintenance service assignments
        # Avoid circular import by using the current module's TaskAssignment and ServiceType
        maintenance_assignments = TaskAssignment.query.filter_by(
            user_id=self.id
        ).filter(
            TaskAssignment.service_type.in_([
                ServiceType.HANDYMAN, 
                ServiceType.GENERAL_MAINTENANCE,
                ServiceType.LAWN_CARE,
                ServiceType.POOL_MAINTENANCE
            ])
        ).first()
        
        return maintenance_assignments is not None

    @property
    def role_enum(self):
        """Get the role as an enum."""
        if self.role:
            try:
                return UserRoles(self.role)
            except ValueError:
                pass
        return None
    
    @role_enum.setter
    def role_enum(self, role_enum):
        """Set the role from an enum."""
        if role_enum is not None:
            self.role = role_enum.value
        else:
            self.role = None

class Property(db.Model):
    __tablename__ = 'property'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    property_type = db.Column(db.String(32), nullable=False, default='house')  # e.g., 'apartment', 'house', 'condo'
    status = db.Column(db.Enum('active', 'inactive', 'maintenance', name='property_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Address components for use in tests
    street_address = db.Column(db.String(128), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    state = db.Column(db.String(64), nullable=True)
    zip_code = db.Column(db.String(16), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    
    # Property details
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Float, nullable=True)
    square_feet = db.Column(db.Integer, nullable=True)
    
    # Guest access fields
    guest_access_enabled = db.Column(db.Boolean, default=False)
    guest_access_token = db.Column(db.String(64), unique=True, nullable=True)
    guest_rules = db.Column(db.Text, nullable=True)
    guest_checkin_instructions = db.Column(db.Text, nullable=True)
    guest_checkout_instructions = db.Column(db.Text, nullable=True)
    guest_wifi_instructions = db.Column(db.Text, nullable=True)
    local_attractions = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.Text, nullable=True)
    guest_faq = db.Column(db.Text, nullable=True)
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('owned_properties', overlaps="owner_user,properties"), overlaps="owner_user,properties")
    property_tasks = db.relationship('Task', backref='property')
    property_rooms = db.relationship('Room', backref='property')
    property_inventory = db.relationship('InventoryItem', backref='property')
    images = db.relationship('PropertyImage', backref='property')
    rooms = db.relationship('Room', backref='property_parent', overlaps="property,property_rooms")
    calendars = db.relationship('PropertyCalendar', backref='property')
    
    @property
    def tasks(self):
        """Get all tasks associated with this property through TaskProperty"""
        return self.task_properties
    
    def __repr__(self):
        return f'<Property {self.name}>'
    
    def get_full_address(self):
        """Return the full address as a formatted string"""
        if self.address:
            return self.address
        
        parts = []
        if self.street_address:
            parts.append(self.street_address)
        
        city_state_zip = []
        if self.city:
            city_state_zip.append(self.city)
        if self.state:
            city_state_zip.append(self.state)
        if self.zip_code:
            city_state_zip.append(self.zip_code)
        
        if city_state_zip:
            parts.append(", ".join(city_state_zip))
        
        if self.country:
            parts.append(self.country)
        
        return ", ".join(parts)
    
    def generate_guest_access_token(self):
        """Generate a unique token for guest access"""
        self.guest_access_token = secrets.token_urlsafe(32)
        return self.guest_access_token
    
    def is_visible_to(self, user):
        """Check if the property is visible to the given user"""
        # Property owners can see their own properties
        if user.is_property_owner() and self.owner_id == user.id:
            return True
        
        # Admins can see all properties
        if user.is_admin():
            return True
        
        # Property managers can see all properties
        if user.role == UserRoles.PROPERTY_MANAGER.value:
            return True
        
        # Service staff can see properties they have tasks for
        if user.is_service_staff():
            # Check if the user has any assigned tasks for this property
            from sqlalchemy.orm import aliased
            from app.models import TaskProperty, TaskAssignment
            
            task_property_alias = aliased(TaskProperty)
            task_assignment_alias = aliased(TaskAssignment)
            
            assigned_tasks = db.session.query(Task).join(
                task_property_alias, Task.id == task_property_alias.task_id
            ).filter(
                task_property_alias.property_id == self.id
            ).join(
                task_assignment_alias, Task.id == task_assignment_alias.task_id
            ).filter(
                task_assignment_alias.user_id == user.id
            ).first()
            
            return assigned_tasks is not None
        
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
        ('direct', 'Direct Booking'),
        ('blocked', 'Blocked Dates'),
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
    
    def get_source_color(self):
        """Return the appropriate color for this calendar source"""
        if self.service == 'airbnb':
            return '#FF5A5F'  # Airbnb red
        elif self.service == 'vrbo':
            return '#3D67FF'  # VRBO blue
        elif self.service == 'direct':
            return '#34C759'  # Direct green
        elif self.service == 'blocked':
            return '#8E8E93'  # Blocked gray
        else:
            return '#767676'  # Default gray
    
    def get_source_class(self):
        """Return the CSS class for this calendar source"""
        return f"{self.service}-event"
    
    def get_source_icon(self):
        """Return the appropriate icon class for this calendar source"""
        if self.service == 'airbnb':
            return 'fab fa-airbnb'
        elif self.service == 'vrbo':
            return 'fas fa-building'
        elif self.service == 'booking':
            return 'fas fa-hotel'
        elif self.service == 'direct':
            return 'fas fa-user-check'
        elif self.service == 'blocked':
            return 'fas fa-ban'
        else:
            return 'fas fa-calendar-alt'

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
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    assign_to_next_cleaner = db.Column(db.Boolean, default=False)
    
    # Add recurring task fields
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.Enum(RecurrencePattern), default=RecurrencePattern.NONE)
    recurrence_interval = db.Column(db.Integer, default=1)
    recurrence_end_date = db.Column(db.DateTime, nullable=True)
    
    # Additional fields used in forms and routes
    notes = db.Column(db.Text, nullable=True)
    linked_to_checkout = db.Column(db.Boolean, default=False)
    calendar_id = db.Column(db.Integer, db.ForeignKey('property_calendar.id', name='fk_task_calendar'), nullable=True)
    
    # Relationships - use task_creator backref instead of creator
    # creator relationship is now handled by the backref from User.created_tasks
    assignments = db.relationship('TaskAssignment', backref='task', lazy='dynamic')
    task_properties = db.relationship('TaskProperty', backref='task', cascade="all, delete-orphan")
    
    @property
    def properties(self):
        """Access properties through TaskProperty relationship"""
        return [tp.property for tp in self.task_properties]
    
    def add_property(self, property_id):
        """Add a property to this task via TaskProperty"""
        # Check if the relationship already exists
        if not any(tp.property_id == property_id for tp in self.task_properties):
            task_property = TaskProperty(property_id=property_id)
            self.task_properties.append(task_property)
            return task_property
        return None
    
    def __repr__(self):
        return f'<Task {self.title}>'
        
    def mark_completed(self, user_id):
        """Mark a task as completed by the specified user"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        # Add completion auditing or history if needed here
        return True
        
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date:
            return False
        return self.due_date < datetime.utcnow() and self.status != TaskStatus.COMPLETED
        
    def get_status_display(self):
        """Return a display-friendly status name"""
        if isinstance(self.status, str):
            # Handle case where status is stored as a string
            return self.status.replace('_', ' ').title()
        else:
            # Handle case where status is stored as an enum
            return self.status.name.replace('_', ' ').title()
        
    def get_priority_display(self):
        """Return a display-friendly priority name"""
        if isinstance(self.priority, str):
            # Handle case where priority is stored as a string
            return self.priority.replace('_', ' ').title()
        else:
            # Handle case where priority is stored as an enum
            return self.priority.name.replace('_', ' ').title()

class TaskAssignment(db.Model):
    __tablename__ = 'task_assignment'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Assignment can be to a user OR to an external person (not in the system)
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
    
    # Relationship
    property = db.relationship('Property', backref='task_properties')
    
    def __repr__(self):
        return f'<TaskProperty task_id={self.task_id} property_id={self.property_id}>'

class CleaningSession(db.Model):
    __tablename__ = 'cleaning_session'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    cleaner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
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
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    booking_id = db.Column(db.String(100), nullable=True)  # External booking ID (Airbnb, etc.)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    guest_name = db.Column(db.String(100), nullable=False)  # Guest name if not tied to a user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property_rel = db.relationship('Property', backref='guest_reviews')
    creator = db.relationship('User', foreign_keys=[creator_id], backref='submitted_reviews')
    
    def __repr__(self):
        return f'<GuestReview {self.guest_name} - {self.rating}>'
        
    def get_rating_display(self):
        """Get a human-readable representation of the rating"""
        if self.rating <= 2:
            return GuestReviewRating.BAD.value
        elif self.rating <= 3:
            return GuestReviewRating.OK.value
        else:
            return GuestReviewRating.GOOD.value
            
    @property
    def is_negative(self):
        """Check if this is a negative review (2 stars or less)"""
        return self.rating <= 2

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
        setting = db.session.get(cls, key)
        return setting.value if setting else default
    
    @classmethod
    def set_setting(cls, key, value, description=None, visible=True):
        """Create or update a setting"""
        setting = db.session.get(cls, key)
        
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
    if not admin_email or not admin_password:
        current_app.logger.info("Admin credentials not fully specified in environment, skipping admin creation")
        return
    
    # Check if admin user already exists
    query = User.query.filter(User.email == admin_email)
    if admin_username:
        query = query.union(User.query.filter(User.username == admin_username))
    
    existing_admin = query.first()
    
    if existing_admin:
        current_app.logger.info(f"Admin user already exists: {existing_admin.email}")
        # Update admin role if needed
        if existing_admin.role != UserRoles.ADMIN.value:
            existing_admin.role = UserRoles.ADMIN.value
            db.session.commit()
            current_app.logger.info(f"Updated user {existing_admin.email} to admin role")
        return
    
    # Create new admin user
    admin_user = User(
        email=admin_email,
        first_name=current_app.config.get('ADMIN_FIRST_NAME', 'System'),
        last_name=current_app.config.get('ADMIN_LAST_NAME', 'Administrator'),
        role=UserRoles.ADMIN.value,
        is_admin=True
    )
    
    # Set username if provided
    if admin_username:
        admin_user.username = admin_username
        
    admin_user.set_password(admin_password)
    
    db.session.add(admin_user)
    db.session.commit()
    current_app.logger.info(f"Created admin user: {admin_email}")

def migrate_site_settings():
    """Initialize default site settings if they don't exist"""
    # Initialize guest reviews setting (enabled by default)
    if not db.session.get(SiteSettings, 'guest_reviews_enabled'):
        SiteSettings.set_setting('guest_reviews_enabled', 'true', 'Enable guest reviews feature', True)
    
    # Set placeholder for OpenAI API key
    if not db.session.get(SiteSettings, 'openai_api_key'):
        SiteSettings.set_setting('openai_api_key', '', 'OpenAI API Key for AI functionality', False)

@login_manager.user_loader
def load_user(id):
    """Load user by ID."""
    try:
        # First try direct SQL query
        table_name = User.__tablename__  # Use the actual table name from the model
        sql = text(f"SELECT * FROM {table_name} WHERE id = :id")
        result = db.session.execute(sql, {'id': id})
        user_data = result.fetchone()
        
        if user_data:
            user = User()
            for key, value in user_data._mapping.items():
                setattr(user, key, value)
            return user
        
        # Fallback to ORM query
        return User.query.get(int(id))
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error loading user: {e}")
        return None

def init_app(app):
    """Initialize app-specific model configurations"""
    with app.app_context():
        try:
            # No need to dynamically set the table name anymore
            app.logger.info("User model using static table name 'users'")
            
            # Verify the User model is properly configured
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if 'users' in inspector.get_table_names():
                app.logger.info("Users table exists in the database")
            else:
                app.logger.warning("Users table does not exist in the database - it will be created if migrations are run")
                
        except Exception as e:
            app.logger.error(f"Error initializing model: {e}", exc_info=True)

class TaskTemplate(db.Model):
    __tablename__ = 'task_template'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM)
    service_type = db.Column(db.Enum(ServiceType), default=ServiceType.CLEANING)
    recurrence_pattern = db.Column(db.Enum(RecurrencePattern), default=RecurrencePattern.NONE)
    recurrence_interval = db.Column(db.Integer, default=1)  # How many days/weeks/months between recurrences
    is_global = db.Column(db.Boolean, default=False)  # Whether this template is available to all users
    sequence_number = db.Column(db.Integer, default=0)  # For ordering templates
    category = db.Column(db.String(50), nullable=True)  # Category or tag for the template
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships - use template_creator backref instead of creator
    # creator relationship is now handled by the backref from User.created_templates
    
    def __repr__(self):
        return f'<TaskTemplate {self.title}>'