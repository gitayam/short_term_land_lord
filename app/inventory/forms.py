from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, SelectField, SubmitField, HiddenField, URLField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import ItemCategory, TransactionType, Property

class InventoryCatalogItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(min=2, max=100)])
    category = SelectField('Category', validators=[DataRequired()], coerce=str)
    unit = StringField('Unit of Measure', validators=[DataRequired(), Length(max=20)], default='units')

    # Detailed information
    description = TextAreaField('Description', validators=[Optional()])
    unit_price = FloatField('Unit Price ($)', validators=[Optional(), NumberRange(min=0)])
    currency = StringField('Currency', validators=[Optional(), Length(max=3)], default='USD')

    submit = SubmitField('Save Catalog Item')

    def __init__(self, *args, **kwargs):
        super(InventoryCatalogItemForm, self).__init__(*args, **kwargs)

        # Set up category choices
        self.category.choices = [(category.value, category.name.title())
                                for category in ItemCategory]

class InventoryItemForm(FlaskForm):
    catalog_item_id = QuerySelectField('Item', get_label='name', validators=[DataRequired()])
    current_quantity = FloatField('Current Quantity', validators=[DataRequired(), NumberRange(min=0)])
    storage_location = StringField('Storage Location', validators=[Optional(), Length(max=100)])
    reorder_threshold = FloatField('Reorder Threshold', validators=[Optional(), NumberRange(min=0)])

    submit = SubmitField('Save Item')

    def __init__(self, *args, **kwargs):
        super(InventoryItemForm, self).__init__(*args, **kwargs)

        # The query for catalog_item_id will be set in the route

class InventoryTransactionForm(FlaskForm):
    item_id = HiddenField('Item ID', validators=[DataRequired()])
    transaction_type = SelectField('Transaction Type', validators=[DataRequired()], coerce=str)
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    notes = TextAreaField('Notes', validators=[Optional()])

    submit = SubmitField('Record Transaction')

    def __init__(self, *args, **kwargs):
        super(InventoryTransactionForm, self).__init__(*args, **kwargs)

        # Set up transaction type choices - exclude transfers which have their own form
        self.transaction_type.choices = [
            (TransactionType.RESTOCK.value, 'Restock'),
            (TransactionType.USAGE.value, 'Usage'),
            (TransactionType.ADJUSTMENT.value, 'Adjustment')
        ]

class InventoryTransferForm(FlaskForm):
    item_id = HiddenField('Item ID', validators=[DataRequired()])
    quantity = FloatField('Quantity to Transfer', validators=[DataRequired(), NumberRange(min=0.01)])
    destination_property = QuerySelectField('Destination Property', get_label='name', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])

    submit = SubmitField('Transfer Item')

class BarcodeSearchForm(FlaskForm):
    barcode = StringField('Barcode', validators=[DataRequired()])
    submit = SubmitField('Search')

class InventoryFilterForm(FlaskForm):
    category = SelectField('Category', validators=[Optional()], coerce=str)
    low_stock_only = SelectField('Stock Level', choices=[
        ('', 'All Items'),
        ('low', 'Low Stock Only')
    ], validators=[Optional()])
    search = StringField('Search', validators=[Optional()])
    barcode = StringField('Barcode', validators=[Optional()])

    submit = SubmitField('Filter')

    def __init__(self, *args, **kwargs):
        super(InventoryFilterForm, self).__init__(*args, **kwargs)

        # Add an "All" option to category
        self.category.choices = [('', 'All Categories')] + [(category.value, category.name.title())
                                                          for category in ItemCategory]