from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField, TextAreaField, SelectField, DateField, BooleanField,
    MultipleFileField, HiddenField, SelectMultipleField, IntegerField,
    FloatField, SubmitField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.models import (
    TaskPriority, RepairRequestSeverity, Property, TaskStatus,
    RecurrencePattern, ServiceType, RepairRequestStatus
)


## Set Common Variables
MIN_LENGTH = 5
MAX_LENGTH = 1000

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=3, max=100, message='Title must be between 3 and 100 characters')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=MIN_LENGTH, max=MAX_LENGTH, message='Description must be between 5 and 1000 characters')
    ])
    properties = QuerySelectMultipleField('Properties',
        validators=[Optional()],
        get_label='name',
        allow_blank=True
    )
    due_date = DateField('Due Date', validators=[Optional()])
    status = SelectField('Status', choices=[
        (status.value, status.name.replace('_', ' ').title())
        for status in TaskStatus
    ], validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        (priority.value, priority.name.replace('_', ' ').title())
        for priority in TaskPriority
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    is_recurring = BooleanField('Recurring Task')
    recurrence_pattern = SelectField('Recurrence Pattern', choices=[
        (pattern.value, pattern.name.replace('_', ' ').title())
        for pattern in RecurrencePattern
    ], validators=[Optional()])
    recurrence_interval = IntegerField('Recurrence Interval', validators=[Optional(), NumberRange(min=1)])
    recurrence_end_date = DateField('Recurrence End Date', validators=[Optional()])
    assign_to_next_cleaner = BooleanField('Assign to Next Available Cleaner')
    linked_to_checkout = BooleanField('Link to Property Checkout')
    calendar_id = SelectField('Calendar', coerce=int, validators=[Optional()])

class TaskAssignmentForm(FlaskForm):
    assign_to_user = BooleanField('Assign to Existing User')
    user = QuerySelectField('Assign To',
        validators=[Optional()],
        get_label=lambda obj: f"{obj.first_name} {obj.last_name}",
        allow_blank=True,
        blank_text='Select staff member...'
    )
    external_name = StringField('Name', validators=[Optional(), Length(min=2, max=100)])
    external_phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    external_email = StringField('Email', validators=[Optional(), Length(max=120)])
    service_type = SelectField('Service Type', choices=[
        (type.value, type.name.replace('_', ' ').title())
        for type in ServiceType
    ], validators=[DataRequired()])
    submit = SubmitField('Assign Task')

class TaskFilterForm(FlaskForm):
    status = SelectField('Status', choices=[('all', 'All')] + [
        (status.value, status.name.replace('_', ' ').title())
        for status in TaskStatus
    ], validators=[Optional()])
    priority = SelectField('Priority', choices=[('all', 'All')] + [
        (priority.value, priority.name.replace('_', ' ').title())
        for priority in TaskPriority
    ], validators=[Optional()])
    property = QuerySelectField('Property',
        validators=[Optional()],
        get_label='name',
        allow_blank=True,
        blank_text='All Properties'
    )

class VideoUploadForm(FlaskForm):
    video = FileField('Video', validators=[
        DataRequired(),
        FileAllowed(['mp4', 'mov', 'avi'], 'Videos only!')
    ])
    description = TextAreaField('Description', validators=[Optional()])

class IssueReportForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=MIN_LENGTH, max=MAX_LENGTH)
    ])
    location = StringField('Location', validators=[
        DataRequired(),
        Length(max=255)
    ])
    severity = SelectField('Severity', choices=[
        (severity.value, severity.name.replace('_', ' ').title())
        for severity in RepairRequestSeverity
    ], validators=[DataRequired()])
    photos = MultipleFileField('Photos', validators=[Optional()])

class CleaningFeedbackForm(FlaskForm):
    notes = TextAreaField('Notes', validators=[
        DataRequired(),
        Length(min=MIN_LENGTH, max=MAX_LENGTH)
    ])
    time_spent = FloatField('Time Spent (hours)', validators=[
        DataRequired(),
        NumberRange(min=0.1, max=24)
    ])
    photos = MultipleFileField('Photos', validators=[Optional()])

class RepairRequestForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=3, max=100, message='Title must be between 3 and 100 characters')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=5, max=1000, message='Description must be between 5 and 1000 characters')
    ])
    property = QuerySelectField('Property', 
        validators=[DataRequired()],
        get_label='name',
        allow_blank=True,
        blank_text='Select a property...'
    )
    location = StringField('Location in Property', validators=[
        DataRequired(),
        Length(max=255, message='Location must not exceed 255 characters')
    ])
    priority = SelectField('Priority', choices=[
        (priority.name, priority.name.title()) 
        for priority in TaskPriority
    ], validators=[DataRequired()])
    
    due_date = DateField('Due Date', validators=[Optional()])
    
    additional_notes = TextAreaField('Additional Notes', validators=[
        Optional(),
        Length(max=2000, message='Additional notes must not exceed 2000 characters')
    ])
    
    photos = MultipleFileField('Photos', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])

class ConvertToTaskForm(FlaskForm):
    title = StringField('Task Title', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Task Description', validators=[
        DataRequired(),
        Length(min=MIN_LENGTH, max=MAX_LENGTH)
    ])
    due_date = DateField('Due Date', validators=[Optional()])
    priority = SelectField('Priority', choices=[
        (priority.value, priority.name.replace('_', ' ').title())
        for priority in TaskPriority
    ], validators=[DataRequired()])
    service_type = SelectField('Service Type', choices=[
        (type.value, type.name.replace('_', ' ').title())
        for type in ServiceType
    ], validators=[DataRequired()])

class TaskTemplateForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=MIN_LENGTH, max=MAX_LENGTH)
    ])
    is_global = BooleanField('Make Global Template')
    sequence_number = IntegerField('Sequence Number', validators=[Optional()])

class TaskStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        (status.value, status.name.replace('_', ' ').title())
        for status in TaskStatus
    ], validators=[DataRequired()])

class TaskPriorityForm(FlaskForm):
    priority = SelectField('Priority', choices=[
        (priority.value, priority.name.replace('_', ' ').title())
        for priority in TaskPriority
    ], validators=[DataRequired()])

class TaskDueDateForm(FlaskForm):
    due_date = DateField('Due Date', validators=[Optional()])

class TaskAssigneeForm(FlaskForm):
    assignee = QuerySelectField('Assignee',
        validators=[Optional()],
        get_label=lambda obj: f"{obj.first_name} {obj.last_name}",
        allow_blank=True,
        blank_text='Select staff member...'
    )

class TaskLocationForm(FlaskForm):
    location = StringField('Location', validators=[
        DataRequired(),
        Length(max=255)
    ])

class TaskDescriptionForm(FlaskForm):
    description = TextAreaField('Description', validators=[
        DataRequired(),
        Length(min=MIN_LENGTH, max=MAX_LENGTH)
    ]) 