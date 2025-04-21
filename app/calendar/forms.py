from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, URL, Length, Optional

class CalendarImportForm(FlaskForm):
    name = StringField('Calendar Name', validators=[DataRequired(), Length(max=100)])
    ical_url = StringField('iCal URL', validators=[DataRequired(), URL(), Length(max=500)])

    service = SelectField('Service', choices=[
        ('airbnb', 'Airbnb'),
        ('vrbo', 'VRBO'),
        ('booking', 'Booking.com'),
        ('other', 'Other')
    ])

    is_entire_property = BooleanField('Entire Property', default=True)
    room_name = StringField('Room Name', validators=[Optional(), Length(max=100)])

    submit = SubmitField('Import Calendar')