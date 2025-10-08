"""
Comprehensive Financial Analytics Routes
Provides holistic financial tracking including P&L, cash flow, tax reporting
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from sqlalchemy import func, or_
import calendar
from decimal import Decimal
import csv
import io

from app import db
from app.models import Property, CalendarEvent
from app.models_modules.invoicing import Invoice
from app.models_modules.financial_tracking import (
    Expense, ExpenseCategory, ExpenseStatus
)

bp = Blueprint('financial_analytics', __name__, url_prefix='/financial-analytics')


@bp.route('/dashboard')
@login_required
def comprehensive_dashboard():
    """Comprehensive financial dashboard with full P&L view"""

    # Check permissions
    if not (current_user.is_property_owner or current_user.has_admin_role or current_user.is_property_manager):
        flash('Access denied. Financial analytics is only available to property owners and managers.', 'error')
        return redirect(url_for('main.dashboard'))

    # Get properties based on user role
    if current_user.has_admin_role:
        properties = Property.query.all()
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_property_manager:
        properties = current_user.managed_properties
    else:
        properties = []

    # Get date range (default to current month)
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    start_date = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = date(year, month, last_day)

    # Calculate comprehensive financial metrics
    financial_summary = calculate_comprehensive_metrics(properties, start_date, end_date)

    # Get expense breakdown by category
    expense_breakdown = get_expense_breakdown(properties, start_date, end_date)

    # Get cash flow analysis (last 12 months)
    cash_flow_data = get_cash_flow_analysis(properties, 12)

    # Get upcoming expenses and bills
    upcoming_expenses = get_upcoming_expenses(properties, 30)

    # Get property performance comparison
    property_performance = get_property_performance_comparison(properties, start_date, end_date)

    # Tax summary for current year
    tax_summary = get_tax_summary(properties, year)

    return render_template('financial_analytics/comprehensive_dashboard.html',
                         properties=properties,
                         financial_summary=financial_summary,
                         expense_breakdown=expense_breakdown,
                         cash_flow_data=cash_flow_data,
                         upcoming_expenses=upcoming_expenses,
                         property_performance=property_performance,
                         tax_summary=tax_summary,
                         year=year,
                         month=month,
                         month_name=calendar.month_name[month])


def calculate_comprehensive_metrics(properties, start_date, end_date):
    """Calculate comprehensive financial metrics including P&L"""

    metrics = {
        # Revenue streams
        'gross_revenue': Decimal('0.00'),
        'booking_revenue': Decimal('0.00'),
        'additional_fees': Decimal('0.00'),

        # Expense categories
        'total_expenses': Decimal('0.00'),
        'operating_expenses': Decimal('0.00'),
        'labor_costs': Decimal('0.00'),
        'cost_of_goods_sold': Decimal('0.00'),
        'capital_improvements': Decimal('0.00'),

        # Profitability metrics
        'gross_profit': Decimal('0.00'),
        'net_income': Decimal('0.00'),
        'profit_margin': 0.0,
        'roi': 0.0,

        # Cash flow
        'cash_inflow': Decimal('0.00'),
        'cash_outflow': Decimal('0.00'),
        'net_cash_flow': Decimal('0.00'),

        # Property count and averages
        'properties_count': len(properties),
        'avg_revenue_per_property': Decimal('0.00'),
        'avg_expenses_per_property': Decimal('0.00'),
    }

    property_ids = [p.id for p in properties] if properties else []

    # Calculate revenue
    if property_ids:
        # Booking revenue from calendar events
        booking_revenue = db.session.query(func.sum(CalendarEvent.booking_amount)).filter(
            CalendarEvent.property_id.in_(property_ids),
            CalendarEvent.start_date >= start_date,
            CalendarEvent.end_date <= end_date,
            CalendarEvent.booking_amount.isnot(None)
        ).scalar() or Decimal('0.00')

        # Additional revenue from paid invoices
        invoice_revenue = db.session.query(func.sum(Invoice.total)).filter(
            Invoice.property_id.in_(property_ids),
            Invoice.created_at >= datetime.combine(start_date, datetime.min.time()),
            Invoice.created_at <= datetime.combine(end_date, datetime.max.time()),
            Invoice.status == 'paid'
        ).scalar() or Decimal('0.00')

        metrics['booking_revenue'] = booking_revenue
        metrics['additional_fees'] = invoice_revenue
        metrics['gross_revenue'] = booking_revenue + invoice_revenue

        # Calculate expenses by category
        expenses = db.session.query(Expense).filter(
            or_(Expense.property_id.in_(property_ids), Expense.property_id.is_(None)),
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
            Expense.status == ExpenseStatus.PAID.value
        ).all()

        for expense in expenses:
            deductible_amount = expense.deductible_amount

            if expense.category in [
                ExpenseCategory.UTILITIES.value,
                ExpenseCategory.INSURANCE.value,
                ExpenseCategory.PROPERTY_TAXES.value,
                ExpenseCategory.REPAIRS_MAINTENANCE.value,
                ExpenseCategory.SUPPLIES.value,
                ExpenseCategory.PROFESSIONAL_SERVICES.value,
                ExpenseCategory.MARKETING.value,
                ExpenseCategory.TRAVEL.value,
                ExpenseCategory.DEPRECIATION.value,
            ]:
                metrics['operating_expenses'] += deductible_amount

            elif expense.category in [
                ExpenseCategory.CONTRACTOR_PAYMENTS.value,
                ExpenseCategory.EMPLOYEE_WAGES.value,
            ]:
                metrics['labor_costs'] += deductible_amount

            elif expense.category in [
                ExpenseCategory.AMENITIES.value,
                ExpenseCategory.LINENS_REPLACEMENT.value,
                ExpenseCategory.FURNITURE_REPLACEMENT.value,
            ]:
                metrics['cost_of_goods_sold'] += deductible_amount

            elif expense.category in [
                ExpenseCategory.IMPROVEMENTS.value,
                ExpenseCategory.EQUIPMENT.value,
            ]:
                metrics['capital_improvements'] += deductible_amount

        metrics['total_expenses'] = (
            metrics['operating_expenses'] +
            metrics['labor_costs'] +
            metrics['cost_of_goods_sold']
        )

        # Calculate profitability
        metrics['gross_profit'] = metrics['gross_revenue'] - metrics['cost_of_goods_sold']
        metrics['net_income'] = metrics['gross_revenue'] - metrics['total_expenses']

        if metrics['gross_revenue'] > 0:
            metrics['profit_margin'] = float(metrics['net_income'] / metrics['gross_revenue'] * 100)

        # Cash flow (simplified - could be enhanced with actual payment dates)
        metrics['cash_inflow'] = metrics['gross_revenue']
        metrics['cash_outflow'] = metrics['total_expenses']
        metrics['net_cash_flow'] = metrics['cash_inflow'] - metrics['cash_outflow']

        # Averages per property
        if len(properties) > 0:
            metrics['avg_revenue_per_property'] = metrics['gross_revenue'] / len(properties)
            metrics['avg_expenses_per_property'] = metrics['total_expenses'] / len(properties)

    return metrics


def get_expense_breakdown(properties, start_date, end_date):
    """Get detailed expense breakdown by category"""

    property_ids = [p.id for p in properties] if properties else []
    breakdown = {}

    if not property_ids:
        return breakdown

    # Query expenses by category
    expense_query = db.session.query(
        Expense.category,
        func.sum(Expense.amount * Expense.business_percentage / 100).label('total')
    ).filter(
        or_(Expense.property_id.in_(property_ids), Expense.property_id.is_(None)),
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.status == ExpenseStatus.PAID.value
    ).group_by(Expense.category).all()

    for category, total in expense_query:
        breakdown[category] = float(total or 0)

    return breakdown


def get_cash_flow_analysis(properties, months=12):
    """Get cash flow analysis for the last N months"""

    property_ids = [p.id for p in properties] if properties else []
    cash_flow_data = []

    if not property_ids:
        return cash_flow_data

    today = date.today()

    for i in range(months - 1, -1, -1):
        # Calculate month boundaries
        month_date = today - timedelta(days=i * 30)
        year = month_date.year
        month = month_date.month

        start_date = date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = date(year, month, last_day)

        # Calculate revenue
        revenue = db.session.query(func.sum(CalendarEvent.booking_amount)).filter(
            CalendarEvent.property_id.in_(property_ids),
            CalendarEvent.start_date >= start_date,
            CalendarEvent.end_date <= end_date
        ).scalar() or Decimal('0.00')

        # Calculate expenses
        expenses = db.session.query(func.sum(
            Expense.amount * Expense.business_percentage / 100
        )).filter(
            or_(Expense.property_id.in_(property_ids), Expense.property_id.is_(None)),
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
            Expense.status == ExpenseStatus.PAID.value
        ).scalar() or Decimal('0.00')

        cash_flow_data.append({
            'month': calendar.month_abbr[month],
            'year': year,
            'revenue': float(revenue),
            'expenses': float(expenses),
            'net_cash_flow': float(revenue - expenses)
        })

    return cash_flow_data


def get_upcoming_expenses(properties, days=30):
    """Get upcoming expenses and bills"""

    property_ids = [p.id for p in properties] if properties else []
    upcoming = []

    if not property_ids:
        return upcoming

    future_date = date.today() + timedelta(days=days)

    # Get unpaid expenses with due dates
    expenses = db.session.query(Expense).filter(
        or_(Expense.property_id.in_(property_ids), Expense.property_id.is_(None)),
        Expense.due_date.isnot(None),
        Expense.due_date <= future_date,
        Expense.status != ExpenseStatus.PAID.value
    ).order_by(Expense.due_date).all()

    for expense in expenses:
        upcoming.append({
            'description': expense.description,
            'vendor': expense.vendor,
            'amount': expense.amount,
            'due_date': expense.due_date,
            'category': expense.category,
            'is_overdue': expense.is_overdue,
            'property': expense.property_rel.name if expense.property_rel else 'All Properties'
        })

    return upcoming


def get_property_performance_comparison(properties, start_date, end_date):
    """Compare financial performance across properties"""

    performance = []

    for property in properties:
        metrics = calculate_comprehensive_metrics([property], start_date, end_date)

        performance.append({
            'property_name': property.name,
            'revenue': metrics['gross_revenue'],
            'expenses': metrics['total_expenses'],
            'net_income': metrics['net_income'],
            'profit_margin': metrics['profit_margin'],
            'occupancy_rate': calculate_occupancy_rate(property, start_date, end_date)
        })

    # Sort by net income descending
    performance.sort(key=lambda x: x['net_income'], reverse=True)

    return performance


def calculate_occupancy_rate(property, start_date, end_date):
    """Calculate occupancy rate for a property"""

    total_days = (end_date - start_date).days + 1

    # Get booked days
    events = CalendarEvent.query.filter(
        CalendarEvent.property_id == property.id,
        CalendarEvent.start_date <= end_date,
        CalendarEvent.end_date >= start_date
    ).all()

    booked_days = 0
    for event in events:
        event_start = max(event.start_date, start_date)
        event_end = min(event.end_date, end_date)
        if event_start <= event_end:
            booked_days += (event_end - event_start).days + 1

    return (booked_days / total_days * 100) if total_days > 0 else 0


def get_tax_summary(properties, year):
    """Get tax summary for the year"""

    property_ids = [p.id for p in properties] if properties else []

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    if not property_ids:
        return {
            'total_deductible_expenses': Decimal('0.00'),
            'total_revenue': Decimal('0.00'),
            'estimated_tax_savings': Decimal('0.00'),
            'category_breakdown': {}
        }

    # Calculate total deductible expenses
    total_deductible = db.session.query(func.sum(
        Expense.amount * Expense.business_percentage / 100
    )).filter(
        or_(Expense.property_id.in_(property_ids), Expense.property_id.is_(None)),
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.tax_deductible is True,
        Expense.status == ExpenseStatus.PAID.value
    ).scalar() or Decimal('0.00')

    # Calculate total revenue
    total_revenue = db.session.query(func.sum(CalendarEvent.booking_amount)).filter(
        CalendarEvent.property_id.in_(property_ids),
        CalendarEvent.start_date >= start_date,
        CalendarEvent.end_date <= end_date
    ).scalar() or Decimal('0.00')

    # Get category breakdown for tax purposes
    category_breakdown = {}
    category_query = db.session.query(
        Expense.category,
        func.sum(Expense.amount * Expense.business_percentage / 100).label('total')
    ).filter(
        or_(Expense.property_id.in_(property_ids), Expense.property_id.is_(None)),
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.tax_deductible is True,
        Expense.status == ExpenseStatus.PAID.value
    ).group_by(Expense.category).all()

    for category, total in category_query:
        category_breakdown[category] = float(total or 0)

    # Estimated tax savings (assuming 25% tax rate)
    estimated_tax_savings = total_deductible * Decimal('0.25')

    return {
        'total_deductible_expenses': total_deductible,
        'total_revenue': total_revenue,
        'estimated_tax_savings': estimated_tax_savings,
        'category_breakdown': category_breakdown
    }


@bp.route('/export/profit-loss')
@login_required
def export_profit_loss():
    """Export profit and loss statement as CSV"""

    year = request.args.get('year', datetime.now().year, type=int)
    property_id = request.args.get('property_id', type=int)

    # Get properties
    if current_user.has_admin_role:
        properties = Property.query.all()
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    elif current_user.is_property_manager:
        properties = current_user.managed_properties
    else:
        return jsonify({'error': 'Access denied'}), 403

    if property_id:
        properties = [p for p in properties if p.id == property_id]

    # Generate monthly P&L for the year
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        'Month', 'Gross Revenue', 'Operating Expenses', 'Labor Costs',
        'Cost of Goods Sold', 'Total Expenses', 'Net Income', 'Profit Margin %'
    ])

    for month in range(1, 13):
        start_date = date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end_date = date(year, month, last_day)

        metrics = calculate_comprehensive_metrics(properties, start_date, end_date)

        writer.writerow([
            calendar.month_name[month],
            f"{metrics['gross_revenue']:.2f}",
            f"{metrics['operating_expenses']:.2f}",
            f"{metrics['labor_costs']:.2f}",
            f"{metrics['cost_of_goods_sold']:.2f}",
            f"{metrics['total_expenses']:.2f}",
            f"{metrics['net_income']:.2f}",
            f"{metrics['profit_margin']:.1f}%"
        ])

    output.seek(0)

    # Create response
    response = send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'profit_loss_{year}.csv'
    )

    return response


@bp.route('/export/tax-report')
@login_required
def export_tax_report():
    """Export tax-ready expense report"""

    year = request.args.get('year', datetime.now().year, type=int)

    # Get properties
    if current_user.has_admin_role:
        properties = Property.query.all()
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    else:
        return jsonify({'error': 'Access denied'}), 403

    property_ids = [p.id for p in properties]

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Get all deductible expenses
    expenses = db.session.query(Expense).filter(
        or_(Expense.property_id.in_(property_ids), Expense.property_id.is_(None)),
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date,
        Expense.tax_deductible is True,
        Expense.status == ExpenseStatus.PAID.value
    ).order_by(Expense.expense_date).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        'Date', 'Category', 'Description', 'Vendor', 'Amount',
        'Business %', 'Deductible Amount', 'Property', 'Receipt'
    ])

    for expense in expenses:
        writer.writerow([
            expense.expense_date.strftime('%Y-%m-%d'),
            expense.category,
            expense.description,
            expense.vendor or '',
            f"{expense.amount:.2f}",
            f"{expense.business_percentage}%",
            f"{expense.deductible_amount:.2f}",
            expense.property.name if expense.property else 'All Properties',
            'Yes' if expense.receipt_url else 'No'
        ])

    output.seek(0)

    response = send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'tax_report_{year}.csv'
    )

    return response
