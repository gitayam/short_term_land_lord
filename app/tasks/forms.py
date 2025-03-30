from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, BooleanField, SubmitField, IntegerField, TelField, RadioField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.models import User, Property, TaskStatus, TaskPriority, RecurrencePattern, UserRoles, MediaType, RepairRequestSeverity, ServiceType


class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    due_date = DateTimeField('Due Date/Time', format='%Y-%m-%d %H:%M', validators=[Optional()])
    status = SelectField('Status', validators=[DataRequired()], coerce=str)
    priority = SelectField('Priority', validators=[DataRequired()], coerce=str)
    notes = TextAreaField('Notes')
    
    # Property selection
    properties = QuerySelectMultipleField('Properties', get_label='name', validators=[Optional()])
    
    # Recurrence options
    is_recurring = BooleanField('Recurring Task')
    recurrence_pattern = SelectField('Recurrence Pattern', coerce=str)
    recurrence_interval = IntegerField('Repeat Every', default=1)
    recurrence_end_date = DateTimeField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Calendar link
    linked_to_checkout = BooleanField('Link to Calendar Checkout')
    calendar_id = SelectField('Calendar', coerce=int, validators=[Optional()])
    
    # Dynamic assignment
    assign_to_next_cleaner = BooleanField('Assign to Next Cleaner')
    
    submit = SubmitField('Save Task')
    
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        
        # Set up status choices
        self.status.choices = [(status.value, status.name.replace('_', ' ').title()) 
                              for status in TaskStatus]
        
        # Set up priority choices
        self.priority.choices = [(priority.value, priority.name.title()) 
                                for priority in TaskPriority]
        
        # Set up recurrence pattern choices
        # First, add standard patterns
        standard_patterns = [(pattern.value, pattern.name.replace('_', ' ').title()) 
                            for pattern in RecurrencePattern]
        
        # Then add custom cleaning patterns
        cleaning_patterns = []
        for pattern in RecurrencePattern.get_cleaning_patterns():
            cleaning_patterns.append((pattern["value"], pattern["name"]))
            
        # Use standard patterns but replace any duplicates with cleaning patterns
        final_patterns = []
        added_values = set()
        
        for pattern in cleaning_patterns:
            final_patterns.append(pattern)
            added_values.add(pattern[0])
            
        for pattern in standard_patterns:
            if pattern[0] not in added_values:
                final_patterns.append(pattern)
                
        self.recurrence_pattern.choices = final_patterns


class TaskAssignmentForm(FlaskForm):
    # Option to assign to existing user
    assign_to_user = BooleanField('Assign to Existing User', default=True)
    user = QuerySelectField('User', get_label=lambda u: f"{u.get_full_name()} ({u.email})", validators=[Optional()])
    
    # Service type for service staff assignments
    service_type = SelectField('Service Type', choices=[(t.value, t.name.replace('_', ' ').title()) 
                                                      for t in ServiceType], 
                             validators=[Optional()])
    
    # Option to assign to external person
    external_name = StringField('Name', validators=[Optional(), Length(max=100)])
    external_phone = TelField('Phone Number', validators=[Optional(), Length(max=20)])
    external_email = StringField('Email', validators=[Optional(), Length(max=120)])
    
    submit = SubmitField('Assign Task')
    
    def validate(self, extra_validators=None):
        if not super(TaskAssignmentForm, self).validate():
            return False
            
        # Either user or external info must be provided
        if self.assign_to_user.data and not self.user.data:
            self.user.errors.append('Please select a user')
            return False
            
        if not self.assign_to_user.data and not self.external_name.data:
            self.external_name.errors.append('Name is required for external assignment')
            return False
            
        if not self.assign_to_user.data and not (self.external_phone.data or self.external_email.data):
            if not self.external_phone.data and not self.external_email.data:
                self.external_phone.errors.append('Either phone number or email is required')
                self.external_email.errors.append('Either phone number or email is required')
            return False
            
        # Service type is required when assigning to service staff
        if self.assign_to_user.data and self.user.data and self.user.data.is_service_staff() and not self.service_type.data:
            self.service_type.errors.append('Service type is required when assigning to service staff')
            return False
            
        return True


class TaskFilterForm(FlaskForm):
    status = SelectField('Status', validators=[Optional()], coerce=str)
    priority = SelectField('Priority', validators=[Optional()], coerce=str)
    property = QuerySelectField('Property', get_label='name', validators=[Optional()])
    assignee = QuerySelectField('Assigned To', get_label=lambda u: f"{u.get_full_name()}", validators=[Optional()])
    due_date_from = DateTimeField('Due From', format='%Y-%m-%d', validators=[Optional()])
    due_date_to = DateTimeField('Due To', format='%Y-%m-%d', validators=[Optional()])
    
    submit = SubmitField('Filter')
    
    def __init__(self, *args, **kwargs):
        super(TaskFilterForm, self).__init__(*args, **kwargs)
        
        # Add an "All" option to status and priority
        self.status.choices = [('', 'All')] + [(status.value, status.name.replace('_', ' ').title()) 
                                              for status in TaskStatus]
        
        self.priority.choices = [('', 'All')] + [(priority.value, priority.name.title()) 
                                                for priority in TaskPriority]


class VideoUploadForm(FlaskForm):
    video = FileField('Video', validators=[
        FileRequired(),
        FileAllowed(['mp4', 'mov', 'avi', 'webm'], 'Videos only!')
    ])
    video_type = RadioField('Video Type', choices=[
        ('start', 'Start of Cleaning'),
        ('end', 'End of Cleaning')
    ], validators=[DataRequired()])
    submit = SubmitField('Upload Video')


class IssueReportForm(FlaskForm):
    description = TextAreaField('Description of Issue', validators=[DataRequired(), Length(min=10, max=500)])
    location = StringField('Location in Property', validators=[DataRequired(), Length(min=3, max=255)])
    additional_notes = TextAreaField('Additional Notes', validators=[Optional(), Length(max=1000)])
    photos = FileField('Photos', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Submit Issue Report')


class CleaningFeedbackForm(FlaskForm):
    rating = SelectField('Rate your cleaning (1-5 stars)', 
                        choices=[(1, '1 - Poor'), (2, '2 - Fair'), (3, '3 - Good'), (4, '4 - Very Good'), (5, '5 - Excellent')],
                        validators=[DataRequired()], 
                        coerce=int)
    notes = TextAreaField('Notes about this cleaning (optional)', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit Feedback')


class RepairRequestForm(FlaskForm):
    title = StringField('Issue Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description of Issue', validators=[DataRequired(), Length(min=10, max=500)])
    location = StringField('Location in Property', validators=[DataRequired(), Length(min=3, max=255)])
    severity = SelectField('Severity', validators=[DataRequired()], coerce=str)
    additional_notes = TextAreaField('Additional Notes', validators=[Optional(), Length(max=1000)])
    photos = FileField('Photos (Optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Submit Repair Request')
    
    def __init__(self, *args, **kwargs):
        super(RepairRequestForm, self).__init__(*args, **kwargs)
        
        # Set up severity choices
        self.severity.choices = [(severity.value, severity.name.title()) 
                                for severity in RepairRequestSeverity]


class ConvertToTaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    due_date = DateTimeField('Due Date/Time', format='%Y-%m-%d %H:%M', validators=[Optional()])
    priority = SelectField('Priority', validators=[DataRequired()], coerce=str)
    notes = TextAreaField('Notes')
    
    # Recurrence options
    is_recurring = BooleanField('Recurring Task')
    recurrence_pattern = SelectField('Recurrence Pattern', coerce=str)
    recurrence_interval = IntegerField('Repeat Every', default=1)
    recurrence_end_date = DateTimeField('End Date', format='%Y-%m-%d', validators=[Optional()])
    
    # Dynamic assignment
    assign_to_next_cleaner = BooleanField('Assign to Next Cleaner')
    
    submit = SubmitField('Create Task')
    
    def __init__(self, *args, **kwargs):
        super(ConvertToTaskForm, self).__init__(*args, **kwargs)
        
        # Set up priority choices
        self.priority.choices = [(priority.value, priority.name.title()) 
                                for priority in TaskPriority]
        
        # Set up recurrence pattern choices
        self.recurrence_pattern.choices = [(pattern.value, pattern.name.replace('_', ' ').title()) 
                                          for pattern in RecurrencePattern]


class TaskTemplateForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=2000)])
    category = StringField('Category', validators=[Length(max=50)])
    is_global = BooleanField('Make Global Template')
    submit = SubmitField('Save Template')