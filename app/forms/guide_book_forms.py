from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length

class GuideBookForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message='Name must be between 1 and 100 characters')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=1, max=500, message='Description must be between 1 and 500 characters')
    ])
    is_public = BooleanField('Make Public', default=False) 