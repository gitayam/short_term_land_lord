from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, BooleanField, TextAreaField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.models import User, Property, ServiceType, UserRoles


class WorkerInvitationForm(FlaskForm):
    """Form for inviting new service staff"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    service_type = SelectField('Service Type', choices=[(t.value, t.name) for t in ServiceType], validators=[DataRequired()])
    message = TextAreaField('Invitation Message', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Send Invitation')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email address is already registered. Please use a different email.')


class WorkerPropertyAssignmentForm(FlaskForm):
    """Form for assigning workers to properties"""
    worker = QuerySelectField('Worker', query_factory=lambda: User.query.filter_by(role=UserRoles.SERVICE_STAFF), 
                             get_label='get_full_name', allow_blank=True, blank_text='Select a worker...')
    properties = QuerySelectMultipleField('Properties', query_factory=lambda: Property.query.all(),
                                        get_label='name')
    service_type = SelectField('Service Type', choices=[(t.value, t.name) for t in ServiceType], validators=[DataRequired()])
    submit = SubmitField('Assign Properties')


class WorkerFilterForm(FlaskForm):
    """Form for filtering workers"""
    service_type = SelectField('Service Type', choices=[('', 'All')] + [(t.value, t.name) for t in ServiceType], validators=[Optional()])
    property_id = SelectField('Property', coerce=int, validators=[Optional()])
    search = StringField('Search', validators=[Optional()])
    submit = SubmitField('Filter')
