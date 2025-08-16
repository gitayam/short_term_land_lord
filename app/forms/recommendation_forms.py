from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, BooleanField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, URL, Optional, ValidationError
from app.models import RecommendationCategory

class RecommendationBlockForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    
    # Recommendation type - determines which fields are shown
    recommendation_type = SelectField('Type', choices=[
        ('place', 'Place'),
        ('activity', 'Activity'),
        ('service', 'Service'),
        ('event', 'Event'),
        ('transportation', 'Transportation'),
        ('shopping', 'Shopping'),
        ('emergency', 'Emergency')
    ], validators=[DataRequired()], default='place')
    
    category = SelectField('Category', choices=[
        ('food', 'Food & Dining'),
        ('outdoors', 'Outdoors & Recreation'),
        ('shopping', 'Shopping'),
        ('attractions', 'Attractions'),
        ('grocery', 'Grocery Stores'),
        ('services', 'Services'),
        ('transportation', 'Transportation'),
        ('emergency', 'Emergency'),
        ('other', 'Other')
    ], validators=[Optional()])
    
    # Core fields (commonly used)
    map_link = StringField('Map Link', validators=[Optional(), URL(), Length(max=500)])
    hours = StringField('Hours of Operation', validators=[Optional(), Length(max=255)])
    price_range = StringField('Price Range', validators=[Optional(), Length(max=50)])
    
    # Location/distance fields
    distance_from_property = StringField('Distance from Property', validators=[Optional(), Length(max=50)])
    
    # Place-specific fields
    best_time_to_go = StringField('Best Time to Visit', validators=[Optional(), Length(max=255)])
    recommended_meal = StringField('Recommended Dish/Item', validators=[Optional(), Length(max=255)])
    parking_details = TextAreaField('Parking Information', validators=[Optional(), Length(max=500)])
    
    # Service/WiFi fields (backward compatibility)
    wifi_name = StringField('WiFi Network Name', validators=[Optional(), Length(max=255)])
    wifi_password = StringField('WiFi Password', validators=[Optional(), Length(max=255)])
    
    # File and organization
    photo = FileField('Photo')
    guide_books = SelectMultipleField('Add to Guide Books', coerce=int)
    add_to_guide = BooleanField('Add to Property Guide Book', default=False)
    
    def validate_description(self, field):
        if field.data and len(field.data) > 500:
            raise ValidationError('Description must be 500 characters or less')

class GuideBookForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Make Public', default=True)
    property_id = HiddenField('Property ID', validators=[DataRequired()]) 