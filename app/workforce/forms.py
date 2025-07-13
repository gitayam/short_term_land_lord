from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, BooleanField, TextAreaField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.models import User, Property, ServiceType, UserRoles

# List of country codes with their phone prefixes
COUNTRY_CODES = [
    ('US', '+1 (USA)'),
    ('CA', '+1 (Canada)'),
    ('GB', '+44 (UK)'),
    ('AU', '+61 (Australia)'),
    ('NZ', '+64 (New Zealand)'),
    ('IN', '+91 (India)'),
    ('PH', '+63 (Philippines)'),
    ('MX', '+52 (Mexico)'),
    ('BR', '+55 (Brazil)'),
    ('DE', '+49 (Germany)'),
    ('FR', '+33 (France)'),
    ('IT', '+39 (Italy)'),
    ('ES', '+34 (Spain)'),
    ('JP', '+81 (Japan)'),
    ('CN', '+86 (China)'),
    ('KR', '+82 (South Korea)'),
    ('SG', '+65 (Singapore)'),
    ('AE', '+971 (UAE)'),
    ('SA', '+966 (Saudi Arabia)'),
    ('ZA', '+27 (South Africa)'),
]

class WorkerInvitationForm(FlaskForm):
    """Form for inviting new service staff"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    country_code = SelectField('Country Code', choices=COUNTRY_CODES, default='US')
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    send_email = BooleanField('Send via Email', default=True)
    send_sms = BooleanField('Send via SMS', default=True)
    service_type = SelectField('Service Type', choices=[(t.value, t.name) for t in ServiceType], validators=[DataRequired()])
    message = TextAreaField('Invitation Message', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Send Invitation')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email address is already registered. Please use a different email.')
            
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
            
        # At least one delivery method must be selected
        if not self.send_email.data and not self.send_sms.data:
            self.send_email.errors.append('At least one delivery method must be selected')
            return False
            
        # If SMS is selected, phone number is required
        if self.send_sms.data and not self.phone.data:
            self.phone.errors.append('Phone number is required when sending via SMS')
            return False
            
        return True


class WorkerPropertyAssignmentForm(FlaskForm):
    """Form for assigning workers to properties"""
    worker = QuerySelectField('Worker', query_factory=lambda: User.query.filter_by(role=UserRoles.SERVICE_STAFF.value),
                            get_label='get_full_name', allow_blank=True, blank_text='Select a worker...',
                            validators=[DataRequired(message='Please select a worker')])
    properties = QuerySelectMultipleField('Properties', query_factory=lambda: Property.query.all(),
                                        get_label='name', validators=[DataRequired(message='Please select at least one property')])
    service_type = SelectField('Service Type', choices=[(t.value, t.name) for t in ServiceType], 
                             validators=[DataRequired()], coerce=lambda x: ServiceType(x))
    submit = SubmitField('Assign Properties')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # Ensure worker is selected
        if not self.worker.data:
            self.worker.errors.append('Please select a worker to assign properties to.')
            return False
        
        # Ensure at least one property is selected
        if not self.properties.data:
            self.properties.errors.append('Please select at least one property to assign.')
            return False
        
        return True


class WorkerFilterForm(FlaskForm):
    """Form for filtering workers"""
    service_type = SelectField('Service Type', choices=[('', 'All')] + [(t.value, t.name) for t in ServiceType], 
                             validators=[Optional()], coerce=lambda x: ServiceType(x) if x else None)
    property_id = SelectField('Property', coerce=int, validators=[Optional()])
    search = StringField('Search', validators=[Optional()])
    submit = SubmitField('Filter')
