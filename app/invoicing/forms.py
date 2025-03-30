from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, DateField, SubmitField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.models import Property, ServiceType, User
from app.models_modules.invoicing import PricingModel, InvoiceStatus
from datetime import datetime


class TaskPriceForm(FlaskForm):
    """Form for setting prices for different service types"""
    service_type = SelectField('Service Type', validators=[DataRequired()], coerce=str)
    pricing_model = SelectField('Pricing Model', validators=[DataRequired()], coerce=str)
    fixed_price = FloatField('Fixed Price ($)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    hourly_rate = FloatField('Hourly Rate ($/hour)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    property = QuerySelectField('Property (leave blank for all properties)', 
                               get_label='name', 
                               allow_blank=True, 
                               blank_text='All Properties',
                               validators=[Optional()])
    submit = SubmitField('Save Price')
    
    def __init__(self, *args, **kwargs):
        super(TaskPriceForm, self).__init__(*args, **kwargs)
        
        # Set up service type choices
        self.service_type.choices = [(t.value, t.name.replace('_', ' ').title()) 
                                    for t in ServiceType]
        
        # Set up pricing model choices
        self.pricing_model.choices = [(m.value, m.name.title()) 
                                     for m in PricingModel]


class InvoiceForm(FlaskForm):
    """Form for creating and editing invoices"""
    title = StringField('Invoice Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    property = QuerySelectField('Property', get_label='name', validators=[DataRequired()])
    date_from = DateField('Date From', validators=[Optional()])
    date_to = DateField('Date To', validators=[Optional()])
    tax_rate = FloatField('Tax Rate (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0.0)
    due_date = DateField('Due Date', validators=[Optional()])
    payment_notes = TextAreaField('Payment Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Invoice')


class InvoiceItemForm(FlaskForm):
    """Form for adding items to an invoice"""
    description = StringField('Description', validators=[DataRequired(), Length(min=3, max=255)])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)], default=1.0)
    unit_price = FloatField('Unit Price ($)', validators=[DataRequired(), NumberRange(min=0)])
    task_id = HiddenField('Task ID')
    cleaning_session_id = HiddenField('Cleaning Session ID')
    service_type = SelectField('Service Type', validators=[Optional()], coerce=str)
    submit = SubmitField('Add Item')
    
    def __init__(self, *args, **kwargs):
        super(InvoiceItemForm, self).__init__(*args, **kwargs)
        
        # Set up service type choices
        self.service_type.choices = [('', 'None')] + [(t.value, t.name.replace('_', ' ').title()) 
                                                     for t in ServiceType]


class InvoiceFilterForm(FlaskForm):
    """Form for filtering invoices"""
    property = QuerySelectField('Property', get_label='name', validators=[Optional()], allow_blank=True, blank_text='All Properties')
    status = SelectField('Status', validators=[Optional()], coerce=str)
    date_from = DateField('Date From', validators=[Optional()])
    date_to = DateField('Date To', validators=[Optional()])
    is_paid = BooleanField('Paid Only', default=False)
    submit = SubmitField('Filter')
    
    def __init__(self, *args, **kwargs):
        super(InvoiceFilterForm, self).__init__(*args, **kwargs)
        
        # Add an "All" option to status
        self.status.choices = [('', 'All')] + [(status.value, status.name.title()) 
                                              for status in InvoiceStatus]


class InvoiceCommentForm(FlaskForm):
    """Form for adding comments to an invoice"""
    comments = TextAreaField('Comments', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Comments')


class PaymentForm(FlaskForm):
    """Form for marking an invoice as paid"""
    payment_date = DateField('Payment Date', validators=[DataRequired()], default=datetime.utcnow().date)
    payment_notes = TextAreaField('Payment Notes', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Mark as Paid')


class ReportFilterForm(FlaskForm):
    """Form for filtering financial reports"""
    report_type = SelectField('Report Type', choices=[
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('annual', 'Annual Report'),
        ('custom', 'Custom Date Range')
    ], default='monthly')
    
    # For custom date range
    date_from = DateField('Date From', validators=[Optional()])
    date_to = DateField('Date To', validators=[Optional()])
    
    # For weekly/monthly/annual reports
    year = SelectField('Year', coerce=int, validators=[Optional()])
    month = SelectField('Month', choices=[
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ], coerce=int, validators=[Optional()])
    week = SelectField('Week', coerce=int, validators=[Optional()])
    
    # Filter by property
    property = QuerySelectField('Property', get_label='name', validators=[Optional()], 
                               allow_blank=True, blank_text='All Properties')
    
    # Filter by service provider (for managers/admins)
    service_provider = QuerySelectField('Service Provider', get_label='name', validators=[Optional()],
                                      allow_blank=True, blank_text='All Service Providers')
    
    submit = SubmitField('Generate Report')
    
    def __init__(self, *args, **kwargs):
        super(ReportFilterForm, self).__init__(*args, **kwargs)
        
        # Set up year choices (current year and 5 years back)
        current_year = datetime.utcnow().year
        self.year.choices = [(year, str(year)) for year in range(current_year - 5, current_year + 1)]
        self.year.default = current_year
        
        # Set up week choices (1-52)
        self.week.choices = [(week, f'Week {week}') for week in range(1, 53)]