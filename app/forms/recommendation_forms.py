from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FileField, BooleanField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, URL, Optional
from app.models import RecommendationCategory

class RecommendationBlockForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=300)])
    category = SelectField('Category', choices=[
        ('food', 'Food & Dining'),
        ('outdoors', 'Outdoors & Recreation'),
        ('shopping', 'Shopping'),
        ('attractions', 'Attractions'),
        ('grocery', 'Grocery Stores'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    map_link = StringField('Map Link', validators=[DataRequired(), URL()])
    best_time_to_go = StringField('Best Time to Go', validators=[Optional(), Length(max=255)])
    recommended_meal = StringField('Recommended Meal', validators=[Optional(), Length(max=255)])
    wifi_name = StringField('WiFi Network Name', validators=[Optional(), Length(max=255)])
    wifi_password = StringField('WiFi Password', validators=[Optional(), Length(max=255)])
    parking_details = TextAreaField('Parking Details', validators=[Optional()])
    hours = StringField('Hours', validators=[Optional(), Length(max=255)])
    guide_books = SelectMultipleField('Add to Guide Books', coerce=int)
    photo = FileField('Photo')
    add_to_guide = BooleanField('Add to Property Guide Book', default=False)
    
    def validate_description(self, field):
        if len(field.data) > 300:
            raise ValidationError('Description must be 300 characters or less')

class GuideBookForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Make Public', default=True)
    property_id = HiddenField('Property ID', validators=[DataRequired()]) 