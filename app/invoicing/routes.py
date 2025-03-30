from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.invoicing import bp
from app.invoicing.forms import (
    TaskPriceForm, InvoiceForm, InvoiceItemForm, InvoiceFilterForm,
    InvoiceCommentForm, PaymentForm, ReportFilterForm
)
from app.models import User, Property, Task, CleaningSession, ServiceType, UserRoles, TaskAssignment
from app.models_modules.invoicing import TaskPrice, Invoice, InvoiceItem, PricingModel, InvoiceStatus
from app.auth.decorators import property_owner_required, admin_required, invoice_access_required
from datetime import datetime, timedelta, date
from sqlalchemy import or_, and_, func, extract
from functools import wraps
from calendar import monthrange
# import pandas as pd  # Commented out until needed


def maintenance_staff_required(f):
    """Decorator to ensure only maintenance staff or higher roles can access a route"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_maintenance() or current_user.is_property_manager() or 
                current_user.is_property_owner() or current_user.is_admin()):
            flash('Access denied. You must be maintenance staff or higher to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/prices')
@invoice_access_required
def prices():
    """View all task prices"""
    # Get all prices
    if current_user.is_admin():
        # Admins see all prices
        prices = TaskPrice.query.order_by(TaskPrice.service_type, TaskPrice.property_id.nullsfirst()).all()
    elif current_user.is_property_owner() or current_user.is_property_manager():
        # Property owners see prices for their properties and global prices
        owned_property_ids = [p.id for p in current_user.properties]
        prices = TaskPrice.query.filter(
            or_(
                TaskPrice.property_id.in_(owned_property_ids),
                TaskPrice.property_id.is_(None)
            )
        ).order_by(TaskPrice.service_type, TaskPrice.property_id.nullsfirst()).all()
    
    return render_template('invoicing/prices.html', 
                          title='Task Prices', 
                          prices=prices)

@bp.route('/prices/create', methods=['GET', 'POST'])
@invoice_access_required
def create_price():
    """Create a new task price"""
    form = TaskPriceForm()
    
    # Set up query for properties owned by the current user
    if current_user.is_admin():
        form.property.query = Property.query
    else:
        form.property.query = Property.query.filter_by(owner_id=current_user.id)
    
    if form.validate_on_submit():
        # Check if a price already exists for this service type and property
        existing_price = None
        if form.property.data:
            existing_price = TaskPrice.query.filter_by(
                service_type=ServiceType(form.service_type.data),
                property_id=form.property.data.id
            ).first()
        else:
            existing_price = TaskPrice.query.filter_by(
                service_type=ServiceType(form.service_type.data),
                property_id=None
            ).first()
        
        if existing_price:
            flash(f'A price already exists for {form.service_type.data} for {"this property" if form.property.data else "all properties"}. Please edit the existing price.', 'warning')
            return redirect(url_for('invoicing.prices'))
        
        # Create new price
        price = TaskPrice(
            service_type=ServiceType(form.service_type.data),
            pricing_model=PricingModel(form.pricing_model.data),
            fixed_price=form.fixed_price.data if form.pricing_model.data == PricingModel.FIXED.value else None,
            hourly_rate=form.hourly_rate.data if form.pricing_model.data == PricingModel.HOURLY.value else None,
            property_id=form.property.data.id if form.property.data else None,
            creator_id=current_user.id
        )
        
        db.session.add(price)
        db.session.commit()
        
        flash('Price created successfully!', 'success')
        return redirect(url_for('invoicing.prices'))
    
    return render_template('invoicing/price_form.html', 
                          title='Create Task Price', 
                          form=form)

@bp.route('/prices/<int:id>/edit', methods=['GET', 'POST'])
@invoice_access_required
def edit_price(id):
    """Edit an existing task price"""
    price = TaskPrice.query.get_or_404(id)
    
    # Check if user has permission to edit this price
    if not current_user.is_admin() and (
        (price.property_id and price.property.owner_id != current_user.id) or
        (price.creator_id != current_user.id)
    ):
        flash('You do not have permission to edit this price.', 'danger')
        return redirect(url_for('invoicing.prices'))
    
    form = TaskPriceForm()
    
    # Set up query for properties owned by the current user
    if current_user.is_admin():
        form.property.query = Property.query
    else:
        form.property.query = Property.query.filter_by(owner_id=current_user.id)
    
    if form.validate_on_submit():
        # Update price
        price.service_type = ServiceType(form.service_type.data)
        price.pricing_model = PricingModel(form.pricing_model.data)
        price.fixed_price = form.fixed_price.data if form.pricing_model.data == PricingModel.FIXED.value else None
        price.hourly_rate = form.hourly_rate.data if form.pricing_model.data == PricingModel.HOURLY.value else None
        price.property_id = form.property.data.id if form.property.data else None
        
        db.session.commit()
        
        flash('Price updated successfully!', 'success')
        return redirect(url_for('invoicing.prices'))
    
    elif request.method == 'GET':
        # Populate form with existing data
        form.service_type.data = price.service_type.value
        form.pricing_model.data = price.pricing_model.value
        form.fixed_price.data = price.fixed_price
        form.hourly_rate.data = price.hourly_rate
        form.property.data = price.property
    
    return render_template('invoicing/price_form.html', 
                          title='Edit Task Price', 
                          form=form,
                          price=price)

@bp.route('/prices/<int:id>/delete', methods=['POST'])
@invoice_access_required
def delete_price(id):
    """Delete a task price"""
    price = TaskPrice.query.get_or_404(id)
    
    # Check if user has permission to delete this price
    if not current_user.is_admin() and (
        (price.property_id and price.property.owner_id != current_user.id) or
        (price.creator_id != current_user.id)
    ):
        flash('You do not have permission to delete this price.', 'danger')
        return redirect(url_for('invoicing.prices'))
    
    db.session.delete(price)
    db.session.commit()
    
    flash('Price deleted successfully!', 'success')
    return redirect(url_for('invoicing.prices'))


@bp.route('/invoices')
@invoice_access_required
def invoices():
    """View all invoices"""
    # Initialize filter form
    form = InvoiceFilterForm()
    
    if current_user.is_admin():
        form.property.query = Property.query
    else:
        form.property.query = Property.query.filter_by(owner_id=current_user.id)
    
    # Base query
    query = Invoice.query
    
    # Property owners see invoices for their properties
    if current_user.is_property_owner() or current_user.is_property_manager():
        owned_property_ids = [p.id for p in current_user.properties]
        query = query.filter(Invoice.property_id.in_(owned_property_ids))
    
    # Apply filters if form is submitted
    if request.args:
        # Filter by property
        property_id = request.args.get('property')
        if property_id and property_id.isdigit():
            query = query.filter(Invoice.property_id == int(property_id))
        
        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter(Invoice.status == InvoiceStatus(status))
        
        # Filter by date range
        date_from = request.args.get('date_from')
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(or_(
                    Invoice.date_from >= from_date,
                    Invoice.date_to >= from_date
                ))
            except ValueError:
                pass
        
        date_to = request.args.get('date_to')
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(or_(
                    Invoice.date_from <= to_date,
                    Invoice.date_to <= to_date
                ))
            except ValueError:
                pass
        
        # Filter by paid status
        is_paid = request.args.get('is_paid')
        if is_paid == 'y':
            query = query.filter(Invoice.status == InvoiceStatus.PAID)
    
    # Order by created date (newest first)
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    return render_template('invoicing/invoices.html', 
                          title='Invoices', 
                          invoices=invoices,
                          form=form)

@bp.route('/invoices/create', methods=['GET', 'POST'])
@invoice_access_required
def create_invoice():
    """Create a new invoice"""
    form = InvoiceForm()
    
    # Set up query for properties owned by the current user
    if current_user.is_admin():
        form.property.query = Property.query
    else:
        form.property.query = Property.query.filter_by(owner_id=current_user.id)
    
    if form.validate_on_submit():
        # Create new invoice
        invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            title=form.title.data,
            description=form.description.data,
            property_id=form.property.data.id,
            date_from=form.date_from.data,
            date_to=form.date_to.data,
            tax_rate=form.tax_rate.data / 100.0 if form.tax_rate.data else 0.0,  # Convert percentage to decimal
            due_date=form.due_date.data,
            payment_notes=form.payment_notes.data,
            creator_id=current_user.id,
            status=InvoiceStatus.DRAFT
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    return render_template('invoicing/invoice_form.html', 
                          title='Create Invoice', 
                          form=form)

@bp.route('/invoices/<int:id>')
@invoice_access_required
def view_invoice(id):
    """View a single invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to view this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to view this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Get all items for this invoice
    items = invoice.items.all()
    
    return render_template('invoicing/invoice_view.html', 
                          title=f'Invoice: {invoice.invoice_number}', 
                          invoice=invoice,
                          items=items)

@bp.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
@invoice_access_required
def edit_invoice(id):
    """Edit an existing invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be edited
    if invoice.status not in [InvoiceStatus.DRAFT]:
        flash('This invoice cannot be edited because it has already been sent or paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    form = InvoiceForm()
    item_form = InvoiceItemForm()
    
    # Set up query for properties owned by the current user
    if current_user.is_admin():
        form.property.query = Property.query
    else:
        form.property.query = Property.query.filter_by(owner_id=current_user.id)
    
    if form.validate_on_submit():
        # Update invoice
        invoice.title = form.title.data
        invoice.description = form.description.data
        invoice.property_id = form.property.data.id
        invoice.date_from = form.date_from.data
        invoice.date_to = form.date_to.data
        invoice.tax_rate = form.tax_rate.data / 100.0 if form.tax_rate.data else 0.0  # Convert percentage to decimal
        invoice.due_date = form.due_date.data
        invoice.payment_notes = form.payment_notes.data
        
        # Recalculate totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        flash('Invoice updated successfully!', 'success')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    elif request.method == 'GET':
        # Populate form with existing data
        form.title.data = invoice.title
        form.description.data = invoice.description
        form.property.data = invoice.property
        form.date_from.data = invoice.date_from
        form.date_to.data = invoice.date_to
        form.tax_rate.data = invoice.tax_rate * 100.0 if invoice.tax_rate else 0.0  # Convert decimal to percentage
        form.due_date.data = invoice.due_date
        form.payment_notes.data = invoice.payment_notes
    
    # Get all items for this invoice
    items = invoice.items.all()
    
    # Get tasks and cleaning sessions for this property that could be added to the invoice
    property_id = invoice.property_id
    
    # Get completed tasks for this property within the date range
    tasks = []
    if invoice.date_from and invoice.date_to:
        tasks = Task.query.join(
            'properties'
        ).filter(
            Task.properties.any(property_id=property_id),
            Task.status == 'completed',
            Task.completed_at >= invoice.date_from,
            Task.completed_at <= invoice.date_to
        ).all()
    
    # Get cleaning sessions for this property within the date range
    cleaning_sessions = []
    if invoice.date_from and invoice.date_to:
        cleaning_sessions = CleaningSession.query.filter(
            CleaningSession.property_id == property_id,
            CleaningSession.end_time.isnot(None),
            CleaningSession.start_time >= invoice.date_from,
            CleaningSession.end_time <= invoice.date_to
        ).all()
    
    return render_template('invoicing/invoice_edit.html', 
                          title=f'Edit Invoice: {invoice.invoice_number}', 
                          form=form,
                          item_form=item_form,
                          invoice=invoice,
                          items=items,
                          tasks=tasks,
                          cleaning_sessions=cleaning_sessions)

@bp.route('/invoices/<int:id>/add_comment', methods=['GET', 'POST'])
@invoice_access_required
def add_invoice_comment(id):
    """Add comments to an invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    form = InvoiceCommentForm()
    
    if form.validate_on_submit():
        invoice.comments = form.comments.data
        db.session.commit()
        
        flash('Comments added to invoice successfully!', 'success')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    elif request.method == 'GET':
        form.comments.data = invoice.comments
    
    return render_template('invoicing/invoice_comment.html', 
                          title=f'Add Comments to Invoice: {invoice.invoice_number}', 
                          form=form,
                          invoice=invoice)

@bp.route('/invoices/<int:id>/add_item', methods=['POST'])
@invoice_access_required
def add_invoice_item(id):
    """Add an item to an invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be edited
    if invoice.status not in [InvoiceStatus.DRAFT]:
        flash('This invoice cannot be edited because it has already been sent or paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    form = InvoiceItemForm()
    
    if form.validate_on_submit():
        # Create new invoice item
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=form.description.data,
            quantity=form.quantity.data,
            unit_price=form.unit_price.data,
            amount=form.quantity.data * form.unit_price.data
        )
        
        # Add optional references if provided
        if form.task_id.data and form.task_id.data.isdigit():
            item.task_id = int(form.task_id.data)
        
        if form.cleaning_session_id.data and form.cleaning_session_id.data.isdigit():
            item.cleaning_session_id = int(form.cleaning_session_id.data)
        
        if form.service_type.data:
            item.service_type = ServiceType(form.service_type.data)
        
        db.session.add(item)
        
        # Recalculate invoice totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        flash('Item added to invoice successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('invoicing.edit_invoice', id=invoice.id))

@bp.route('/invoices/<int:invoice_id>/remove_item/<int:item_id>', methods=['POST'])
@invoice_access_required
def remove_invoice_item(invoice_id, item_id):
    """Remove an item from an invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    item = InvoiceItem.query.get_or_404(item_id)
    
    # Check if item belongs to this invoice
    if item.invoice_id != invoice.id:
        abort(404)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be edited
    if invoice.status not in [InvoiceStatus.DRAFT]:
        flash('This invoice cannot be edited because it has already been sent or paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    # Remove the item
    db.session.delete(item)
    
    # Recalculate invoice totals
    invoice.calculate_totals()
    
    db.session.commit()
    
    flash('Item removed from invoice successfully!', 'success')
    return redirect(url_for('invoicing.edit_invoice', id=invoice.id))

@bp.route('/invoices/<int:id>/send', methods=['POST'])
@invoice_access_required
def send_invoice(id):
    """Mark an invoice as sent"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be sent
    if invoice.status != InvoiceStatus.DRAFT:
        flash('This invoice has already been sent or paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    # Check if invoice has items
    if invoice.items.count() == 0:
        flash('Cannot send an empty invoice. Please add at least one item.', 'warning')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Update status
    invoice.status = InvoiceStatus.SENT
    db.session.commit()
    
    flash('Invoice marked as sent!', 'success')
    return redirect(url_for('invoicing.view_invoice', id=invoice.id))

@bp.route('/invoices/<int:id>/mark_paid', methods=['GET', 'POST'])
@invoice_access_required
def mark_invoice_paid(id):
    """Mark an invoice as paid with payment date"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be marked as paid
    if invoice.status not in [InvoiceStatus.SENT, InvoiceStatus.OVERDUE]:
        flash('This invoice cannot be marked as paid because it has not been sent or is already paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    form = PaymentForm()
    
    if form.validate_on_submit():
        # Mark as paid with the specified payment date
        invoice.mark_as_paid(payment_date=form.payment_date.data)
        invoice.payment_notes = form.payment_notes.data
        db.session.commit()
        
        flash('Invoice marked as paid!', 'success')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    elif request.method == 'GET':
        # Pre-populate with today's date
        form.payment_date.data = datetime.utcnow().date()
        form.payment_notes.data = invoice.payment_notes
    
    return render_template('invoicing/mark_paid.html', 
                          title=f'Mark Invoice as Paid: {invoice.invoice_number}', 
                          form=form,
                          invoice=invoice)

@bp.route('/invoices/<int:id>/cancel', methods=['POST'])
@invoice_access_required
def cancel_invoice(id):
    """Cancel an invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be cancelled
    if invoice.status == InvoiceStatus.PAID:
        flash('This invoice cannot be cancelled because it has already been paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    # Update status
    invoice.status = InvoiceStatus.CANCELLED
    db.session.commit()
    
    flash('Invoice cancelled!', 'success')
    return redirect(url_for('invoicing.view_invoice', id=invoice.id))

@bp.route('/invoices/<int:id>/delete', methods=['POST'])
@invoice_access_required
def delete_invoice(id):
    """Delete an invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Check if user has permission to delete this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to delete this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be deleted
    if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED]:
        flash('This invoice cannot be deleted because it has already been sent or paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    # Delete the invoice
    db.session.delete(invoice)
    db.session.commit()
    
    flash('Invoice deleted successfully!', 'success')
    return redirect(url_for('invoicing.invoices'))


@bp.route('/invoices/generate_from_tasks', methods=['GET', 'POST'])
@invoice_access_required
def generate_from_tasks():
    """Generate an invoice from completed tasks"""
    if request.method == 'POST':
        # Get form data
        property_id = request.form.get('property_id')
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        
        if not property_id or not date_from or not date_to:
            flash('Please provide all required fields.', 'danger')
            return redirect(url_for('invoicing.invoices'))
        
        # Convert dates
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('invoicing.invoices'))
        
        # Get property
        property = Property.query.get_or_404(property_id)
        
        # Check if user has permission to create invoices for this property
        if not current_user.is_admin() and property.owner_id != current_user.id:
            flash('You do not have permission to create invoices for this property.', 'danger')
            return redirect(url_for('invoicing.invoices'))
        
        # Create new invoice
        invoice = Invoice(
            invoice_number=Invoice.generate_invoice_number(),
            title=f"Invoice for {property.name} - {date_from.strftime('%b %d')} to {date_to.strftime('%b %d, %Y')}",
            description=f"Services performed at {property.name} from {date_from.strftime('%b %d')} to {date_to.strftime('%b %d, %Y')}",
            property_id=property.id,
            date_from=date_from,
            date_to=date_to,
            creator_id=current_user.id,
            status=InvoiceStatus.DRAFT,
            due_date=(datetime.utcnow() + timedelta(days=30)).date()  # Due in 30 days
        )
        
        db.session.add(invoice)
        db.session.flush()  # Get the invoice ID without committing
        
        # Get completed tasks for this property within the date range
        tasks = Task.query.join(
            'properties'
        ).filter(
            Task.properties.any(property_id=property.id),
            Task.status == 'completed',
            Task.completed_at >= date_from,
            Task.completed_at <= date_to
        ).all()
        
        # Add tasks to invoice
        for task in tasks:
            # Try to find a price for this task's service type
            service_type = None
            for assignment in task.assignments:
                if assignment.service_type:
                    service_type = assignment.service_type
                    break
            
            if not service_type:
                # Skip tasks without a service type
                continue
            
            # Look for a price specific to this property first, then fall back to global price
            price = TaskPrice.query.filter_by(
                service_type=service_type,
                property_id=property.id
            ).first()
            
            if not price:
                price = TaskPrice.query.filter_by(
                    service_type=service_type,
                    property_id=None
                ).first()
            
            if not price:
                # Skip tasks without a price
                continue
            
            # Calculate price based on pricing model
            amount = 0
            if price.pricing_model == PricingModel.FIXED:
                amount = price.fixed_price
            elif price.pricing_model == PricingModel.HOURLY:
                # Look for cleaning sessions associated with this task
                cleaning_session = CleaningSession.query.filter_by(
                    task_id=task.id
                ).filter(CleaningSession.end_time.isnot(None)).first()
                
                if cleaning_session and cleaning_session.duration_minutes:
                    amount = price.calculate_price(cleaning_session.duration_minutes)
                else:
                    # Skip tasks without a duration
                    continue
            
            # Create invoice item
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=f"{service_type.name.replace('_', ' ').title()}: {task.title}",
                quantity=1,
                unit_price=amount,
                amount=amount,
                task_id=task.id,
                service_type=service_type
            )
            
            db.session.add(item)
        
        # Calculate invoice totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        flash('Invoice generated successfully!', 'success')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # GET request - show form
    properties = []
    if current_user.is_admin():
        properties = Property.query.all()
    else:
        properties = current_user.properties
    
    return render_template('invoicing/generate_invoice.html', 
                          title='Generate Invoice from Tasks', 
                          properties=properties)

@bp.route('/invoices/add_task/<int:invoice_id>/<int:task_id>', methods=['GET'])
@invoice_access_required
def add_task_to_invoice(invoice_id, task_id):
    """Add a task to an invoice with automatic pricing"""
    invoice = Invoice.query.get_or_404(invoice_id)
    task = Task.query.get_or_404(task_id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be edited
    if invoice.status not in [InvoiceStatus.DRAFT]:
        flash('This invoice cannot be edited because it has already been sent or paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    # Check if task is already on this invoice
    existing_item = InvoiceItem.query.filter_by(
        invoice_id=invoice.id,
        task_id=task.id
    ).first()
    
    if existing_item:
        flash('This task is already on the invoice.', 'warning')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Try to find a service type for this task
    service_type = None
    for assignment in task.assignments:
        if assignment.service_type:
            service_type = assignment.service_type
            break
    
    if not service_type:
        flash('Could not determine service type for this task. Please add it manually.', 'warning')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Look for a price specific to this property first, then fall back to global price
    price = TaskPrice.query.filter_by(
        service_type=service_type,
        property_id=invoice.property_id
    ).first()
    
    if not price:
        price = TaskPrice.query.filter_by(
            service_type=service_type,
            property_id=None
        ).first()
    
    if not price:
        flash('No price found for this service type. Please add the task manually.', 'warning')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Calculate price based on pricing model
    amount = 0
    if price.pricing_model == PricingModel.FIXED:
        amount = price.fixed_price
    elif price.pricing_model == PricingModel.HOURLY:
        # Look for cleaning sessions associated with this task
        cleaning_session = CleaningSession.query.filter_by(
            task_id=task.id
        ).filter(CleaningSession.end_time.isnot(None)).first()
        
        if cleaning_session and cleaning_session.duration_minutes:
            amount = price.calculate_price(cleaning_session.duration_minutes)
        else:
            flash('No duration found for this task. Please add it manually.', 'warning')
            return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Create invoice item
    item = InvoiceItem(
        invoice_id=invoice.id,
        description=f"{service_type.name.replace('_', ' ').title()}: {task.title}",
        quantity=1,
        unit_price=amount,
        amount=amount,
        task_id=task.id,
        service_type=service_type
    )
    
    db.session.add(item)
    
    # Recalculate invoice totals
    invoice.calculate_totals()
    
    db.session.commit()
    
    flash('Task added to invoice successfully!', 'success')
    return redirect(url_for('invoicing.edit_invoice', id=invoice.id))

@bp.route('/invoices/add_session/<int:invoice_id>/<int:session_id>', methods=['GET'])
@invoice_access_required
def add_session_to_invoice(invoice_id, session_id):
    """Add a cleaning session to an invoice with automatic pricing"""
    invoice = Invoice.query.get_or_404(invoice_id)
    session = CleaningSession.query.get_or_404(session_id)
    
    # Check if user has permission to edit this invoice
    if not current_user.is_admin() and invoice.property.owner_id != current_user.id:
        flash('You do not have permission to edit this invoice.', 'danger')
        return redirect(url_for('invoicing.invoices'))
    
    # Check if invoice is in a state that can be edited
    if invoice.status not in [InvoiceStatus.DRAFT]:
        flash('This invoice cannot be edited because it has already been sent or paid.', 'warning')
        return redirect(url_for('invoicing.view_invoice', id=invoice.id))
    
    # Check if session is already on this invoice
    existing_item = InvoiceItem.query.filter_by(
        invoice_id=invoice.id,
        cleaning_session_id=session.id
    ).first()
    
    if existing_item:
        flash('This cleaning session is already on the invoice.', 'warning')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Check if session has a duration
    if not session.duration_minutes:
        flash('This cleaning session does not have a duration. Please add it manually.', 'warning')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Use CLEANING service type for cleaning sessions
    service_type = ServiceType.CLEANING
    
    # Look for a price specific to this property first, then fall back to global price
    price = TaskPrice.query.filter_by(
        service_type=service_type,
        property_id=invoice.property_id
    ).first()
    
    if not price:
        price = TaskPrice.query.filter_by(
            service_type=service_type,
            property_id=None
        ).first()
    
    if not price:
        flash('No price found for cleaning services. Please add the session manually.', 'warning')
        return redirect(url_for('invoicing.edit_invoice', id=invoice.id))
    
    # Calculate price based on pricing model
    amount = 0
    description = "Cleaning"
    
    if session.associated_task:
        description = f"Cleaning: {session.associated_task.title}"
    
    if price.pricing_model == PricingModel.FIXED:
        amount = price.fixed_price
    elif price.pricing_model == PricingModel.HOURLY:
        amount = price.calculate_price(session.duration_minutes)
    
    # Create invoice item
    item = InvoiceItem(
        invoice_id=invoice.id,
        description=description,
        quantity=1,
        unit_price=amount,
        amount=amount,
        cleaning_session_id=session.id,
        service_type=service_type
    )
    
    db.session.add(item)
    
    # Recalculate invoice totals
    invoice.calculate_totals()
    
    db.session.commit()
    
    flash('Cleaning session added to invoice successfully!', 'success')
    return redirect(url_for('invoicing.edit_invoice', id=invoice.id))

def get_date_range_for_report(report_type, year=None, month=None, week=None, date_from=None, date_to=None):
    """Get the date range for a report based on the report type and parameters"""
    today = datetime.utcnow().date()
    
    if report_type == 'custom' and date_from and date_to:
        return date_from, date_to
    
    if not year:
        year = today.year
    
    if report_type == 'weekly' and week:
        # Calculate the first day of the year
        first_day = date(year, 1, 1)
        # Calculate the first day of the week (Monday)
        first_monday = first_day + timedelta(days=(7 - first_day.weekday()) % 7)
        # Calculate the start date of the specified week
        start_date = first_monday + timedelta(weeks=week-1)
        # End date is 6 days after start date
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    
    elif report_type == 'monthly' and month:
        # Get the last day of the month
        _, last_day = monthrange(year, month)
        return date(year, month, 1), date(year, month, last_day)
    
    elif report_type == 'annual':
        return date(year, 1, 1), date(year, 12, 31)
    
    # Default to current month if no valid parameters
    return date(today.year, today.month, 1), today

@bp.route('/reports', methods=['GET', 'POST'])
@maintenance_staff_required
def financial_reports():
    """View financial reports with role-based access controls"""
    form = ReportFilterForm()
    
    # Set up property choices based on user role
    if current_user.is_admin():
        form.property.query = Property.query
        form.service_provider.query = User.query.filter(
            User.role.in_([UserRoles.MAINTENANCE, UserRoles.CLEANER])
        )
    elif current_user.is_property_owner():
        # Property owners see only their properties
        form.property.query = Property.query.filter_by(owner_id=current_user.id)
        # Property owners can see all service providers who worked on their properties
        service_providers = User.query.join(
            TaskAssignment, TaskAssignment.user_id == User.id
        ).join(
            Task, Task.id == TaskAssignment.task_id
        ).join(
            'properties'
        ).filter(
            Property.owner_id == current_user.id,
            User.role.in_([UserRoles.MAINTENANCE, UserRoles.CLEANER])
        ).distinct()
        form.service_provider.query = service_providers
    elif current_user.is_property_manager():
        # Property managers see properties they manage
        managed_properties = Property.query.join(
            TaskAssignment, TaskAssignment.property_id == Property.id
        ).filter(
            TaskAssignment.user_id == current_user.id
        )
        form.property.query = managed_properties
        
        # Property managers can see service providers who worked on properties they manage
        service_providers = User.query.join(
            TaskAssignment, TaskAssignment.user_id == User.id
        ).join(
            Task, Task.id == TaskAssignment.task_id
        ).join(
            'properties'
        ).join(
            TaskAssignment, TaskAssignment.property_id == Property.id
        ).filter(
            TaskAssignment.user_id == current_user.id,
            User.role.in_([UserRoles.MAINTENANCE, UserRoles.CLEANER])
        ).distinct()
        form.service_provider.query = service_providers
    else:
        # Maintenance staff can only see their own data
        form.property.query = Property.query.filter(Property.id.in_([]))  # Empty query
        form.service_provider.query = User.query.filter(User.id == current_user.id)
    
    # Initialize report data
    report_data = []
    total_earnings = 0
    date_from = None
    date_to = None
    
    if request.method == 'POST' and form.validate():
        # Get date range based on report type
        date_from, date_to = get_date_range_for_report(
            form.report_type.data,
            year=form.year.data,
            month=form.month.data if form.report_type.data == 'monthly' else None,
            week=form.week.data if form.report_type.data == 'weekly' else None,
            date_from=form.date_from.data,
            date_to=form.date_to.data
        )
        
        # Base query for invoices
        query = Invoice.query.filter(
            Invoice.status == InvoiceStatus.PAID,
            Invoice.paid_date >= date_from,
            Invoice.paid_date <= date_to
        )
        
        # Apply property filter if specified
        if form.property.data:
            query = query.filter(Invoice.property_id == form.property.data.id)
        
        # Apply role-based access controls
        if current_user.is_admin():
            # Admins can see all invoices
            pass
        elif current_user.is_property_owner():
            # Property owners see invoices for their properties
            owned_property_ids = [p.id for p in current_user.properties]
            query = query.filter(Invoice.property_id.in_(owned_property_ids))
        elif current_user.is_property_manager():
            # Property managers see invoices for properties they manage
            managed_property_ids = [p.id for p in form.property.query.all()]
            query = query.filter(Invoice.property_id.in_(managed_property_ids))
        else:
            # Maintenance staff see only invoices for tasks they worked on
            query = query.join(
                InvoiceItem, InvoiceItem.invoice_id == Invoice.id
            ).join(
                Task, Task.id == InvoiceItem.task_id
            ).join(
                TaskAssignment, TaskAssignment.task_id == Task.id
            ).filter(
                TaskAssignment.user_id == current_user.id
            )
        
        # Apply service provider filter if specified (for admins, property owners, managers)
        if form.service_provider.data and (current_user.is_admin() or 
                                          current_user.is_property_owner() or 
                                          current_user.is_property_manager()):
            query = query.join(
                InvoiceItem, InvoiceItem.invoice_id == Invoice.id
            ).join(
                Task, Task.id == InvoiceItem.task_id
            ).join(
                TaskAssignment, TaskAssignment.task_id == Task.id
            ).filter(
                TaskAssignment.user_id == form.service_provider.data.id
            )
        
        # Get invoices
        invoices = query.distinct().all()
        
        # Process invoices for report
        for invoice in invoices:
            # For maintenance staff, only include items they worked on
            if current_user.role in [UserRoles.MAINTENANCE, UserRoles.CLEANER]:
                items = []
                for item in invoice.items:
                    if item.task_id:
                        # Check if this staff worked on this task
                        assignment = TaskAssignment.query.filter_by(
                            task_id=item.task_id,
                            user_id=current_user.id
                        ).first()
                        if assignment:
                            items.append(item)
                
                if not items:
                    continue  # Skip invoices where staff didn't work on any items
                
                # Calculate total for just this staff's items
                staff_total = sum(item.amount for item in items)
                
                report_data.append({
                    'invoice': invoice,
                    'items': items,
                    'total': staff_total
                })
                total_earnings += staff_total
            else:
                # For other roles, include all items
                report_data.append({
                    'invoice': invoice,
                    'items': invoice.items.all(),
                    'total': invoice.total
                })
                total_earnings += invoice.total
    
    return render_template('invoicing/reports.html',
                          title='Financial Reports',
                          form=form,
                          report_data=report_data,
                          total_earnings=total_earnings,
                          date_from=date_from,
                          date_to=date_to)