from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SubmitField, SelectField, PasswordField, BooleanField, URLField, FormField, FieldList
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL

class RoomForm(FlaskForm):
    name = StringField('Room Name', validators=[DataRequired(), Length(max=100)])
    room_type = SelectField('Room Type', choices=[
        ('bedroom', '🛏️ Bedroom'),
        ('living_room', '🛋️ Living Room'),
        ('dining_room', '🍽️ Dining Room'),
        ('kitchen', '🍳 Kitchen'),
        ('bathroom', '🚿 Bathroom'),
        ('office', '💼 Office'),
        ('other', '📦 Other')
    ], validators=[DataRequired()])
    square_feet = IntegerField('Approximate Sq. Footage', validators=[Optional(), NumberRange(min=0)])
    has_tv = BooleanField('Has TV', default=False)
    tv_details = StringField('TV Details (size, type)', validators=[Optional(), Length(max=100)])
    
    # Bedroom specific details
    bed_type = SelectField('Bed Type', choices=[
        ('', 'Select Bed Type'),
        ('king', '👑 King'),
        ('queen', '👸 Queen'),
        ('full', '🛌 Full/Double'),
        ('twin', '🛏️ Twin'),
        ('bunk', '🏗️ Bunk Bed'),
        ('sofa', '🛋️ Sofa Bed'),
        ('air', '💨 Air Mattress'),
        ('crib', '👶 Crib'),
        ('other', '🛏️ Other')
    ], validators=[Optional()])
    
    # Bathroom specific details
    has_shower = BooleanField('Has Shower', default=False)
    has_tub = BooleanField('Has Bathtub', default=False)
    
    # For deleting rooms when editing
    delete = BooleanField('Delete this room', default=False)

class PropertyForm(FlaskForm):
    name = StringField('Property Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    
    # Address information
    street_address = StringField('Street Address 🏠', validators=[DataRequired(), Length(max=100)])
    city = StringField('City 🏙️', validators=[DataRequired(), Length(max=50)])
    state = StringField('State/Province 🗺️', validators=[DataRequired(), Length(max=50)])
    zip_code = StringField('ZIP/Postal Code 📮', validators=[DataRequired(), Length(max=20)])
    country = StringField('Country 🌎', validators=[DataRequired(), Length(max=50)], default='United States')
    
    # Property specifications
    property_type = SelectField('Property Type 🏘️', choices=[
        ('', 'Select Type'),
        ('house', '🏠 House'),
        ('apartment', '🏢 Apartment'),
        ('condo', '🏙️ Condominium'),
        ('townhouse', '🏘️ Townhouse'),
        ('duplex', '🏠🏠 Duplex'),
        ('cabin', '🌲 Cabin'),
        ('cottage', '🏡 Cottage'),
        ('villa', '🏛️ Villa'),
        ('other', '🏗️ Other')
    ], validators=[DataRequired()])
    
    # Basic property metrics
    bedrooms = IntegerField('Number of Bedrooms 🛏️', validators=[Optional(), NumberRange(min=0)])
    bathrooms = FloatField('Number of Bathrooms 🚿', validators=[Optional(), NumberRange(min=0)])
    square_feet = IntegerField('Total Square Feet 📏', validators=[Optional(), NumberRange(min=0)])
    year_built = IntegerField('Year Built 📅', validators=[Optional(), NumberRange(min=1800, max=2100)])
    
    # Calendar integration
    ical_url = URLField('Property Calendar URL (iCal) 📅', validators=[Optional(), URL(), Length(max=500)])
    
    # Cleaner-specific information (preserved for compatibility)
    total_beds = IntegerField('Total Number of Beds', validators=[Optional(), NumberRange(min=0)])
    bed_sizes = StringField('Bed Sizes (e.g., "1 King, 2 Queen, 1 Twin")', validators=[Optional(), Length(max=255)])
    number_of_tvs = IntegerField('Number of TVs', validators=[Optional(), NumberRange(min=0)])
    number_of_showers = IntegerField('Number of Showers', validators=[Optional(), NumberRange(min=0)])
    number_of_tubs = IntegerField('Number of Bathtubs', validators=[Optional(), NumberRange(min=0)])
    
    # Access information
    cleaning_supplies_location = TextAreaField('Cleaning Supplies Location 🧹', validators=[Optional()])
    wifi_network = StringField('WiFi Network Name 📶', validators=[Optional(), Length(max=100)])
    wifi_password = PasswordField('WiFi Password 🔑', validators=[Optional(), Length(max=100)])
    special_instructions = TextAreaField('Special Instructions for Cleaners ℹ️', validators=[Optional()])
    entry_instructions = TextAreaField('Entry Instructions (key codes, etc.) 🔐', validators=[Optional()])
    
    # Dynamic room fields will be handled separately in the view function
    
    submit = SubmitField('Save Property 💾')

class PropertyImageForm(FlaskForm):
    image = FileField('Property Image 📷', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    caption = StringField('Caption ✏️', validators=[Optional(), Length(max=255)])
    is_primary = SelectField('Set as Primary Image', choices=[
        ('0', 'No'),
        ('1', 'Yes')
    ], default='0')
    submit = SubmitField('Upload Image 📤')

class PropertyCalendarForm(FlaskForm):
    name = StringField('Calendar Name 📅', validators=[DataRequired(), Length(min=2, max=100)])
    ical_url = URLField('iCal URL 🔗', validators=[DataRequired(), URL(), Length(max=500)])
    
    is_entire_property = BooleanField('This calendar is for the entire property 🏠', default=True)
    room_name = StringField('Room Name (if not entire property) 🛏️', validators=[Optional(), Length(max=100)])
    
    service = SelectField('Calendar Source', choices=[
        ('airbnb', '🏠 Airbnb'),
        ('vrbo', '🏡 VRBO'),
        ('booking', '🏨 Booking.com'),
        ('other', '📅 Other')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Save Calendar 💾')

class GuestAccessForm(FlaskForm):
    guest_access_enabled = BooleanField('Enable Guest Access 🔓', default=False)
    guest_rules = TextAreaField('House Rules 📜', validators=[Optional()], 
                               description='Rules guests should follow during their stay')
    guest_checkin_instructions = TextAreaField('Check-in Instructions 🔑', validators=[Optional()],
                                             description='Instructions for guests on how to check in')
    guest_checkout_instructions = TextAreaField('Check-out Instructions 🧹', validators=[Optional()],
                                              description='Instructions for guests on how to check out')
    guest_wifi_instructions = TextAreaField('WiFi Instructions 📶', validators=[Optional()],
                                          description='Instructions for connecting to WiFi')
    local_attractions = TextAreaField('Local Attractions & Recommendations 🏖️', validators=[Optional()],
                                    description='Information about nearby attractions, restaurants, etc.')
    emergency_contact = StringField('Emergency Contact Information 🚑', validators=[Optional(), Length(max=255)],
                                  description='Contact information for emergencies')
    
    regenerate_token = BooleanField('Regenerate Access Link 🔄', default=False,
                                  description='Check this to create a new access link (invalidates the old one)')
    
    submit = SubmitField('Save Guest Access Settings 💾')