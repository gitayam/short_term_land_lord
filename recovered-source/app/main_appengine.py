"""
Short Term Landlord - App Engine Entry Point
Streamlined version with essential features for cloud deployment
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_mail import Mail
from wtforms import StringField, TextAreaField, SelectField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'landlord-app-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///landlord.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_property_owner = db.Column(db.Boolean, default=False)
    is_property_manager = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    property_type = db.Column(db.String(50), nullable=False)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    checkin_time = db.Column(db.String(20), default='3:00 PM')
    checkout_time = db.Column(db.String(20), default='11:00 AM')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    guest_access_token = db.Column(db.String(64), unique=True)
    worker_calendar_token = db.Column(db.String(64), unique=True)
    guest_access_enabled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def generate_guest_access_token(self):
        self.guest_access_token = secrets.token_urlsafe(32)
        
    def generate_worker_calendar_token(self):
        self.worker_calendar_token = secrets.token_urlsafe(32)

class GuidebookEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    address = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    phone = db.Column(db.String(20))
    website = db.Column(db.String(200))
    hours = db.Column(db.String(200))
    price_range = db.Column(db.String(20))
    rating = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    guest_name = db.Column(db.String(200), nullable=False)
    guest_email = db.Column(db.String(200))
    guest_phone = db.Column(db.String(20))
    checkin_date = db.Column(db.Date, nullable=False)
    checkout_date = db.Column(db.Date, nullable=False)
    number_of_guests = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class PropertyForm(FlaskForm):
    name = StringField('Property Name', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    description = TextAreaField('Description')
    property_type = SelectField('Type', choices=[('house', 'House'), ('apartment', 'Apartment'), ('condo', 'Condo')])
    bedrooms = SelectField('Bedrooms', choices=[(str(i), str(i)) for i in range(1, 11)], coerce=int)
    bathrooms = SelectField('Bathrooms', choices=[(str(i), str(i)) for i in range(1, 6)], coerce=int)
    submit = SubmitField('Save Property')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
        return render_template('dashboard.html', properties=properties)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_property_owner=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/properties')
@login_required
def properties():
    properties = Property.query.filter_by(owner_id=current_user.id).all()
    return render_template('properties.html', properties=properties)

@app.route('/property/new', methods=['GET', 'POST'])
@login_required
def new_property():
    form = PropertyForm()
    if form.validate_on_submit():
        property = Property(
            name=form.name.data,
            address=form.address.data,
            description=form.description.data,
            property_type=form.property_type.data,
            bedrooms=form.bedrooms.data,
            bathrooms=form.bathrooms.data,
            owner_id=current_user.id
        )
        property.generate_guest_access_token()
        property.generate_worker_calendar_token()
        property.guest_access_enabled = True
        
        db.session.add(property)
        db.session.commit()
        flash('Property added successfully!')
        return redirect(url_for('properties'))
    
    return render_template('property_form.html', form=form, title='Add New Property')

@app.route('/property/<int:property_id>')
@login_required
def view_property(property_id):
    property = Property.query.get_or_404(property_id)
    if property.owner_id != current_user.id:
        flash('Access denied.')
        return redirect(url_for('properties'))
    
    bookings = Booking.query.filter_by(property_id=property_id).order_by(Booking.checkin_date.desc()).limit(10).all()
    return render_template('property_detail.html', property=property, bookings=bookings)

@app.route('/worker-calendar/<token>')
def worker_calendar(token):
    property = Property.query.filter_by(worker_calendar_token=token).first_or_404()
    
    # Get upcoming bookings for the next 4 weeks
    start_date = datetime.now().date()
    end_date = start_date + timedelta(weeks=4)
    
    bookings = Booking.query.filter(
        Booking.property_id == property.id,
        Booking.checkout_date >= start_date,
        Booking.checkin_date <= end_date
    ).order_by(Booking.checkin_date).all()
    
    return render_template('worker_calendar.html', property=property, bookings=bookings)

@app.route('/guest/<int:property_id>/guidebook')
def guest_guidebook(property_id):
    token = request.args.get('token')
    property = Property.query.get_or_404(property_id)
    
    if not property.guest_access_enabled or property.guest_access_token != token:
        return jsonify({'error': 'Invalid access token'}), 403
    
    guidebook_entries = GuidebookEntry.query.filter_by(property_id=property_id).all()
    categories = list(set([entry.category for entry in guidebook_entries]))
    
    return render_template('guest_guidebook.html', property=property, entries=guidebook_entries, categories=categories)

@app.route('/health')
def health_check():
    """Health check endpoint for App Engine"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return {
            'status': 'healthy',
            'service': 'short-term-landlord',
            'version': '1.0.0',
            'features': [
                'Property Management',
                'Guest Guidebooks',
                'Worker Calendar Access',
                'User Authentication',
                'Booking Management'
            ]
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }, 500

@app.route('/service-info')
def service_info():
    """Service information endpoint"""
    return {
        'service_name': 'Short Term Landlord',
        'service_id': 'short-term-landlord',
        'deployment': 'Google App Engine Service',
        'project': os.environ.get('GOOGLE_CLOUD_PROJECT_ID', 'speech-memorization'),
        'version': '1.0.0',
        'features': {
            'property_management': True,
            'guest_guidebooks': True,
            'worker_calendar': True,
            'user_authentication': True,
            'booking_management': True,
            'mobile_responsive': True
        },
        'endpoints': {
            '/': 'Dashboard (authenticated)',
            '/login': 'User login',
            '/register': 'User registration',
            '/properties': 'Property listing',
            '/worker-calendar/<token>': 'Worker calendar view',
            '/guest/<id>/guidebook': 'Guest guidebook',
            '/health': 'Health check',
            '/service-info': 'Service information'
        }
    }

# Initialize database and create admin user
@app.before_first_request
def create_tables():
    """Create database tables and admin user"""
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@landlord-app.com',
            first_name='System',
            last_name='Administrator',
            is_admin=True,
            is_property_owner=True,
            is_property_manager=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create sample property
        sample_property = Property(
            name='Sample Property',
            address='123 Main St, Anytown, USA',
            description='A beautiful sample property for demonstration',
            property_type='house',
            bedrooms=3,
            bathrooms=2,
            owner_id=1
        )
        sample_property.generate_guest_access_token()
        sample_property.generate_worker_calendar_token()
        sample_property.guest_access_enabled = True
        
        db.session.add(sample_property)
        
        # Add sample guidebook entries
        categories = ['restaurants', 'attractions', 'shopping', 'transportation']
        sample_entries = [
            {
                'title': 'Downtown Bistro',
                'description': 'Great local restaurant with amazing steaks',
                'category': 'restaurants',
                'address': '456 Food St',
                'phone': '(555) 123-4567'
            },
            {
                'title': 'City Museum',
                'description': 'Fascinating local history and art exhibits',
                'category': 'attractions',
                'address': '789 Culture Ave',
                'phone': '(555) 987-6543'
            }
        ]
        
        for entry_data in sample_entries:
            entry = GuidebookEntry(property_id=1, **entry_data)
            db.session.add(entry)
        
        # Add sample booking
        sample_booking = Booking(
            property_id=1,
            guest_name='John Doe',
            guest_email='john@example.com',
            checkin_date=datetime.now().date() + timedelta(days=1),
            checkout_date=datetime.now().date() + timedelta(days=4),
            number_of_guests=2
        )
        db.session.add(sample_booking)
        
        db.session.commit()
        app.logger.info('Sample data created - Admin user: admin/admin123')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)