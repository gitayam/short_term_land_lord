from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, BooleanField, 
                     IntegerField, FloatField, URLField, TimeField)
from wtforms.validators import DataRequired, Optional, Length, URL, NumberRange
from flask_wtf.file import FileField, FileAllowed

# Recommendation types and their categories
RECOMMENDATION_TYPES = [
    ('place', 'Place'),
    ('activity', 'Activity'),
    ('service', 'Service'),
    ('event', 'Event'),
    ('transportation', 'Transportation'),
    ('shopping', 'Shopping'),
    ('emergency', 'Emergency')
]

# Categories for each type
TYPE_CATEGORIES = {
    'place': [
        ('restaurant', 'Restaurant'),
        ('bar', 'Bar/Pub'),
        ('cafe', 'Cafe/Coffee Shop'),
        ('museum', 'Museum'),
        ('park', 'Park'),
        ('beach', 'Beach'),
        ('landmark', 'Landmark'),
        ('viewpoint', 'Viewpoint'),
        ('other', 'Other')
    ],
    'activity': [
        ('tour', 'Tour'),
        ('hiking', 'Hiking'),
        ('water_sports', 'Water Sports'),
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural'),
        ('sports', 'Sports'),
        ('entertainment', 'Entertainment'),
        ('nightlife', 'Nightlife'),
        ('other', 'Other')
    ],
    'service': [
        ('spa', 'Spa/Wellness'),
        ('gym', 'Gym/Fitness'),
        ('medical', 'Medical'),
        ('beauty', 'Beauty/Salon'),
        ('laundry', 'Laundry'),
        ('rental', 'Equipment Rental'),
        ('tour_operator', 'Tour Operator'),
        ('other', 'Other')
    ],
    'event': [
        ('festival', 'Festival'),
        ('market', 'Market'),
        ('concert', 'Concert'),
        ('show', 'Show/Performance'),
        ('sports_event', 'Sports Event'),
        ('seasonal', 'Seasonal Event'),
        ('other', 'Other')
    ],
    'transportation': [
        ('taxi', 'Taxi/Ride Service'),
        ('car_rental', 'Car Rental'),
        ('bike_rental', 'Bike Rental'),
        ('public_transit', 'Public Transit'),
        ('airport_shuttle', 'Airport Shuttle'),
        ('boat', 'Boat/Ferry'),
        ('other', 'Other')
    ],
    'shopping': [
        ('grocery', 'Grocery Store'),
        ('mall', 'Shopping Mall'),
        ('market', 'Local Market'),
        ('pharmacy', 'Pharmacy'),
        ('souvenir', 'Souvenir Shop'),
        ('specialty', 'Specialty Store'),
        ('convenience', 'Convenience Store'),
        ('other', 'Other')
    ],
    'emergency': [
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('pharmacy_24h', '24h Pharmacy'),
        ('police', 'Police'),
        ('fire', 'Fire Department'),
        ('embassy', 'Embassy/Consulate'),
        ('other', 'Other')
    ]
}

PRICE_RANGES = [
    ('', 'Not Applicable'),
    ('free', 'Free'),
    ('$', '$ - Budget'),
    ('$$', '$$ - Moderate'),
    ('$$$', '$$$ - Expensive'),
    ('$$$$', '$$$$ - Very Expensive')
]

DIFFICULTY_LEVELS = [
    ('', 'Not Applicable'),
    ('easy', 'Easy'),
    ('moderate', 'Moderate'),
    ('difficult', 'Difficult'),
    ('expert', 'Expert')
]

DISTANCE_OPTIONS = [
    ('', 'Select Distance'),
    ('1_min_walk', '1 min walk'),
    ('5_min_walk', '5 min walk'),
    ('10_min_walk', '10 min walk'),
    ('15_min_walk', '15 min walk'),
    ('20_min_walk', '20 min walk'),
    ('30_min_walk', '30 min walk'),
    ('5_min_drive', '5 min drive'),
    ('10_min_drive', '10 min drive'),
    ('15_min_drive', '15 min drive'),
    ('20_min_drive', '20 min drive'),
    ('30_min_drive', '30 min drive'),
    ('45_min_drive', '45 min drive'),
    ('1_hour_drive', '1 hour drive'),
    ('over_1_hour', 'Over 1 hour')
]

class EnhancedRecommendationForm(FlaskForm):
    """Enhanced form for creating/editing recommendations with type-specific fields"""
    
    # Basic Information
    recommendation_type = SelectField('Type', 
                                    choices=RECOMMENDATION_TYPES, 
                                    validators=[DataRequired()],
                                    render_kw={'onchange': 'updateFormFields()'})
    
    category = SelectField('Category', 
                          choices=[],  # Will be populated dynamically
                          validators=[DataRequired()])
    
    title = StringField('Name/Title', 
                       validators=[DataRequired(), Length(min=1, max=100)],
                       render_kw={'placeholder': 'e.g., The Blue Whale Restaurant'})
    
    description = TextAreaField('Description', 
                              validators=[DataRequired(), Length(min=10, max=500)],
                              render_kw={'rows': 4, 'placeholder': 'Brief description of what makes this special'})
    
    # Location & Contact
    address = StringField('Address', 
                         validators=[Optional(), Length(max=500)],
                         render_kw={'placeholder': '123 Main St, City'})
    
    phone = StringField('Phone', 
                       validators=[Optional(), Length(max=50)],
                       render_kw={'placeholder': '+1 234-567-8900'})
    
    website = URLField('Website', 
                      validators=[Optional(), URL()],
                      render_kw={'placeholder': 'https://example.com'})
    
    map_link = URLField('Map Link', 
                       validators=[Optional(), URL()],
                       render_kw={'placeholder': 'Google Maps or other map service URL'})
    
    distance_from_property = SelectField('Distance from Property', 
                                        choices=DISTANCE_OPTIONS,
                                        validators=[Optional()])
    
    # Timing & Availability
    hours = TextAreaField('Operating Hours', 
                         validators=[Optional(), Length(max=500)],
                         render_kw={'rows': 3, 'placeholder': 'Mon-Fri: 9am-5pm\nSat-Sun: 10am-6pm'})
    
    best_time_to_go = StringField('Best Time to Visit', 
                                 validators=[Optional(), Length(max=255)],
                                 render_kw={'placeholder': 'Sunset, Happy Hour (5-7pm), Weekday mornings'})
    
    seasonal_availability = StringField('Seasonal Availability', 
                                       validators=[Optional(), Length(max=255)],
                                       render_kw={'placeholder': 'Year-round, Summer only, October-March'})
    
    # Booking & Pricing
    booking_required = BooleanField('Booking Required')
    
    booking_link = URLField('Booking Link', 
                           validators=[Optional(), URL()],
                           render_kw={'placeholder': 'Reservation or booking website'})
    
    price_range = SelectField('Price Range', 
                             choices=PRICE_RANGES,
                             validators=[Optional()])
    
    # Restaurant/Food Specific
    cuisine_type = StringField('Cuisine Type', 
                              validators=[Optional(), Length(max=100)],
                              render_kw={'placeholder': 'Italian, Thai, Seafood, etc.'})
    
    recommended_meal = StringField('Recommended Dishes', 
                                  validators=[Optional(), Length(max=255)],
                                  render_kw={'placeholder': 'Fish tacos, Pad Thai, House special pizza'})
    
    dietary_options = StringField('Dietary Options', 
                                 validators=[Optional(), Length(max=255)],
                                 render_kw={'placeholder': 'Vegetarian, Vegan, Gluten-free available'})
    
    # Activity Specific
    duration = StringField('Duration', 
                          validators=[Optional(), Length(max=100)],
                          render_kw={'placeholder': '2-3 hours, Half day, Full day'})
    
    difficulty_level = SelectField('Difficulty Level', 
                                  choices=DIFFICULTY_LEVELS,
                                  validators=[Optional()])
    
    age_restrictions = StringField('Age Restrictions', 
                                  validators=[Optional(), Length(max=100)],
                                  render_kw={'placeholder': 'All ages, 18+, Children under 12 free'})
    
    # Transportation Specific
    app_download_link = URLField('App Download Link', 
                                validators=[Optional(), URL()],
                                render_kw={'placeholder': 'Link to mobile app'})
    
    fare_info = StringField('Fare Information', 
                           validators=[Optional(), Length(max=255)],
                           render_kw={'placeholder': '$2.50 per ride, Meter starts at $5'})
    
    # Event Specific
    event_dates = StringField('Event Dates', 
                             validators=[Optional(), Length(max=255)],
                             render_kw={'placeholder': 'July 4th, December 15-25'})
    
    recurring_schedule = StringField('Recurring Schedule', 
                                    validators=[Optional(), Length(max=255)],
                                    render_kw={'placeholder': 'Every Saturday, First Friday of month'})
    
    # Additional Details
    wifi_name = StringField('WiFi Network Name', 
                           validators=[Optional(), Length(max=255)],
                           render_kw={'placeholder': 'GuestWiFi'})
    
    wifi_password = StringField('WiFi Password', 
                               validators=[Optional(), Length(max=255)],
                               render_kw={'placeholder': 'password123'})
    
    parking_details = TextAreaField('Parking Information', 
                                   validators=[Optional()],
                                   render_kw={'rows': 2, 'placeholder': 'Free street parking, Paid lot ($10/day)'})
    
    accessibility_info = StringField('Accessibility', 
                                   validators=[Optional(), Length(max=255)],
                                   render_kw={'placeholder': 'Wheelchair accessible, Elevator available'})
    
    insider_tips = TextAreaField('Insider Tips', 
                                validators=[Optional()],
                                render_kw={'rows': 3, 'placeholder': 'Ask for the secret menu, Best tables are on the terrace'})
    
    # Meta Information
    staff_pick = BooleanField('Mark as Staff Pick')
    is_featured = BooleanField('Feature this Recommendation')
    priority_order = IntegerField('Display Priority', 
                                 validators=[Optional(), NumberRange(min=0)],
                                 default=0,
                                 render_kw={'placeholder': '0 (higher number = higher priority)'})
    
    # Photo Upload
    photo = FileField('Photo', 
                     validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    
    # Guide Book Assignment
    add_to_guide_books = SelectField('Add to Guide Books',
                                    choices=[],  # Will be populated with guide books
                                    validators=[Optional()],
                                    render_kw={'multiple': True})