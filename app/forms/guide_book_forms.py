from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import GuideBook

class GuideBookForm(FlaskForm):
    property_id = HiddenField('Property ID', validators=[DataRequired()])
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message='Name must be between 1 and 100 characters')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=1, max=500, message='Description must be between 1 and 500 characters')
    ])
    is_public = BooleanField('Make Public', default=False)

    def validate_name(self, field):
        # Skip validation if property_id is not set (should not happen)
        if not self.property_id.data:
            return
        
        # Check if a guide book with this name already exists for the property
        existing = GuideBook.query.filter_by(
            property_id=int(self.property_id.data),
            name=field.data
        ).first()
        
        # If editing an existing guide book, exclude it from the check
        if hasattr(self, 'guide_book_id') and existing and existing.id == int(self.guide_book_id):
            return
            
        if existing:
            raise ValidationError('A guide book with this name already exists for this property.') 