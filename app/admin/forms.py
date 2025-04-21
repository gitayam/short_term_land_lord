from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, SelectField
from wtforms.validators import Optional, Length, DataRequired

class SiteSettingsForm(FlaskForm):
    """Form for managing site settings"""
    # AI Features
    openai_api_key = StringField('OpenAI API Key', validators=[Optional(), Length(max=255)],
                               description="API key for OpenAI services (keep this secure)")
    
    # Feature toggles
    enable_guest_reviews = BooleanField('Enable Guest Reviews', default=False,
                                       description="Allow property owners and managers to add guest reviews")
    
    submit = SubmitField('Save Settings')

class RequestReviewForm(FlaskForm):
    """Form for reviewing registration requests"""
    notes = TextAreaField('Admin Notes', validators=[Optional(), Length(max=1000)],
                         description="Internal notes about this request")
    action = SelectField('Action', choices=[
        ('approve', 'Approve Request'),
        ('reject', 'Reject Request')
    ], validators=[DataRequired()])
    rejection_reason = TextAreaField('Rejection Reason', validators=[Optional(), Length(max=1000)],
                                    description="Reason for rejection (will be sent to applicant)")
    submit = SubmitField('Submit Review') 