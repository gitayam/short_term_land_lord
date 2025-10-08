from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, FloatField, URLField, EmailField
from wtforms.validators import DataRequired, Optional, Email, URL, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed

SECTION_TYPES = [
    ('house_rules', 'House Rules'),
    ('check_in', 'Check-In/Check-Out'),
    ('wifi', 'WiFi & Entertainment'),
    ('appliances', 'Appliances & Equipment'),
    ('emergency', 'Emergency Information'),
    ('transportation', 'Transportation'),
    ('local_area', 'Local Area Guide'),
    ('faq', 'FAQ'),
    ('amenities', 'Amenities'),
    ('parking', 'Parking Information'),
    ('trash', 'Trash & Recycling'),
    ('quiet_hours', 'Quiet Hours'),
    ('pets', 'Pet Policy'),
    ('smoking', 'Smoking Policy'),
    ('custom', 'Custom Section')
]

ENTRY_TYPES = [
    ('text', 'Text'),
    ('instruction', 'Instruction'),
    ('contact', 'Contact'),
    ('location', 'Location'),
    ('link', 'Link'),
    ('image', 'Image'),
    ('warning', 'Warning'),
    ('tip', 'Tip'),
    ('rule', 'Rule')
]

ICON_CHOICES = [
    ('bi-house', 'House'),
    ('bi-key', 'Key'),
    ('bi-wifi', 'WiFi'),
    ('bi-tv', 'TV'),
    ('bi-telephone', 'Phone'),
    ('bi-exclamation-triangle', 'Warning'),
    ('bi-info-circle', 'Info'),
    ('bi-geo-alt', 'Location'),
    ('bi-car-front', 'Car'),
    ('bi-trash', 'Trash'),
    ('bi-clock', 'Clock'),
    ('bi-list-check', 'Checklist'),
    ('bi-shield-check', 'Security'),
    ('bi-heart', 'Favorite'),
    ('bi-star', 'Star'),
    ('bi-question-circle', 'Question'),
    ('bi-lightbulb', 'Tip'),
    ('bi-book', 'Book'),
    ('bi-calendar', 'Calendar'),
    ('bi-map', 'Map')
]

class GuideBookSectionForm(FlaskForm):
    """Form for creating/editing guide book sections"""
    section_type = SelectField('Section Type', choices=SECTION_TYPES, validators=[DataRequired()])
    title = StringField('Section Title', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('Section Overview', validators=[Optional()])
    icon = SelectField('Icon', choices=[('', 'No Icon')] + ICON_CHOICES, validators=[Optional()])
    order_index = IntegerField('Display Order', validators=[Optional(), NumberRange(min=0)], default=0)
    is_active = BooleanField('Active', default=True)

class GuideBookEntryForm(FlaskForm):
    """Form for creating/editing guide book entries"""
    entry_type = SelectField('Entry Type', choices=ENTRY_TYPES, validators=[DataRequired()])
    title = StringField('Title', validators=[Optional(), Length(max=200)])
    subtitle = StringField('Subtitle', validators=[Optional(), Length(max=200)])
    content = TextAreaField('Content', validators=[Optional()])
    
    # Contact fields
    phone = StringField('Phone Number', validators=[Optional(), Length(max=50)])
    email = EmailField('Email', validators=[Optional(), Email()])
    
    # Location fields
    address = StringField('Address', validators=[Optional(), Length(max=500)])
    latitude = FloatField('Latitude', validators=[Optional()])
    longitude = FloatField('Longitude', validators=[Optional()])
    
    # Link fields
    url = URLField('URL', validators=[Optional(), URL()])
    
    # Image field
    image = FileField('Image', validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    
    # Display options
    icon = SelectField('Icon', choices=[('', 'No Icon')] + ICON_CHOICES, validators=[Optional()])
    order_index = IntegerField('Display Order', validators=[Optional(), NumberRange(min=0)], default=0)
    is_important = BooleanField('Mark as Important', default=False)
    is_active = BooleanField('Active', default=True)

class BulkGuideBookEntryForm(FlaskForm):
    """Form for adding multiple entries at once"""
    entries = TextAreaField('Entries (one per line)', validators=[DataRequired()],
                           render_kw={'placeholder': 'Enter items one per line\nExample:\nNo smoking inside\nQuiet hours 10pm-8am\nCheck-out by 11am'})
    entry_type = SelectField('Entry Type', choices=ENTRY_TYPES, validators=[DataRequired()])