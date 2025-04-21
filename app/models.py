from datetime import datetime, timedelta
import enum
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy import text
from flask import url_for

# Add this function back - needed by invoicing module
def get_user_fk_target():
    """Get the appropriate foreign key target for user relationships."""
    return "users.id"

class UserRoles(enum.Enum):
    PROPERTY_OWNER = "property_owner"
    SERVICE_STAFF = "service_staff"
    PROPERTY_MANAGER = "property_manager"
    ADMIN = "admin"
    TENANT = "tenant"
    PROPERTY_GUEST = "property_guest"

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
    category = db.Column(db.Enum(ItemCategory), nullable=False, default=ItemCategory.GENERAL)
    unit = db.Column(db.String(32), nullable=False)  # e.g., 'piece', 'box', 'kg'
    unit_price = db.Column(db.Float, nullable=False)
    sku = db.Column(db.String(50), nullable=True)
    barcode = db.Column(db.String(100), nullable=True, unique=True)
    purchase_link = db.Column(db.String(500), nullable=True)
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
        
    @property
    def unit_of_measure(self):
        """Alias for unit to maintain compatibility with templates"""
        return self.unit
        
    @unit_of_measure.setter
    def unit_of_measure(self, value):
        self.unit = value
        
    @property
    def unit_cost(self):
        """Alias for unit_price to maintain compatibility with templates"""
        return self.unit_price
        
    @unit_cost.setter
    def unit_cost(self, value):
        self.unit_price = value

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
    is_suspended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    authentik_id = db.Column(db.String(36), unique=True, nullable=True)
    signal_identity = db.Column(db.String(36), unique=True, nullable=True)
    attributes = db.Column(db.Text)  # Store JSON as Text instead of JSON type
    _is_admin = db.Column('is_admin', db.Boolean, default=False)
    
    # New profile fields
    profile_image = db.Column(db.String(255), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    theme_preference = db.Column(db.String(20), default='light')
    default_dashboard_view = db.Column(db.String(20), default='tasks')
    default_calendar_view = db.Column(db.String(20), default='month')
    default_task_sort = db.Column(db.String(20), default='due_date')
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=False)
    in_app_notifications = db.Column(db.Boolean, default=True)
    notification_frequency = db.Column(db.String(20), default='immediate')  # immediate, daily, weekly
    
    # Security settings
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_method = db.Column(db.String(20), nullable=True)  # sms, authenticator
    last_password_change = db.Column(db.DateTime, nullable=True)
    
    # Connected services
    google_calendar_connected = db.Column(db.Boolean, default=False)
    google_calendar_token = db.Column(db.Text, nullable=True)
    twilio_phone_verified = db.Column(db.Boolean, default=False)
    slack_workspace_id = db.Column(db.String(100), nullable=True)
    
    # Relationships with explicit primary joins - use different backref names to avoid conflicts
    created_tasks = db.relationship('Task', 
                                  foreign_keys='Task.creator_id', 
                                  back_populates='creator',
                                  overlaps="created_tasks_direct,task_creator",
                                  lazy='dynamic')
    
    created_tasks_direct = db.relationship('Task', 
                                         foreign_keys='Task.creator_id',
                                         back_populates='creator',
                                         overlaps="created_tasks,task_creator",
                                         lazy='dynamic')
    
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
    
    @property
    def is_property_owner(self):
        """Check if the user has the property owner role."""
        return self.role == UserRoles.PROPERTY_OWNER.value
    
    @property
    def is_service_staff(self):
        """Check if the user has the service staff role."""
        return self.role == UserRoles.SERVICE_STAFF.value
    
    @property
    def is_property_manager(self):
        """Check if the user has the property manager role."""
        return self.role == UserRoles.PROPERTY_MANAGER.value
    
    @property
    def is_property_guest(self):
        """Check if the user has the property guest role."""
        return self.role == UserRoles.PROPERTY_GUEST.value
    
    @property
    def has_admin_role(self):
        """Check if the user has admin privileges."""
        # Always return True for users with ADMIN role, regardless of is_admin column
        return self.role == UserRoles.ADMIN.value or self._is_admin is True

    @property
    def is_cleaner(self):
        """Check if the user is a cleaner (service staff with cleaning service type)."""
        if not self.is_service_staff:
            return False
        
        # Check if the user has any cleaning service assignments
        # Avoid circular import by using the current module's TaskAssignment and ServiceType
        cleaning_assignments = TaskAssignment.query.filter_by(
            user_id=self.id, 
            service_type=ServiceType.CLEANING
        ).first()
        
        return cleaning_assignments is not None
    
    @property
    def is_maintenance(self):
        """Check if this user is a maintenance person."""
        if not self.is_service_staff:
            return False
        
        # Check if the user has any maintenance service assignments
        maintenance_assignments = TaskAssignment.query.filter_by(
            user_id=self.id, 
            service_type=ServiceType.HANDYMAN
        ).first()
        
        return maintenance_assignments is not None
        
    def can_reassign_task(self, task):
        """Check if this user has permission to reassign a task.
        
        Admins and task creators can reassign tasks.
        
        Args:
            task: The task to check reassignment permissions for
            
        Returns:
            bool: True if user can reassign the task, False otherwise
        """
        # Admin users can reassign any task
        if self.has_admin_role:
            return True
            
        # Task creators can reassign their tasks
        if task.creator_id == self.id:
            return True
            
        # Anyone else cannot reassign
        return False
    
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

    def can_complete_task(self, task):
        """Check if this user has permission to complete a task.
        
        Admins, task creators, and assigned users can complete tasks.
        
        Args:
            task: The task to check completion permissions for
            
        Returns:
            bool: True if user can complete the task, False otherwise
        """
        # Admin users can complete any task
        if self.has_admin_role:
            return True
            
        # Task creators can complete their tasks
        if task.creator_id == self.id:
            return True
            
        # Check if user is assigned to the task
        assignment = TaskAssignment.query.filter_by(
            task_id=task.id, 
            user_id=self.id
        ).first()
        
        return assignment is not None

    @property
    def is_admin(self):
        """Get admin status (True if role is ADMIN or is_admin column is True)"""
        return self.role == UserRoles.ADMIN.value or self._is_admin is True
        
    @is_admin.setter
    def is_admin(self, value):
        """Set admin flag directly to database column"""
        self._is_admin = value

    def suspend(self):
        """Suspend the user account"""
        self.is_suspended = True
        db.session.add(self)
        db.session.commit()
    
    def reactivate(self):
        """Reactivate the user account"""
        self.is_suspended = False
        db.session.add(self)
        db.session.commit()
    
    def is_active(self):
        """Override UserMixin's is_active to check suspension status"""
        return not self.is_suspended

class Property(db.Model):
    """
    Property model representing real estate properties in the system.
    
    Relationships:
    - owner: The User who owns this property
    - property_tasks: Tasks associated with this property
    - property_inventory: Inventory items associated with this property
    - images: Images of this property
    - rooms: Rooms that belong to this property (lazy loaded)
    - calendars: Calendars associated with this property
    """
    __tablename__ = 'property'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(128), nullable=True)
    address = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    property_type = db.Column(db.String(32), nullable=False, default='house')  # e.g., 'apartment', 'house', 'condo'
    status = db.Column(db.Enum('active', 'inactive', 'maintenance', name='property_status'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Address components
    street_address = db.Column(db.String(128), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    state = db.Column(db.String(64), nullable=True)
    zip_code = db.Column(db.String(16), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    
    # Property details
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Float, nullable=True)
    square_feet = db.Column(db.Integer, nullable=True)
    year_built = db.Column(db.Integer, nullable=True)
    
    # Waste collection schedule
    trash_day = db.Column(db.String(20), nullable=True)  # e.g., 'Monday', 'Tuesday and Friday'
    trash_schedule_type = db.Column(db.String(20), nullable=True)  # 'weekly', 'biweekly', 'monthly', 'custom'
    trash_schedule_details = db.Column(db.Text, nullable=True)  # JSON string for complex schedules
    recycling_day = db.Column(db.String(20), nullable=True)
    recycling_schedule_type = db.Column(db.String(20), nullable=True)  # 'weekly', 'biweekly', 'monthly', 'custom'
    recycling_schedule_details = db.Column(db.Text, nullable=True)  # JSON string for complex schedules
    recycling_notes = db.Column(db.Text, nullable=True)
    
    # Utility information
    internet_provider = db.Column(db.String(100), nullable=True)
    internet_account = db.Column(db.String(100), nullable=True)
    internet_contact = db.Column(db.String(100), nullable=True)
    electric_provider = db.Column(db.String(100), nullable=True)
    electric_account = db.Column(db.String(100), nullable=True)
    electric_contact = db.Column(db.String(100), nullable=True)
    water_provider = db.Column(db.String(100), nullable=True)
    water_account = db.Column(db.String(100), nullable=True)
    water_contact = db.Column(db.String(100), nullable=True)
    trash_provider = db.Column(db.String(100), nullable=True)
    trash_account = db.Column(db.String(100), nullable=True)
    trash_contact = db.Column(db.String(100), nullable=True)
    
    # Access information
    cleaning_supplies_location = db.Column(db.Text, nullable=True)
    wifi_network = db.Column(db.String(100), nullable=True)
    wifi_password = db.Column(db.String(100), nullable=True)
    special_instructions = db.Column(db.Text, nullable=True)
    entry_instructions = db.Column(db.Text, nullable=True)
    
    # Cleaner-specific information
    total_beds = db.Column(db.Integer, nullable=True)
    bed_sizes = db.Column(db.String(255), nullable=True)
    number_of_tvs = db.Column(db.Integer, nullable=True)
    number_of_showers = db.Column(db.Integer, nullable=True)
    number_of_tubs = db.Column(db.Integer, nullable=True)
    
    # Calendar integration
    ical_url = db.Column(db.String(500), nullable=True)
    
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
    
    # Check-in/out times
    checkin_time = db.Column(db.String(10), nullable=True)
    checkout_time = db.Column(db.String(10), nullable=True)
    
    # Guide book token
    guide_book_token = db.Column(db.String(64), unique=True)
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('owned_properties', overlaps="owner_user,properties"), overlaps="owner_user,properties")
    property_tasks = db.relationship('Task', backref='property')
    property_inventory = db.relationship('InventoryItem', backref='property')
    images = db.relationship('PropertyImage', backref='property')
    rooms = db.relationship('Room', backref='property', lazy='dynamic')
    calendars = db.relationship('PropertyCalendar', backref='property')
    bookings = db.relationship('Booking', backref='property', lazy=True, cascade='all, delete-orphan')
    
    @property
    def tasks(self):
        """Get all tasks associated with this property through TaskProperty"""
        return self.task_properties
    
    def __repr__(self):
        return f'<Property {self.name}>'
    
    def get_full_address(self):
        """Return the full address as a formatted string"""
        if self.street_address or self.city or self.state or self.zip_code or self.country:
            parts = []
            if self.street_address:
                parts.append(self.street_address)
            
            city_state_zip = []
            if self.city:
                city_state_zip.append(self.city)
            
            state_zip = ""
            if self.state and self.zip_code:
                state_zip = f"{self.state} {self.zip_code}"
            elif self.state:
                state_zip = self.state
            elif self.zip_code:
                state_zip = self.zip_code
            
            if state_zip:
                city_state_zip.append(state_zip)
            
            if city_state_zip:
                parts.append(", ".join(city_state_zip))
            
            if self.country:
                parts.append(self.country)
            
            return ", ".join(parts)
        
        # If no components are available, fall back to the address field
        return self.address
    
    def generate_guest_access_token(self):
        """Generate a unique token for guest access"""
        self.guest_access_token = secrets.token_urlsafe(32)
        return self.guest_access_token
    
    def generate_guide_book_token(self):
        """Generate a unique token for public guide book access."""
        if not self.guide_book_token:
            self.guide_book_token = secrets.token_urlsafe(32)
            db.session.commit()
        return self.guide_book_token
    
    def is_visible_to(self, user):
        """Check if the property is visible to the given user"""
        # Property owners can see their own properties
        if user.is_property_owner and self.owner_id == user.id:
            return True
        
        # Admins can see all properties
        if user.has_admin_role:
            return True
        
        # Property managers can see all properties
        if user.role == UserRoles.PROPERTY_MANAGER.value:
            return True
        
        # Service staff can see properties they have tasks for
        if user.is_service_staff:
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

    def get_room_count(self):
        """Safely count the number of rooms"""
        return self.rooms.count()

    def get_primary_image_url(self):
        """Get the URL of the primary property image or a default if none exists"""
        # Check if property has any images
        primary_images = [img for img in self.images if img.is_primary]
        
        if primary_images:
            # Return the first primary image
            return primary_images[0].image_path
        elif self.images:
            # If no primary image but there are images, return the first one
            return self.images[0].image_path
        else:
            # Return a default image if no images exist
            return "/static/img/default-property.jpg"

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
    """
    Room model representing rooms within a property.
    
    Each room belongs to a single property and can have furniture items.
    The relationship with Property is defined through the property_id foreign key
    and accessed via the 'property' backref.
    """
    __tablename__ = 'room'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    room_type = db.Column(db.String(64))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    square_feet = db.Column(db.Integer, nullable=True)
    
    # Bedroom/room-specific fields
    bed_type = db.Column(db.String(50), nullable=True)
    has_tv = db.Column(db.Boolean, default=False)
    tv_details = db.Column(db.String(255), nullable=True)
    has_bathroom = db.Column(db.Boolean, default=False)
    
    # Bathroom-specific fields
    has_shower = db.Column(db.Boolean, default=False)
    has_tub = db.Column(db.Boolean, default=False)
    
    # Relationships
    room_furniture = db.relationship('RoomFurniture', backref='room')
    
    @property
    def furniture(self):
        """Get all furniture items for the room."""
        return self.room_furniture
    
    def __repr__(self):
        return f'<Room {self.name}>'

class RoomFurniture(db.Model):
    __tablename__ = 'room_furniture'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    furniture_type = db.Column(db.String(64))
    quantity = db.Column(db.Integer, default=1)
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
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
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
    
    # Tags for categorizing tasks (e.g., repair_request, workorder, etc.)
    tags = db.Column(db.String(255), nullable=True)
    
    # Fields for repair requests
    location = db.Column(db.String(255), nullable=True)  # Location within property
    severity = db.Column(db.String(50), nullable=True)  # Severity level for repair requests
    
    # Relationships - use task_creator backref instead of creator
    assignments = db.relationship('TaskAssignment', backref='task', lazy='dynamic')
    task_properties = db.relationship('TaskProperty', backref='task', cascade="all, delete-orphan")
    creator = db.relationship('User', 
                            foreign_keys=[creator_id], 
                            back_populates='created_tasks_direct',
                            overlaps="created_tasks,task_creator")
    
    @property
    def properties(self):
        """Get all properties that this task is associated with."""
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
            
    def is_repair_request(self):
        """Check if this task is a repair request"""
        return self.tags and 'repair_request' in self.tags.split(',')
        
    def get_severity_display(self):
        """Return a display-friendly severity name"""
        if not self.severity:
            return None
        return self.severity.replace('_', ' ').title()

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
    sequence_number = db.Column(db.Integer, default=0)  # For ordering tasks within a property
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
    associated_property = db.relationship('Property', foreign_keys=[property_id], backref='cleaning_sessions')
    associated_task = db.relationship('Task', foreign_keys=[task_id], backref='cleaning_sessions')
    
    def __repr__(self):
        if hasattr(self, 'assigned_cleaner') and self.assigned_cleaner:
            cleaner_name = self.assigned_cleaner.get_full_name()
        else:
            cleaner_name = f"User #{self.cleaner_id}"
        
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
    status = db.Column(db.Enum(RepairRequestStatus), default=RepairRequestStatus.PENDING)
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='repair_priority'), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields needed for repair requests
    location = db.Column(db.String(255), nullable=True)
    severity = db.Column(db.Enum(RepairRequestSeverity), default=RepairRequestSeverity.MEDIUM)
    additional_notes = db.Column(db.Text, nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    
    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reported_repairs')
    associated_task = db.relationship('Task', foreign_keys=[task_id], backref='repair_request', uselist=False)
    
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
    catalog_item_id = db.Column(db.Integer, db.ForeignKey('inventory_catalog_item.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    current_quantity = db.Column(db.Float, default=0)
    storage_location = db.Column(db.String(100), nullable=True)
    reorder_threshold = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    catalog_item = db.relationship('InventoryCatalogItem', backref='inventory_instances')
    item_transactions = db.relationship('InventoryTransaction', backref='item')
    
    def __repr__(self):
        return f'<InventoryItem {self.catalog_item.name if self.catalog_item else "Unknown"}>'
    
    def is_low_stock(self):
        """Check if this item is below the reorder threshold"""
        if self.reorder_threshold is None:
            return False
        return self.current_quantity <= self.reorder_threshold
    
    def update_quantity(self, quantity, transaction_type):
        """Update the item quantity based on the transaction type"""
        if transaction_type == TransactionType.RESTOCK:
            self.current_quantity += quantity
        elif transaction_type == TransactionType.USAGE:
            self.current_quantity -= quantity
        elif transaction_type == TransactionType.TRANSFER_OUT:
            self.current_quantity -= quantity
        elif transaction_type == TransactionType.TRANSFER_IN:
            self.current_quantity += quantity
        elif transaction_type == TransactionType.ADJUSTMENT:
            # For adjustments, the quantity is the new total
            self.current_quantity = quantity
        
        # Ensure quantity doesn't go below zero
        if self.current_quantity < 0:
            self.current_quantity = 0
        
        self.updated_at = datetime.utcnow()

class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    previous_quantity = db.Column(db.Float, nullable=True)
    new_quantity = db.Column(db.Float, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    source_property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
    destination_property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='inventory_transactions')
    source_property = db.relationship('Property', foreign_keys=[source_property_id], backref='outgoing_inventory')
    destination_property = db.relationship('Property', foreign_keys=[destination_property_id], backref='incoming_inventory')
    
    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type.value} {self.quantity}>'
        
    def get_transaction_type_display(self):
        """Get a human-readable representation of the transaction type"""
        if self.transaction_type == TransactionType.RESTOCK:
            return "Restock"
        elif self.transaction_type == TransactionType.USAGE:
            return "Usage"
        elif self.transaction_type == TransactionType.TRANSFER_IN:
            return "Transfer In"
        elif self.transaction_type == TransactionType.TRANSFER_OUT:
            return "Transfer Out"
        elif self.transaction_type == TransactionType.ADJUSTMENT:
            return "Adjustment"
        return str(self.transaction_type)

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
    rating = db.Column(db.String(10), nullable=False)  # Changed to String to store 'good', 'ok', 'bad'
    comment = db.Column(db.Text)
    guest_name = db.Column(db.String(100), nullable=False)  # Guest name if not tied to a user
    check_in_date = db.Column(db.Date, nullable=False)  # Added check_in_date
    check_out_date = db.Column(db.Date, nullable=False)  # Added check_out_date
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property_rel = db.relationship('Property', backref='guest_reviews')
    creator = db.relationship('User', foreign_keys=[creator_id], backref='submitted_reviews')
    
    def __repr__(self):
        return f'<GuestReview {self.guest_name} - {self.rating}>'
        
    def get_rating_display(self):
        """Get a human-readable representation of the rating"""
        return self.rating.upper()
            
    @property
    def is_negative(self):
        """Check if this is a negative review"""
        return self.rating == 'bad'

class SiteSetting(db.Model):
    """Model for storing site-wide settings"""
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
    if not db.session.get(SiteSetting, 'guest_reviews_enabled'):
        SiteSetting.set_setting('guest_reviews_enabled', 'true', 'Enable guest reviews feature', True)
    
    # Set placeholder for OpenAI API key
    if not db.session.get(SiteSetting, 'openai_api_key'):
        SiteSetting.set_setting('openai_api_key', '', 'OpenAI API Key for AI functionality', False)

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

class AdminAction(db.Model):
    """Model for tracking administrative actions"""
    __tablename__ = 'admin_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # e.g. 'delete_account', 'reset_password', 'suspend_account', 'reactivate_account', 'resend_invite'
    action_details = db.Column(db.Text, nullable=True)  # Additional details about the action
    ip_address = db.Column(db.String(45), nullable=True)  # IP address of the admin performing the action
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    admin = db.relationship('User', foreign_keys=[admin_id], backref='admin_actions')
    target_user = db.relationship('User', foreign_keys=[target_user_id], backref='admin_action_targets')
    
    def __repr__(self):
        return f'<AdminAction {self.action_type} by {self.admin_id} on {self.target_user_id}>'

class RecommendationCategory(enum.Enum):
    FOOD = "food"
    OUTDOORS = "outdoors"
    SHOPPING = "shopping"
    ATTRACTIONS = "attractions"
    GROCERY = "grocery"
    OTHER = "other"

class RecommendationVote(db.Model):
    """Model for storing recommendation votes from guests"""
    __tablename__ = 'recommendation_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendation_blocks.id'), nullable=False)
    guest_token = db.Column(db.String(64), nullable=False)  # Unique token per guest stay
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    recommendation = db.relationship('RecommendationBlock', backref='votes')
    
    def __repr__(self):
        return f'<RecommendationVote for recommendation {self.recommendation_id}>'

class RecommendationBlock(db.Model):
    """Model for storing location-based recommendations"""
    __tablename__ = 'recommendation_blocks'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)  # 300-char limit enforced in form
    category = db.Column(db.String(20), nullable=False)  # Store enum as string in SQLite
    map_link = db.Column(db.String(500), nullable=False)
    best_time_to_go = db.Column(db.String(255), nullable=True)
    recommended_meal = db.Column(db.String(255), nullable=True)  # For food recommendations
    wifi_name = db.Column(db.String(255), nullable=True)  # WiFi network name (SSID)
    wifi_password = db.Column(db.String(255), nullable=True)  # WiFi password if available
    parking_details = db.Column(db.Text, nullable=True)  # Parking information
    in_guide_book = db.Column(db.Boolean, default=False)  # Whether this recommendation is in the guide book
    photo_path = db.Column(db.String(500), nullable=True)
    staff_pick = db.Column(db.Boolean, default=False)  # Whether this is marked as a staff pick
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - rename property to associated_property
    # associated_property = db.relationship('Property', backref='recommendations')
    
    def __repr__(self):
        return f'<RecommendationBlock {self.title} for Property {self.property_id}>'
    
    def get_category_display(self):
        return self.category.title()
    
    @property
    def photo_url(self):
        if self.photo_path:
            return url_for('static', filename=f'recommendations/{self.photo_path}')
        return None
    
    @property
    def vote_count(self):
        """Get the total number of votes for this recommendation"""
        return len(self.votes)
    
    def has_voted(self, guest_token):
        """Check if a guest has already voted for this recommendation"""
        return any(vote.guest_token == guest_token for vote in self.votes)
    
    def toggle_vote(self, guest_token):
        """Toggle a vote for this recommendation"""
        existing_vote = RecommendationVote.query.filter_by(
            recommendation_id=self.id,
            guest_token=guest_token
        ).first()
        
        if existing_vote:
            db.session.delete(existing_vote)
            db.session.commit()
            return False
        else:
            vote = RecommendationVote(
                recommendation_id=self.id,
                guest_token=guest_token
            )
            db.session.add(vote)
            db.session.commit()
            return True

    def is_in_guide_book(self, guide_book_id=None):
        """Check if recommendation is in a specific guide book or any guide book"""
        if guide_book_id:
            return any(gb.id == guide_book_id for gb in self.guide_books)
        return len(self.guide_books) > 0

class GuideBook(db.Model):
    """Model for property guide books"""
    __tablename__ = 'guide_books'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    access_token = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    
    # Relationships
    # associated_property = db.relationship('Property', backref=db.backref('guide_books', lazy=True))
    recommendations = db.relationship('RecommendationBlock', 
                                   secondary='guide_book_recommendations',
                                   backref=db.backref('guide_books', lazy=True))

    def __repr__(self):
        return f'<GuideBook {self.name}>'

    @property
    def recommendations_count(self):
        return len(self.recommendations)

    def generate_access_token(self):
        """Generate a unique token for public access."""
        if not self.access_token and self.is_public:
            self.access_token = secrets.token_urlsafe(32)
            db.session.commit()
        return self.access_token

    def ensure_access_token(self):
        """Ensure the guide book has an access token if it's public."""
        if self.is_public and not self.access_token:
            return self.generate_access_token()
        return self.access_token

# Association table for guide books and recommendations
guide_book_recommendations = db.Table('guide_book_recommendations',
    db.Column('guide_book_id', db.Integer, db.ForeignKey('guide_books.id'), primary_key=True),
    db.Column('recommendation_id', db.Integer, db.ForeignKey('recommendation_blocks.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Booking(db.Model):
    """Model for property bookings/calendar events."""
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    calendar_id = db.Column(db.Integer, db.ForeignKey('property_calendar.id'), nullable=False)
    external_id = db.Column(db.String(255))  # ID from external calendar if available
    title = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    guest_name = db.Column(db.String(255))
    guest_phone = db.Column(db.String(50))
    amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(50), default='Confirmed')
    source_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    room_name = db.Column(db.String(255))
    is_entire_property = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = db.Column(db.DateTime)
    
    # Relationships - REMOVE associated_property and property_bookings
    # associated_property = db.relationship('Property', backref=db.backref('property_bookings', lazy=True))
    calendar = db.relationship('PropertyCalendar', backref=db.backref('calendar_bookings', lazy=True))
    tasks = db.relationship('BookingTask', backref='parent_booking', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Convert booking to dictionary for calendar display."""
        return {
            'id': self.id,
            'title': self.title,
            'start': self.start_date.isoformat(),
            'end': (self.end_date + timedelta(days=1)).isoformat(),  # FullCalendar uses exclusive end dates
            'resourceId': str(self.property_id),
            'className': f'{self.calendar.service.lower()}-event',
            'extendedProps': {
                'property_name': self.property.name,  # Use self.property
                'property_id': self.property_id,
                'service': self.calendar.get_service_display(),
                'room': None if self.is_entire_property else self.room_name,
                'guest_name': self.guest_name,
                'amount': float(self.amount) if self.amount else None,
                'source_url': self.source_url,
                'status': self.status,
                'notes': self.notes,
                'phone': self.guest_phone
            }
        }

class BookingTask(db.Model):
    """Model for tasks associated with bookings."""
    __tablename__ = 'booking_task'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Fix: Change 'user.id' to 'users.id'
    task_type = db.Column(db.String(50), nullable=False)  # e.g., 'cleaning', 'maintenance', 'check-in'
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed, cancelled
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - fix backref names
    assigned_to = db.relationship('User', backref=db.backref('assigned_booking_tasks', lazy=True))

    def to_dict(self):
        """Convert task to dictionary for display."""
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'task_type': self.task_type,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'assigned_to': self.assigned_to.get_full_name() if self.assigned_to else None,
            'notes': self.notes
        }