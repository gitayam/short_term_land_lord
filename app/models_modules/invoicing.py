import enum
from datetime import datetime
from app import db
from app.models import User, Task, Property, ServiceType, CleaningSession


class PricingModel(enum.Enum):
    FIXED = "fixed"
    HOURLY = "hourly"
    BUNDLE = "bundle"


class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class TaskPrice(db.Model):
    __tablename__ = 'task_price'

    id = db.Column(db.Integer, primary_key=True)

    # The service type this price applies to
    service_type = db.Column(db.Enum(ServiceType), nullable=False)

    # Pricing model
    pricing_model = db.Column(db.Enum(PricingModel), nullable=False, default=PricingModel.FIXED)

    # Fixed price amount (for fixed pricing model)
    fixed_price = db.Column(db.Float, nullable=True)

    # Hourly rate (for hourly pricing model)
    hourly_rate = db.Column(db.Float, nullable=True)

    # Property this price applies to (optional - if NULL, applies to all properties)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)

    # Creator information
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    property = db.relationship('Property', backref='task_prices')
    creator = db.relationship('User',
                            foreign_keys=[creator_id],
                            primaryjoin="TaskPrice.creator_id == User.id",
                            backref='created_task_prices')

    def __repr__(self):
        property_name = self.property.name if self.property else "All Properties"
        if self.pricing_model == PricingModel.FIXED:
            return f'<TaskPrice {self.service_type.value} - ${self.fixed_price} fixed for {property_name}>'
        else:
            return f'<TaskPrice {self.service_type.value} - ${self.hourly_rate}/hr for {property_name}>'

    def calculate_price(self, duration_minutes=None):
        """Calculate price based on pricing model and duration"""
        if self.pricing_model == PricingModel.FIXED:
            return self.fixed_price
        elif self.pricing_model == PricingModel.HOURLY and duration_minutes:
            # Convert minutes to hours and multiply by hourly rate
            hours = duration_minutes / 60.0
            return hours * self.hourly_rate
        return 0


class Invoice(db.Model):
    __tablename__ = 'invoice'

    id = db.Column(db.Integer, primary_key=True)

    # Invoice number (user-friendly identifier)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)

    # Invoice details
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Date range this invoice covers
    date_from = db.Column(db.Date, nullable=True)
    date_to = db.Column(db.Date, nullable=True)

    # Invoice status
    status = db.Column(db.Enum('draft', 'sent', 'paid', 'cancelled', name='invoice_status'), default='draft')

    # Invoice totals
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax_rate = db.Column(db.Float, nullable=False, default=0.0)
    tax_amount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    # Payment information
    due_date = db.Column(db.DateTime)
    paid_date = db.Column(db.Date, nullable=True)
    payment_notes = db.Column(db.Text, nullable=True)

    # Comments for record-keeping
    comments = db.Column(db.Text, nullable=True)

    # Who created the invoice
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Property this invoice is for
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = db.relationship('User',
                             foreign_keys=[creator_id],
                             primaryjoin="Invoice.creator_id == User.id",
                             backref='created_invoices')
    property = db.relationship('Property', foreign_keys=[property_id], backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Invoice {self.invoice_number} - {self.status} - ${self.total}>'

    def calculate_totals(self):
        """Calculate invoice totals based on items"""
        self.subtotal = sum(item.amount for item in self.items)
        self.tax_amount = self.subtotal * self.tax_rate
        self.total = self.subtotal + self.tax_amount
        return self.total

    def mark_as_paid(self, payment_date=None):
        """Mark the invoice as paid with optional payment date"""
        self.status = 'paid'
        self.paid_date = payment_date if payment_date else datetime.utcnow().date()
        return True

    @classmethod
    def generate_invoice_number(cls):
        """Generate a unique invoice number"""
        # Format: INV-YYYYMMDD-XXXX where XXXX is a sequential number
        today = datetime.utcnow().strftime('%Y%m%d')

        # Find the latest invoice with this date prefix
        prefix = f"INV-{today}-"
        latest_invoice = cls.query.filter(
            cls.invoice_number.like(f"{prefix}%")
        ).order_by(cls.id.desc()).first()

        if latest_invoice:
            # Extract the sequential number and increment
            seq_num = int(latest_invoice.invoice_number.split('-')[-1])
            next_seq_num = seq_num + 1
        else:
            # First invoice of the day
            next_seq_num = 1

        return f"{prefix}{next_seq_num:04d}"


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_item'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)

    # Item details
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)  # quantity * unit_price

    # Optional references to related entities
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    cleaning_session_id = db.Column(db.Integer, db.ForeignKey('cleaning_session.id'), nullable=True)
    service_type = db.Column(db.Enum(ServiceType), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    task = db.relationship('Task', backref='invoice_items')
    cleaning_session = db.relationship('CleaningSession', backref='invoice_items')

    def __repr__(self):
        return f'<InvoiceItem {self.description} - {self.quantity} x ${self.unit_price} = ${self.amount}>'

    def calculate_amount(self):
        """Calculate the amount based on quantity and unit price"""
        self.amount = self.quantity * self.unit_price
        return self.amount