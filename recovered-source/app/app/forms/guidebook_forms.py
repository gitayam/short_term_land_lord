"""
Forms for managing guidebook entries
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, FloatField, 
    BooleanField, SubmitField, HiddenField, IntegerField
)
from wtforms.validators import DataRequired, Optional, Length, URL, NumberRange, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import Property, GuidebookCategory
try:
    from app.utils.validation import validate_coordinate, validate_phone_number
except ImportError:
    def validate_coordinate(*args, **kwargs):
        pass
    def validate_phone_number(*args, **kwargs):
        pass


class GuidebookEntryForm(FlaskForm):
    """Form for creating and editing guidebook entries"""
    
    # Basic information
    title = StringField('Title', validators=[
        DataRequired(message='Title is required'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required'),
        Length(min=10, max=2000, message='Description must be between 10 and 2000 characters')
    ])
    
    category = SelectField('Category', 
                          choices=[(cat.value, cat.value.replace('_', ' ').title()) for cat in GuidebookCategory],
                          validators=[DataRequired(message='Please select a category')])
    
    # Location information
    address = StringField('Address', validators=[
        Optional(),
        Length(max=500, message='Address must be less than 500 characters')
    ])
    
    latitude = FloatField('Latitude', validators=[
        Optional(),
        NumberRange(min=-90, max=90, message='Latitude must be between -90 and 90')
    ])
    
    longitude = FloatField('Longitude', validators=[
        Optional(),
        NumberRange(min=-180, max=180, message='Longitude must be between -180 and 180')
    ])
    
    # Contact and details
    website_url = StringField('Website URL', validators=[
        Optional(),
        URL(message='Please enter a valid URL'),
        Length(max=500, message='URL must be less than 500 characters')
    ])
    
    phone_number = StringField('Phone Number', validators=[
        Optional(),
        Length(max=20, message='Phone number must be less than 20 characters')
    ])
    
    price_range = SelectField('Price Range', 
                             choices=[
                                 ('', 'Not specified'),
                                 ('$', '$ - Budget-friendly'),
                                 ('$$', '$$ - Moderate'),
                                 ('$$$', '$$$ - Upscale'),
                                 ('$$$$', '$$$$ - Fine dining/Luxury')
                             ],
                             validators=[Optional()])
    
    # Opening hours (simplified - can be enhanced later)
    opening_hours_text = TextAreaField('Opening Hours', validators=[
        Optional(),
        Length(max=500, message='Opening hours must be less than 500 characters')
    ], description='e.g., Mon-Fri: 9am-5pm, Sat: 10am-6pm, Sun: Closed')
    
    # Host recommendations
    host_notes = TextAreaField('Host Notes', validators=[
        Optional(),
        Length(max=1000, message='Host notes must be less than 1000 characters')
    ], description='Private notes for your reference (not shown to guests)')
    
    host_tip = StringField('Host Tip', validators=[
        Optional(),
        Length(max=500, message='Host tip must be less than 500 characters')
    ], description='A special tip or recommendation to share with guests')
    
    recommended_for = StringField('Recommended For', validators=[
        Optional(),
        Length(max=200, message='Recommendation must be less than 200 characters')
    ], description='e.g., families, couples, business travelers')
    
    # Image upload
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    image_url = StringField('Image URL', validators=[
        Optional(),
        URL(message='Please enter a valid image URL'),
        Length(max=500, message='Image URL must be less than 500 characters')
    ], description='Alternatively, provide a URL to an image')
    
    # Status options
    is_featured = BooleanField('Featured Entry', 
                              description='Highlight this entry as a top recommendation')
    
    is_active = BooleanField('Active', default=True,
                            description='Uncheck to hide this entry from guests')
    
    sort_order = IntegerField('Sort Order', validators=[
        Optional(),
        NumberRange(min=0, max=999, message='Sort order must be between 0 and 999')
    ], default=0, description='Lower numbers appear first (0 = highest priority)')
    
    # Hidden field for property ID
    property_id = HiddenField()
    
    submit = SubmitField('Save Entry')
    
    def validate_coordinates(self):
        """Validate that if one coordinate is provided, both are provided"""
        lat = self.latitude.data
        lng = self.longitude.data
        
        if (lat is not None and lng is None) or (lat is None and lng is not None):
            if lat is not None and lng is None:
                self.longitude.errors.append('Longitude is required when latitude is provided')
            if lat is None and lng is not None:
                self.latitude.errors.append('Latitude is required when longitude is provided')
            return False
        
        return True
    
    def validate_phone_number(self, field):
        """Validate phone number format"""
        if field.data:
            formatted = validate_phone_number(field.data)
            if not formatted:
                raise ValidationError('Please enter a valid phone number')
    
    def validate_image_source(self):
        """Validate that either image file or URL is provided, not both"""
        has_file = bool(self.image.data)
        has_url = bool(self.image_url.data)
        
        if has_file and has_url:
            self.image_url.errors.append('Please provide either an image file or URL, not both')
            return False
        
        return True
    
    def validate(self, extra_validators=None):
        """Custom validation for the entire form"""
        if not super().validate(extra_validators=extra_validators):
            return False
        
        # Validate coordinates
        if not self.validate_coordinates():
            return False
        
        # Validate image source
        if not self.validate_image_source():
            return False
        
        return True


class GuidebookSearchForm(FlaskForm):
    """Form for searching and filtering guidebook entries"""
    
    category = SelectField('Category',
                          choices=[('', 'All Categories')] + 
                                 [(cat.value, cat.value.replace('_', ' ').title()) for cat in GuidebookCategory],
                          validators=[Optional()])
    
    search = StringField('Search', validators=[
        Optional(),
        Length(max=200, message='Search term must be less than 200 characters')
    ], description='Search titles, descriptions, or locations')
    
    featured_only = BooleanField('Featured Only', 
                                description='Show only featured recommendations')
    
    submit = SubmitField('Filter')


class GuidebookBulkActionForm(FlaskForm):
    """Form for bulk actions on guidebook entries"""
    
    action = SelectField('Action',
                        choices=[
                            ('', 'Select action...'),
                            ('activate', 'Activate selected entries'),
                            ('deactivate', 'Deactivate selected entries'),
                            ('feature', 'Mark as featured'),
                            ('unfeature', 'Remove featured status'),
                            ('delete', 'Delete selected entries')
                        ],
                        validators=[DataRequired(message='Please select an action')])
    
    selected_entries = HiddenField('Selected Entries')
    
    submit = SubmitField('Apply Action')
    
    def get_selected_ids(self):
        """Parse selected entry IDs from hidden field"""
        if not self.selected_entries.data:
            return []
        
        try:
            return [int(id_str) for id_str in self.selected_entries.data.split(',') if id_str.strip()]
        except ValueError:
            return []


class GuidebookImportForm(FlaskForm):
    """Form for importing guidebook entries from external sources"""
    
    import_source = SelectField('Import Source',
                               choices=[
                                   ('', 'Select source...'),
                                   ('csv', 'CSV File'),
                                   ('google_places', 'Google Places (nearby)'),
                                   ('tripadvisor', 'TripAdvisor Export'),
                                   ('manual_list', 'Manual Entry List')
                               ],
                               validators=[DataRequired(message='Please select an import source')])
    
    import_file = FileField('Import File', validators=[
        FileAllowed(['csv', 'txt'], 'CSV and text files only!')
    ])
    
    import_radius = SelectField('Search Radius',
                               choices=[
                                   ('1', '1 km'),
                                   ('2', '2 km'),
                                   ('5', '5 km'),
                                   ('10', '10 km'),
                                   ('20', '20 km')
                               ],
                               default='5',
                               validators=[Optional()])
    
    import_categories = SelectField('Categories to Import',
                                   choices=[
                                       ('all', 'All categories'),
                                       ('food', 'Food & Dining'),
                                       ('attractions', 'Attractions'),
                                       ('shopping', 'Shopping'),
                                       ('services', 'Services')
                                   ],
                                   default='all',
                                   validators=[Optional()])
    
    auto_approve = BooleanField('Auto-approve imports',
                               description='Automatically activate imported entries')
    
    submit = SubmitField('Import Entries')


class QuickAddForm(FlaskForm):
    """Simplified form for quickly adding basic guidebook entries"""
    
    title = StringField('Name/Title', validators=[
        DataRequired(message='Name is required'),
        Length(min=3, max=200)
    ])
    
    category = SelectField('Category',
                          choices=[(cat.value, cat.value.replace('_', ' ').title()) for cat in GuidebookCategory],
                          validators=[DataRequired()])
    
    address = StringField('Address', validators=[Optional(), Length(max=500)])
    
    host_tip = StringField('Quick Tip', validators=[
        Optional(),
        Length(max=200)
    ], description='A quick recommendation for guests')
    
    website_url = StringField('Website', validators=[Optional(), URL()])
    
    submit = SubmitField('Quick Add')