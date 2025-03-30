from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.inventory import bp
from app.inventory.forms import InventoryItemForm, InventoryTransactionForm, InventoryTransferForm, InventoryFilterForm
from app.models import Property, InventoryItem, InventoryTransaction, ItemCategory, TransactionType, User, UserRoles, NotificationType, NotificationChannel
from app.notifications.service import create_notification
from datetime import datetime
import json

def property_owner_required(f):
    """Decorator to ensure only property owners can access a route"""
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_property_owner():
            flash('Access denied. You must be a property owner to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def can_manage_inventory(property_id):
    """Check if the current user can manage inventory for this property"""
    property = Property.query.get_or_404(property_id)
    
    # Property owners can manage their own properties
    if current_user.is_property_owner() and property.owner_id == current_user.id:
        return True
    
    # Cleaners can update inventory counts but not add/remove items
    if current_user.is_cleaner():
        return True
    
    return False

@bp.route('/property/<int:property_id>/inventory')
@login_required
def index(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if user can view this property
    if not property.is_visible_to(current_user):
        flash('Access denied. You can only view inventory for properties you have access to.', 'danger')
        return redirect(url_for('main.index'))
    
    # Initialize filter form
    filter_form = InventoryFilterForm(request.args)
    
    # Apply filters
    query = InventoryItem.query.filter_by(property_id=property_id)
    
    if filter_form.category.data:
        query = query.filter_by(category=filter_form.category.data)
    
    if filter_form.low_stock_only.data == 'low':
        # This is a bit complex as we need to filter items below their threshold
        # We'll use a subquery approach
        low_stock_items = []
        for item in query.all():
            if item.is_low_stock():
                low_stock_items.append(item.id)
        
        if low_stock_items:
            query = query.filter(InventoryItem.id.in_(low_stock_items))
        else:
            query = query.filter(InventoryItem.id == None)  # No results
    
    if filter_form.search.data:
        search = f"%{filter_form.search.data}%"
        query = query.filter(InventoryItem.name.ilike(search) | 
                            InventoryItem.description.ilike(search) |
                            InventoryItem.storage_location.ilike(search))
    
    # Get inventory items
    inventory_items = query.order_by(InventoryItem.name).all()
    
    # Check if user can manage inventory
    can_manage = can_manage_inventory(property_id)
    
    return render_template('inventory/index.html', 
                          title=f'Inventory - {property.name}',
                          property=property,
                          inventory_items=inventory_items,
                          filter_form=filter_form,
                          can_manage=can_manage,
                          is_property_owner=current_user.is_property_owner())

@bp.route('/property/<int:property_id>/inventory/add', methods=['GET', 'POST'])
@property_owner_required
def add_item(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only manage inventory for your own properties.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    form = InventoryItemForm()
    
    if form.validate_on_submit():
        item = InventoryItem(
            property_id=property_id,
            name=form.name.data,
            category=form.category.data,
            current_quantity=form.current_quantity.data,
            unit_of_measure=form.unit_of_measure.data,
            storage_location=form.storage_location.data,
            sku=form.sku.data,
            description=form.description.data,
            reorder_threshold=form.reorder_threshold.data,
            unit_cost=form.unit_cost.data,
            purchase_link=form.purchase_link.data
        )
        db.session.add(item)
        
        # Create initial transaction record for the starting quantity
        transaction = InventoryTransaction(
            item=item,
            transaction_type=TransactionType.RESTOCK,
            quantity=form.current_quantity.data,
            previous_quantity=0,
            new_quantity=form.current_quantity.data,
            user_id=current_user.id,
            notes="Initial inventory setup"
        )
        db.session.add(transaction)
        
        db.session.commit()
        flash(f'Inventory item "{item.name}" added successfully!', 'success')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    return render_template('inventory/item_form.html',
                          title='Add Inventory Item',
                          form=form,
                          property=property)

@bp.route('/property/<int:property_id>/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
@property_owner_required
def edit_item(property_id, item_id):
    property = Property.query.get_or_404(property_id)
    item = InventoryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to this property
    if item.property_id != property_id:
        abort(404)
    
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only manage inventory for your own properties.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    form = InventoryItemForm(obj=item)
    
    if form.validate_on_submit():
        # Check if quantity changed
        old_quantity = item.current_quantity
        new_quantity = form.current_quantity.data
        
        # Update item details
        form.populate_obj(item)
        
        # If quantity changed, create a transaction record
        if old_quantity != new_quantity:
            transaction = InventoryTransaction(
                item=item,
                transaction_type=TransactionType.ADJUSTMENT,
                quantity=abs(new_quantity - old_quantity),
                previous_quantity=old_quantity,
                new_quantity=new_quantity,
                user_id=current_user.id,
                notes="Quantity adjusted during item edit"
            )
            db.session.add(transaction)
        
        db.session.commit()
        flash(f'Inventory item "{item.name}" updated successfully!', 'success')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    return render_template('inventory/item_form.html',
                          title='Edit Inventory Item',
                          form=form,
                          property=property,
                          item=item)

@bp.route('/property/<int:property_id>/inventory/<int:item_id>/delete', methods=['POST'])
@property_owner_required
def delete_item(property_id, item_id):
    property = Property.query.get_or_404(property_id)
    item = InventoryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to this property
    if item.property_id != property_id:
        abort(404)
    
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only manage inventory for your own properties.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    item_name = item.name
    db.session.delete(item)
    db.session.commit()
    
    flash(f'Inventory item "{item_name}" deleted successfully!', 'success')
    return redirect(url_for('inventory.index', property_id=property_id))

@bp.route('/property/<int:property_id>/inventory/<int:item_id>/transaction', methods=['GET', 'POST'])
@login_required
def record_transaction(property_id, item_id):
    property = Property.query.get_or_404(property_id)
    item = InventoryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to this property
    if item.property_id != property_id:
        abort(404)
    
    # Check if user can manage inventory
    if not can_manage_inventory(property_id):
        flash('Access denied. You do not have permission to record inventory transactions.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    form = InventoryTransactionForm()
    form.item_id.data = item_id
    
    if form.validate_on_submit():
        transaction_type = TransactionType(form.transaction_type.data)
        quantity = form.quantity.data
        previous_quantity = item.current_quantity
        
        # Update item quantity
        item.update_quantity(quantity, transaction_type)
        
        # Create transaction record
        transaction = InventoryTransaction(
            item=item,
            transaction_type=transaction_type,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=item.current_quantity,
            user_id=current_user.id,
            notes=form.notes.data
        )
        db.session.add(transaction)
        
        # Check if item is now below threshold and notify if needed
        if item.is_low_stock() and transaction_type in [TransactionType.USAGE, TransactionType.TRANSFER_OUT]:
            # Notify property owner
            title = f"Low Inventory Alert: {item.name}"
            message = f"The inventory level for {item.name} at {property.name} is low.\n"
            message += f"Current quantity: {item.current_quantity} {item.unit_of_measure}\n"
            message += f"Reorder threshold: {item.reorder_threshold} {item.unit_of_measure}\n"
            
            # Create in-app notification for property owner
            create_notification(
                user_id=property.owner_id,
                notification_type=NotificationType.INVENTORY_LOW,
                channel=NotificationChannel.IN_APP,
                title=title,
                message=message
            )
        
        db.session.commit()
        flash(f'Transaction recorded successfully!', 'success')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    return render_template('inventory/transaction_form.html',
                          title='Record Inventory Transaction',
                          form=form,
                          property=property,
                          item=item)

@bp.route('/property/<int:property_id>/inventory/<int:item_id>/transfer', methods=['GET', 'POST'])
@login_required
def transfer_item(property_id, item_id):
    property = Property.query.get_or_404(property_id)
    item = InventoryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to this property
    if item.property_id != property_id:
        abort(404)
    
    # Check if user can manage inventory
    if not can_manage_inventory(property_id):
        flash('Access denied. You do not have permission to transfer inventory.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    form = InventoryTransferForm()
    form.item_id.data = item_id
    
    # Get properties that the user can transfer to
    if current_user.is_property_owner():
        # Property owners can transfer to their own properties
        available_properties = Property.query.filter_by(owner_id=current_user.id).filter(Property.id != property_id).all()
    else:
        # Cleaners can see all properties but can't transfer between them
        available_properties = []
    
    form.destination_property.query = Property.query.filter(Property.id.in_([p.id for p in available_properties]))
    
    if form.validate_on_submit():
        quantity = form.quantity.data
        destination_property = form.destination_property.data
        
        # Ensure quantity is not more than available
        if quantity > item.current_quantity:
            flash(f'Cannot transfer more than the available quantity ({item.current_quantity} {item.unit_of_measure}).', 'danger')
            return redirect(url_for('inventory.transfer_item', property_id=property_id, item_id=item_id))
        
        # Create outgoing transaction
        previous_quantity = item.current_quantity
        item.update_quantity(quantity, TransactionType.TRANSFER_OUT)
        
        outgoing_transaction = InventoryTransaction(
            item=item,
            transaction_type=TransactionType.TRANSFER_OUT,
            quantity=quantity,
            previous_quantity=previous_quantity,
            new_quantity=item.current_quantity,
            user_id=current_user.id,
            source_property_id=property_id,
            destination_property_id=destination_property.id,
            notes=form.notes.data
        )
        db.session.add(outgoing_transaction)
        
        # Check if the same item exists in the destination property
        dest_item = InventoryItem.query.filter_by(
            property_id=destination_property.id,
            name=item.name,
            unit_of_measure=item.unit_of_measure
        ).first()
        
        if not dest_item:
            # Create a new item in the destination property
            dest_item = InventoryItem(
                property_id=destination_property.id,
                name=item.name,
                category=item.category,
                current_quantity=0,
                unit_of_measure=item.unit_of_measure,
                storage_location=item.storage_location,
                sku=item.sku,
                description=item.description,
                reorder_threshold=item.reorder_threshold,
                unit_cost=item.unit_cost,
                purchase_link=item.purchase_link
            )
            db.session.add(dest_item)
            db.session.flush()  # Generate ID for the new item
        
        # Create incoming transaction
        previous_dest_quantity = dest_item.current_quantity
        dest_item.update_quantity(quantity, TransactionType.TRANSFER_IN)
        
        incoming_transaction = InventoryTransaction(
            item=dest_item,
            transaction_type=TransactionType.TRANSFER_IN,
            quantity=quantity,
            previous_quantity=previous_dest_quantity,
            new_quantity=dest_item.current_quantity,
            user_id=current_user.id,
            source_property_id=property_id,
            destination_property_id=destination_property.id,
            notes=form.notes.data
        )
        db.session.add(incoming_transaction)
        
        # Check if source item is now below threshold
        if item.is_low_stock():
            # Notify property owner
            title = f"Low Inventory Alert: {item.name}"
            message = f"The inventory level for {item.name} at {property.name} is low after a transfer.\n"
            message += f"Current quantity: {item.current_quantity} {item.unit_of_measure}\n"
            message += f"Reorder threshold: {item.reorder_threshold} {item.unit_of_measure}\n"
            
            # Create in-app notification for property owner
            create_notification(
                user_id=property.owner_id,
                notification_type=NotificationType.INVENTORY_LOW,
                channel=NotificationChannel.IN_APP,
                title=title,
                message=message
            )
        
        db.session.commit()
        flash(f'Successfully transferred {quantity} {item.unit_of_measure} of {item.name} to {destination_property.name}!', 'success')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    return render_template('inventory/transfer_form.html',
                          title='Transfer Inventory Item',
                          form=form,
                          property=property,
                          item=item,
                          available_properties=available_properties)

@bp.route('/property/<int:property_id>/inventory/<int:item_id>/history')
@login_required
def item_history(property_id, item_id):
    property = Property.query.get_or_404(property_id)
    item = InventoryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to this property
    if item.property_id != property_id:
        abort(404)
    
    # Check if user can view this property
    if not property.is_visible_to(current_user):
        flash('Access denied. You can only view inventory for properties you have access to.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get transaction history
    transactions = InventoryTransaction.query.filter_by(item_id=item_id).order_by(InventoryTransaction.created_at.desc()).all()
    
    return render_template('inventory/item_history.html',
                          title=f'Transaction History - {item.name}',
                          property=property,
                          item=item,
                          transactions=transactions)

@bp.route('/property/<int:property_id>/inventory/low-stock')
@login_required
def low_stock(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if user can view this property
    if not property.is_visible_to(current_user):
        flash('Access denied. You can only view inventory for properties you have access to.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all inventory items for this property
    items = InventoryItem.query.filter_by(property_id=property_id).all()
    
    # Filter to only low stock items
    low_stock_items = [item for item in items if item.is_low_stock()]
    
    return render_template('inventory/low_stock.html',
                          title=f'Low Stock Items - {property.name}',
                          property=property,
                          low_stock_items=low_stock_items)
