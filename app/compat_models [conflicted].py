"""
Compatibility models for database transitions
These models are designed to work with both old and new database schemas
"""
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from app import db
from app.models import UserRoles

# Create a Base class for compatibility models
Base = declarative_base()

class CompatUser(UserMixin, Base):
    """User model compatible with both old and new schema"""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(512))
    role = Column(Enum(UserRoles), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # The following columns might not exist in older database versions
    # We'll access these with getattr() to avoid attribute errors
    authentik_id = Column(String(64), nullable=True)
    signal_identity = Column(String(64), nullable=True)
    attributes = Column(Text, nullable=True)  # Store as JSON text
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    date_joined = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def is_property_owner(self):
        return self.role == UserRoles.PROPERTY_OWNER

    def is_property_manager(self):
        return self.role == UserRoles.PROPERTY_MANAGER

    def is_service_staff(self):
        return self.role == UserRoles.SERVICE_STAFF

    def is_admin(self):
        # Check the is_admin column first if it exists
        admin_flag = getattr(self, 'is_admin', None)
        if admin_flag is not None:
            return admin_flag
        # Fall back to role check
        return self.role == UserRoles.ADMIN

def get_user_search_query(search_term):
    """Create a search query that works with both database schemas"""
    from sqlalchemy import or_
    from sqlalchemy.sql import text

    # Start with basic fields that exist in all versions
    basic_query = or_(
        CompatUser.first_name.ilike(f'%{search_term}%'),
        CompatUser.last_name.ilike(f'%{search_term}%'),
        CompatUser.email.ilike(f'%{search_term}%')
    )

    # Try a direct query first to see what columns exist
    try:
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]

        # Build a more complete query based on available columns
        query_parts = [basic_query]

        # For attributes, we need different syntax for SQLite vs PostgreSQL
        if 'attributes' in columns:
            # We'll handle this separately in the function that calls this
            # as it needs different SQL syntax for each database type
            pass

        return or_(*query_parts)

    except Exception:
        # If any error, just return the basic query
        return basic_query

def compatible_user_search(search_term):
    """Perform a user search that works with both database schemas"""
    from sqlalchemy import text

    # Create a session with our Base
    from sqlalchemy.orm import Session
    session = Session(db.engine)

    try:
        # Get the query filters based on available columns
        query_filter = get_user_search_query(search_term)

        # Execute the query with our compatible model
        users = session.query(CompatUser).filter(query_filter).all()

        # If attributes search is needed for PostgreSQL, we'll do that in separate raw SQL
        # because the syntax is very different between SQLite and PostgreSQL

        return users
    finally:
        session.close()

def get_user_by_id(user_id):
    """Get a user by ID using the compatible model"""
    from sqlalchemy.orm import Session
    session = Session(db.engine)
    try:
        return session.query(CompatUser).get(user_id)
    finally:
        session.close()

def get_user_by_email(email):
    """Get a user by email using the compatible model"""
    from sqlalchemy.orm import Session
    session = Session(db.engine)
    try:
        return session.query(CompatUser).filter(CompatUser.email == email).first()
    finally:
        session.close()