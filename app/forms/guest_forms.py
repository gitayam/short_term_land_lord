"""
Forms for guest invitation and registration functionality
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, BooleanField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, NumberRange, ValidationError
from wtforms.widgets import DateInput
from datetime import datetime, timedelta
from app.models import User, GuestInvitation


class GuestInvitationForm(FlaskForm):
    """Form for creating guest invitation codes"""
    property_id = SelectField('Property (Optional)', coerce=int, validators=[Optional()])
    email = StringField('Guest Email (Optional)', validators=[Optional(), Email(), Length(max=120)])
    guest_name = StringField('Guest Name (Optional)', validators=[Optional(), Length(max=200)])
    expires_in_days = IntegerField('Expires in Days', default=30, 
                                  validators=[DataRequired(), NumberRange(min=1, max=365)])
    max_uses = IntegerField('Maximum Uses', default=1, 
                           validators=[DataRequired(), NumberRange(min=1, max=50)])
    notes = TextAreaField('Internal Notes (Optional)', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super(GuestInvitationForm, self).__init__(*args, **kwargs)
        # Property choices will be populated in the route
        self.property_id.choices = [(0, 'All Properties')] 


class GuestRegistrationForm(FlaskForm):
    """Form for guest account registration using invitation code"""
    invitation_code = StringField('Invitation Code', 
                                 validators=[DataRequired(), Length(min=5, max=24)],
                                 render_kw={"placeholder": "Enter your invitation code"})
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', 
                            validators=[DataRequired(), Length(min=8, max=128)])
    password_confirm = PasswordField('Confirm Password',
                                    validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Phone Number (Optional)', validators=[Optional(), Length(max=20)])
    
    # Consent fields
    marketing_emails_consent = BooleanField('I would like to receive marketing emails about special offers')
    booking_reminders_consent = BooleanField('I would like to receive booking reminders and important updates', 
                                           default=True)
    
    def validate_invitation_code(self, field):
        """Validate that the invitation code exists and is valid"""
        invitation = GuestInvitation.get_by_code(field.data)
        if not invitation:
            raise ValidationError('Invalid invitation code.')
        if not invitation.is_available:
            if invitation.is_expired:
                raise ValidationError('This invitation code has expired.')
            else:
                raise ValidationError('This invitation code has already been used.')
    
    def validate_email(self, field):
        """Validate that email is not already registered"""
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('An account with this email already exists.')


class GuestProfileForm(FlaskForm):
    """Form for guest profile management"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=64)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    
    # Preferences
    timezone = SelectField('Timezone', choices=[
        ('UTC', 'UTC'),
        ('US/Eastern', 'Eastern Time'),
        ('US/Central', 'Central Time'),
        ('US/Mountain', 'Mountain Time'),
        ('US/Pacific', 'Pacific Time'),
    ], default='UTC')
    
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
    ], default='en')
    
    theme_preference = SelectField('Theme', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ], default='light')
    
    # Communication preferences
    marketing_emails_consent = BooleanField('Receive marketing emails')
    booking_reminders_consent = BooleanField('Receive booking reminders')
    email_notifications = BooleanField('Email notifications', default=True)


class DirectBookingForm(FlaskForm):
    """Form for guests to make direct bookings"""
    property_id = SelectField('Property', coerce=int, validators=[DataRequired()])
    check_in_date = DateField('Check-in Date', 
                             validators=[DataRequired()],
                             widget=DateInput())
    check_out_date = DateField('Check-out Date', 
                              validators=[DataRequired()],
                              widget=DateInput())
    guest_count = IntegerField('Number of Guests', 
                              default=1, 
                              validators=[DataRequired(), NumberRange(min=1, max=20)])
    special_requests = TextAreaField('Special Requests (Optional)', 
                                   validators=[Optional(), Length(max=1000)])
    
    def validate_check_in_date(self, field):
        """Validate check-in date is not in the past"""
        if field.data < datetime.now().date():
            raise ValidationError('Check-in date cannot be in the past.')
    
    def validate_check_out_date(self, field):
        """Validate check-out date is after check-in date"""
        if hasattr(self, 'check_in_date') and self.check_in_date.data:
            if field.data <= self.check_in_date.data:
                raise ValidationError('Check-out date must be after check-in date.')


class GuestInvitationManagementForm(FlaskForm):
    """Form for managing existing guest invitations"""
    extend_days = IntegerField('Extend Expiration by Days', 
                              validators=[Optional(), NumberRange(min=1, max=365)])
    deactivate = BooleanField('Deactivate Invitation')
    notes = TextAreaField('Update Notes', validators=[Optional(), Length(max=500)])


class BulkInvitationForm(FlaskForm):
    """Form for creating multiple guest invitations at once"""
    property_id = SelectField('Property (Optional)', coerce=int, validators=[Optional()])
    guest_emails = TextAreaField('Guest Emails (One per line)', 
                                validators=[DataRequired()],
                                render_kw={"placeholder": "email1@example.com\nemail2@example.com\nemail3@example.com"})
    expires_in_days = IntegerField('Expires in Days', default=30, 
                                  validators=[DataRequired(), NumberRange(min=1, max=365)])
    notes = TextAreaField('Internal Notes (Optional)', validators=[Optional(), Length(max=500)])
    
    def validate_guest_emails(self, field):
        """Validate that all emails are valid"""
        emails = [email.strip() for email in field.data.split('\n') if email.strip()]
        
        if len(emails) == 0:
            raise ValidationError('At least one email address is required.')
        
        if len(emails) > 50:
            raise ValidationError('Maximum 50 email addresses allowed.')
        
        # Validate each email format
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        invalid_emails = []
        for email in emails:
            if not email_pattern.match(email):
                invalid_emails.append(email)
        
        if invalid_emails:
            raise ValidationError(f'Invalid email addresses: {", ".join(invalid_emails)}')


class PropertyBrowseFilterForm(FlaskForm):
    """Form for filtering properties in public browse view"""
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = SelectField('State', choices=[('', 'All States')] + [
        ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
        ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
        ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
        ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
        ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
        ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
        ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
        ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
        ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
        ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
        ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
        ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'), ('WY', 'Wyoming')
    ], validators=[Optional()])
    
    property_type = SelectField('Property Type', choices=[
        ('', 'All Types'),
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condo'),
        ('studio', 'Studio'),
        ('suite', 'Suite'),
        ('other', 'Other')
    ], validators=[Optional()])
    
    min_bedrooms = SelectField('Minimum Bedrooms', choices=[
        ('', 'Any'),
        ('1', '1+'),
        ('2', '2+'),
        ('3', '3+'),
        ('4', '4+'),
        ('5', '5+')
    ], validators=[Optional()])


class EmailVerificationForm(FlaskForm):
    """Form for email verification token input"""
    token = StringField('Verification Code', 
                       validators=[DataRequired(), Length(min=5, max=64)],
                       render_kw={"placeholder": "Enter the verification code from your email"})


class PasswordResetRequestForm(FlaskForm):
    """Form for requesting password reset for guest accounts"""
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    
    def validate_email(self, field):
        """Validate that email belongs to a guest user"""
        user = User.query.filter_by(email=field.data).first()
        if not user:
            raise ValidationError('No account found with this email address.')
        if not user.is_guest_user:
            raise ValidationError('This email is not associated with a guest account.')


class PasswordResetForm(FlaskForm):
    """Form for resetting password with token"""
    password = PasswordField('New Password', 
                            validators=[DataRequired(), Length(min=8, max=128)])
    password_confirm = PasswordField('Confirm New Password',
                                    validators=[DataRequired(), EqualTo('password')])
    token = StringField('Reset Token', validators=[DataRequired()])