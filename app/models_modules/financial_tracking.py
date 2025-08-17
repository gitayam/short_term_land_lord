"""
Comprehensive Financial Tracking Models
Tracks all revenue streams, operating expenses, and provides holistic financial analytics
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from app import db


class ExpenseCategory(Enum):
    """IRS-compliant expense categories for tax reporting"""
    # Operating Expenses
    UTILITIES = "utilities"                    # Electricity, water, gas, internet, cable
    INSURANCE = "insurance"                   # Property, liability, business insurance
    PROPERTY_TAXES = "property_taxes"         # Real estate taxes
    MORTGAGE_INTEREST = "mortgage_interest"   # Loan interest (deductible portion)
    REPAIRS_MAINTENANCE = "repairs_maintenance"  # Ongoing maintenance, repairs
    SUPPLIES = "supplies"                     # Cleaning supplies, amenities, consumables
    PROFESSIONAL_SERVICES = "professional_services"  # Legal, accounting, property mgmt
    MARKETING = "marketing"                   # Advertising, listing fees, photography
    TRAVEL = "travel"                         # Property visits, business travel
    DEPRECIATION = "depreciation"             # Asset depreciation
    
    # Labor Costs
    CONTRACTOR_PAYMENTS = "contractor_payments"  # Independent contractor payments
    EMPLOYEE_WAGES = "employee_wages"           # W2 employee payments
    
    # Cost of Goods Sold
    AMENITIES = "amenities"                   # Welcome baskets, toiletries, coffee
    LINENS_REPLACEMENT = "linens_replacement" # Towels, sheets, pillows
    FURNITURE_REPLACEMENT = "furniture_replacement"  # Furniture, appliances
    
    # Capital Improvements
    IMPROVEMENTS = "improvements"             # Property improvements (capitalized)
    EQUIPMENT = "equipment"                   # Major equipment purchases


class ExpenseStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PAID = "paid"
    DISPUTED = "disputed"


class PaymentMethod(Enum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_PAYMENT = "digital_payment"  # Venmo, PayPal, etc.


class RecurringExpense(db.Model):
    """Template for recurring expenses like utilities, insurance, etc."""
    __tablename__ = 'recurring_expenses'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property.id'), nullable=True)  # Null = applies to all
    
    # Expense details
    name = Column(String(200), nullable=False)  # "Electric Bill - Main House"
    category = Column(String(50), nullable=False)  # ExpenseCategory enum value
    vendor = Column(String(200), nullable=True)  # "Georgia Power", "State Farm"
    description = Column(Text, nullable=True)
    
    # Recurring schedule
    frequency = Column(String(20), nullable=False)  # monthly, quarterly, annually
    amount = Column(Numeric(10, 2), nullable=True)  # Fixed amount (if known)
    due_day = Column(Integer, nullable=True)  # Day of month due (1-31)
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    auto_generate = Column(Boolean, default=True)  # Auto-create expense entries
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    property = relationship('Property', backref='recurring_expenses')
    created_by = relationship('User', backref='created_recurring_expenses')
    expense_entries = relationship('Expense', backref='recurring_template', lazy='dynamic')
    
    def __repr__(self):
        return f'<RecurringExpense {self.name}>'
    
    def generate_next_expense(self):
        """Generate the next expense entry for this recurring template"""
        from datetime import timedelta
        
        # Calculate next due date
        today = date.today()
        if self.frequency == 'monthly':
            next_due = date(today.year, today.month, self.due_day or 1)
            if next_due <= today:
                next_month = today.month + 1 if today.month < 12 else 1
                next_year = today.year if today.month < 12 else today.year + 1
                next_due = date(next_year, next_month, self.due_day or 1)
        
        # Create expense entry
        expense = Expense(
            property_id=self.property_id,
            recurring_expense_id=self.id,
            category=self.category,
            vendor=self.vendor,
            description=f"{self.name} - {next_due.strftime('%B %Y')}",
            amount=self.amount,
            due_date=next_due,
            status=ExpenseStatus.DRAFT.value,
            created_by_id=self.created_by_id
        )
        db.session.add(expense)
        return expense


class Expense(db.Model):
    """Individual expense entries - both one-time and recurring"""
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property.id'), nullable=True)  # Null = business expense
    recurring_expense_id = Column(Integer, ForeignKey('recurring_expenses.id'), nullable=True)
    
    # Expense details
    category = Column(String(50), nullable=False)  # ExpenseCategory enum value
    vendor = Column(String(200), nullable=True)  # Who was paid
    description = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    
    # Tax and accounting
    tax_deductible = Column(Boolean, default=True)
    business_percentage = Column(Integer, default=100)  # % business use (for mixed-use)
    
    # Dates
    expense_date = Column(Date, nullable=False, default=date.today)  # When expense occurred
    due_date = Column(Date, nullable=True)  # When payment is due
    paid_date = Column(Date, nullable=True)  # When actually paid
    
    # Payment tracking
    status = Column(String(20), default=ExpenseStatus.DRAFT.value)
    payment_method = Column(String(20), nullable=True)  # PaymentMethod enum value
    check_number = Column(String(50), nullable=True)
    
    # Receipt management
    receipt_url = Column(String(500), nullable=True)  # Cloud storage URL
    receipt_filename = Column(String(200), nullable=True)
    
    # Relationships and references
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True)  # If paying an invoice
    task_id = Column(Integer, ForeignKey('booking_task.id'), nullable=True)  # If related to a task
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    property = relationship('Property', backref='expenses')
    created_by = relationship('User', foreign_keys=[created_by_id], backref='created_expenses')
    approved_by = relationship('User', foreign_keys=[approved_by_id], backref='approved_expenses')
    
    def __repr__(self):
        return f'<Expense {self.description}: ${self.amount}>'
    
    @property
    def deductible_amount(self):
        """Calculate tax-deductible amount based on business percentage"""
        if not self.tax_deductible:
            return Decimal('0.00')
        return self.amount * (Decimal(self.business_percentage) / Decimal('100'))
    
    @property
    def is_overdue(self):
        """Check if expense payment is overdue"""
        if not self.due_date or self.status == ExpenseStatus.PAID.value:
            return False
        return date.today() > self.due_date
    
    def mark_as_paid(self, payment_date=None, payment_method=None):
        """Mark expense as paid"""
        self.status = ExpenseStatus.PAID.value
        self.paid_date = payment_date or date.today()
        if payment_method:
            self.payment_method = payment_method
        self.updated_at = datetime.utcnow()


class FinancialPeriod(db.Model):
    """Financial reporting periods (monthly, quarterly, annually)"""
    __tablename__ = 'financial_periods'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property.id'), nullable=True)  # Null = all properties
    
    # Period definition
    period_type = Column(String(20), nullable=False)  # monthly, quarterly, annual
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Calculated totals (cached for performance)
    total_revenue = Column(Numeric(12, 2), default=Decimal('0.00'))
    total_expenses = Column(Numeric(12, 2), default=Decimal('0.00'))
    net_income = Column(Numeric(12, 2), default=Decimal('0.00'))
    
    # Expense breakdowns
    operating_expenses = Column(Numeric(12, 2), default=Decimal('0.00'))
    labor_costs = Column(Numeric(12, 2), default=Decimal('0.00'))
    cost_of_goods_sold = Column(Numeric(12, 2), default=Decimal('0.00'))
    capital_improvements = Column(Numeric(12, 2), default=Decimal('0.00'))
    
    # Status
    is_closed = Column(Boolean, default=False)  # Period closed for accounting
    last_calculated = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    property = relationship('Property', backref='financial_periods')
    created_by = relationship('User', backref='created_financial_periods')
    
    def __repr__(self):
        return f'<FinancialPeriod {self.start_date} to {self.end_date}>'
    
    def calculate_totals(self):
        """Recalculate all financial totals for this period"""
        from app.models import CalendarEvent
        from app.models_modules.invoicing import Invoice, InvoiceItem
        
        # Revenue calculation
        revenue_query = db.session.query(func.sum(CalendarEvent.booking_amount)).filter(
            CalendarEvent.start_date >= self.start_date,
            CalendarEvent.end_date <= self.end_date
        )
        if self.property_id:
            revenue_query = revenue_query.filter(CalendarEvent.property_id == self.property_id)
        
        self.total_revenue = revenue_query.scalar() or Decimal('0.00')
        
        # Expense calculation by category
        expense_query = db.session.query(Expense).filter(
            Expense.expense_date >= self.start_date,
            Expense.expense_date <= self.end_date,
            Expense.status == ExpenseStatus.PAID.value
        )
        if self.property_id:
            expense_query = expense_query.filter(Expense.property_id == self.property_id)
        
        expenses = expense_query.all()
        
        # Categorize expenses
        self.operating_expenses = sum(
            exp.deductible_amount for exp in expenses 
            if exp.category in [
                ExpenseCategory.UTILITIES.value,
                ExpenseCategory.INSURANCE.value,
                ExpenseCategory.PROPERTY_TAXES.value,
                ExpenseCategory.REPAIRS_MAINTENANCE.value,
                ExpenseCategory.SUPPLIES.value,
                ExpenseCategory.PROFESSIONAL_SERVICES.value,
                ExpenseCategory.MARKETING.value,
            ]
        ) or Decimal('0.00')
        
        self.labor_costs = sum(
            exp.deductible_amount for exp in expenses
            if exp.category in [
                ExpenseCategory.CONTRACTOR_PAYMENTS.value,
                ExpenseCategory.EMPLOYEE_WAGES.value,
            ]
        ) or Decimal('0.00')
        
        self.cost_of_goods_sold = sum(
            exp.deductible_amount for exp in expenses
            if exp.category in [
                ExpenseCategory.AMENITIES.value,
                ExpenseCategory.LINENS_REPLACEMENT.value,
                ExpenseCategory.FURNITURE_REPLACEMENT.value,
            ]
        ) or Decimal('0.00')
        
        self.capital_improvements = sum(
            exp.deductible_amount for exp in expenses
            if exp.category in [
                ExpenseCategory.IMPROVEMENTS.value,
                ExpenseCategory.EQUIPMENT.value,
            ]
        ) or Decimal('0.00')
        
        self.total_expenses = (
            self.operating_expenses + 
            self.labor_costs + 
            self.cost_of_goods_sold + 
            self.capital_improvements
        )
        
        self.net_income = self.total_revenue - self.total_expenses
        self.last_calculated = datetime.utcnow()
        
        return {
            'revenue': self.total_revenue,
            'expenses': self.total_expenses,
            'net_income': self.net_income,
            'operating_expenses': self.operating_expenses,
            'labor_costs': self.labor_costs,
            'cogs': self.cost_of_goods_sold,
            'capital_improvements': self.capital_improvements
        }


class TaxDocument(db.Model):
    """Generated tax documents and reports"""
    __tablename__ = 'tax_documents'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property.id'), nullable=True)
    financial_period_id = Column(Integer, ForeignKey('financial_periods.id'), nullable=False)
    
    # Document details
    document_type = Column(String(50), nullable=False)  # schedule_e, 1099_misc, profit_loss
    tax_year = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=True)  # Generated document path
    
    # Status
    is_final = Column(Boolean, default=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    property = relationship('Property', backref='tax_documents')
    financial_period = relationship('FinancialPeriod', backref='tax_documents')
    generated_by = relationship('User', backref='generated_tax_documents')
    
    def __repr__(self):
        return f'<TaxDocument {self.document_type} for {self.tax_year}>'


# Import necessary functions for FinancialPeriod calculations
from sqlalchemy import func