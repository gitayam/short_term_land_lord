from datetime import datetime, timedelta
import enum
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class UserRoles(enum.Enum):
    PROPERTY_OWNER = "property_owner"
    CLEANER = "cleaner"
    MAINTENANCE = "maintenance"

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

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
