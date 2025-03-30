from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, FloatField, SubmitField, SelectField, PasswordField, BooleanField, URLField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL

class PropertyForm(FlaskForm):
    name = StringField('Property Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    
    # Address information
    street_address = StringField('Street Address', validators=[DataRequired(), Length(max=100)])
    city = StringField('City', validators=[DataRequired(), Length(max=50)])
    state = StringField('State/Province', validators=[DataRequired(), Length(max=50)])
    zip_code = StringField('ZIP/Postal Code', validators=[DataRequired(), Length(max=20)])
    country = StringField('Country', validators=[DataRequired(), Length(max=50)], default='United States')
    
    # Property specifications
    property_type = SelectField('Property Type', choices=[
        ('', 'Select Type'),
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condominium'),
        ('townhouse', 'Townhouse'),
        ('duplex', 'Duplex'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    bedrooms = IntegerField('Bedrooms', validators=[Optional(), NumberRange(min=0)])
    bathrooms = FloatField('Bathrooms', validators=[Optional(), NumberRange(min=0)])
    square_feet = IntegerField('Square Feet', validators=[Optional(), NumberRange(min=0)])
    year_built = IntegerField('Year Built', validators=[Optional(), NumberRange(min=1800, max=2100)])
    
    # Cleaner-specific information
    total_beds = IntegerField('Total Number of Beds', validators=[Optional(), NumberRange(min=0)])
    bed_sizes = StringField('Bed Sizes (e.g., "1 King, 2 Queen, 1 Twin")', validators=[Optional(), Length(max=255)])
    number_of_tvs = IntegerField('Number of TVs', validators=[Optional(), NumberRange(min=0)])
    number_of_showers = IntegerField('Number of Showers', validators=[Optional(), NumberRange(min=0)])
    number_of_tubs = IntegerField('Number of Bathtubs', validators=[Optional(), NumberRange(min=0)])
    cleaning_supplies_location = TextAreaField('Cleaning Supplies Location', validators=[Optional()])
    wifi_network = StringField('WiFi Network Name', validators=[Optional(), Length(max=100)])
    wifi_password = PasswordField('WiFi Password', validators=[Optional(), Length(max=100)])
    special_instructions = TextAreaField('Special Instructions for Cleaners', validators=[Optional()])
    entry_instructions = TextAreaField('Entry Instructions (key codes, etc.)', validators=[Optional()])
    
    submit = SubmitField('Save Property')

class PropertyImageForm(FlaskForm):
    image = FileField('Property Image', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    caption = StringField('Caption', validators=[Optional(), Length(max=255)])
    is_primary = SelectField('Set as Primary Image', choices=[
        ('0', 'No'),
        ('1', 'Yes')
    ], default='0')
    submit = SubmitField('Upload Image')

class PropertyCalendarForm(FlaskForm):
    name = StringField('Calendar Name', validators=[DataRequired(), Length(min=2, max=100)])
    ical_url = URLField('iCal URL', validators=[DataRequired(), URL(), Length(max=500)])
    
    is_entire_property = BooleanField('This calendar is for the entire property', default=True)
    room_name = StringField('Room Name (if not entire property)', validators=[Optional(), Length(max=100)])
    
    service = SelectField('Calendar Source', choices=[
        ('airbnb', 'Airbnb'),
        ('vrbo', 'VRBO'),
        ('booking', 'Booking.com'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Save Calendar')
