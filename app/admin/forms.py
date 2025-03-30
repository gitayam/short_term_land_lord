from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import Optional, Length

class SiteSettingsForm(FlaskForm):
    # AI Features
    openai_api_key = StringField('OpenAI API Key', validators=[Optional(), Length(max=255)],
                               description="API key for OpenAI services (keep this secure)")
    
    # Feature toggles
    enable_guest_reviews = BooleanField('Enable Guest Reviews', default=False,
                                       description="Allow property owners and managers to add guest reviews")
    
    submit = SubmitField('Save Settings') 