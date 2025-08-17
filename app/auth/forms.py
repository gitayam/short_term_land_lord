from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[Optional(), Length(max=64)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[
        ('property_owner', 'Property Owner'),
        ('service_staff', 'Service Staff'),
        ('property_manager', 'Property Manager'),
        ('guest', 'Guest (with invitation code)')
    ], validators=[DataRequired()])
    invitation_code = StringField('Invitation Code', 
                                validators=[Optional(), Length(min=5, max=24)],
                                description="Required for guest registration")
    message = TextAreaField('Why do you want to join?', 
                         validators=[Length(max=500)],
                         description="Tell us a bit about yourself and why you want to join the platform")
    submit = SubmitField('Request Registration')
    
    def validate_invitation_code(self, field):
        if self.role.data == 'guest':
            if not field.data:
                raise ValidationError('Invitation code is required for guest registration.')
            
            # Import here to avoid circular imports
            from app.models import GuestInvitation
            invitation = GuestInvitation.query.filter_by(
                invitation_code=field.data,
                is_active=True,
                is_used=False
            ).first()
            
            if not invitation:
                raise ValidationError('Invalid or expired invitation code.')
            
            if invitation.is_expired():
                raise ValidationError('This invitation code has expired.')
    
    def validate_message(self, field):
        # Message is required for non-guest roles
        if self.role.data != 'guest' and not field.data:
            raise ValidationError('Please tell us why you want to join the platform.')

class PropertyRegistrationForm(FlaskForm):
    """Form for adding property details during registration"""
    property_name = StringField('Property Name', validators=[DataRequired()])
    property_address = StringField('Property Address', validators=[DataRequired()])
    property_description = TextAreaField('Property Description', 
                                      validators=[Length(max=1000)])
    submit = SubmitField('Continue with Registration')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class SSOLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Continue with SSO')

class InviteServiceStaffForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    message = TextAreaField('Invitation Message', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Send Invitation') 