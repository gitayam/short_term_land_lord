from flask import render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.inventory import bp
from app.inventory.forms import InventoryItemForm, InventoryTransactionForm, InventoryTransferForm, InventoryFilterForm, InventoryCatalogItemForm, BarcodeSearchForm
from app.models import Property, InventoryItem, InventoryTransaction, ItemCategory, TransactionType, User, UserRoles, NotificationType, NotificationChannel, InventoryCatalogItem
from app.notifications.service import create_notification
from datetime import datetime
import json
from app.auth.decorators import property_owner_required, admin_required

def can_manage_inventory(property_id):
    """Check if the current user can manage inventory for the specified property.
    
    Args:
        property_id: The ID of the property to check
        
    Returns:
        bool: True if user can manage, False otherwise
    """
    # Admin users can manage inventory for any property
    if current_user.has_admin_role:
        return True
        
    property = Property.query.get(property_id)
    if not property:
        return False
        
    # Property owners can manage their own properties
    if property.owner_id == current_user.id:
        return True
    
    # Property managers can manage properties they are assigned to
    if current_user.is_property_manager:
        return property.is_managed_by(current_user)
        
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
        query = query.join(InventoryCatalogItem).filter(InventoryCatalogItem.category == filter_form.category.data)
    
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
        query = query.join(InventoryCatalogItem).filter(
            InventoryCatalogItem.name.ilike(search) | 
            InventoryCatalogItem.description.ilike(search) |
            InventoryItem.storage_location.ilike(search)
        )
    
    if filter_form.barcode.data:
        query = query.join(InventoryCatalogItem).filter(InventoryCatalogItem.barcode == filter_form.barcode.data)
    
    # Get inventory items
    inventory_items = query.order_by(InventoryItem.id).all()
    
    # Check if user can manage inventory
    can_manage = can_manage_inventory(property_id)
    
    return render_template('inventory/index.html', 
                          title=f'Inventory - {property.name}',
                          property=property,
                          inventory_items=inventory_items,
                          filter_form=filter_form,
                          can_manage=can_manage,
                          is_property_owner=current_user.is_property_owner)

@bp.route('/catalog')
@login_required
def catalog_index():
    """Display the global inventory catalog"""
    # Check if user is authorized (admin or property owner)
    if not (current_user.is_property_owner or current_user.has_admin_role):
        flash('Access denied. This page is only available to property owners and administrators.', 'danger')
        return redirect(url_for('main.index'))
    
    # Initialize filter form
    filter_form = InventoryFilterForm(request.args)
    
    # Apply filters
    query = InventoryCatalogItem.query
    
    if filter_form.category.data:
        query = query.filter_by(category=filter_form.category.data)
    
    if filter_form.search.data:
        search = f"%{filter_form.search.data}%"
        query = query.filter(InventoryCatalogItem.name.ilike(search) | 
                            InventoryCatalogItem.description.ilike(search) |
                            InventoryCatalogItem.sku.ilike(search))
    
    if filter_form.barcode.data:
        query = query.filter(InventoryCatalogItem.barcode == filter_form.barcode.data)
    
    # Get catalog items
    catalog_items = query.order_by(InventoryCatalogItem.name).all()
    
    return render_template('inventory/catalog_index.html', 
                          title='Global Inventory Catalog',
                          catalog_items=catalog_items,
                          filter_form=filter_form)

@bp.route('/catalog/add', methods=['GET', 'POST'])
@login_required
def add_catalog_item():
    """Add a new item to the global catalog"""
    # Check if user is authorized (admin or property owner)
    if not (current_user.is_property_owner or current_user.has_admin_role):
        flash('Access denied. This page is only available to property owners and administrators.', 'danger')
        return redirect(url_for('main.index'))
    
    form = InventoryCatalogItemForm()
    
    if form.validate_on_submit():
        # Convert the category string to an ItemCategory enum instance
        try:
            category = ItemCategory(form.category.data)
        except ValueError:
            flash(f'Invalid category: {form.category.data}', 'danger')
            return render_template('inventory/catalog_form.html', title='Add Catalog Item', form=form)
            
        catalog_item = InventoryCatalogItem(
            name=form.name.data,
            description=form.description.data,
            unit=form.unit.data,
            unit_price=form.unit_price.data or 0.0,
            currency=form.currency.data or 'USD',
            creator_id=current_user.id
        )
        db.session.add(catalog_item)
        db.session.commit()
        
        flash(f'Catalog item "{catalog_item.name}" added successfully!', 'success')
        
        # Check if we should redirect back to a specific page
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('inventory.catalog_index'))
    
    return render_template('inventory/catalog_form.html',
                          title='Add Catalog Item',
                          form=form)

@bp.route('/catalog/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_catalog_item(item_id):
    """Edit an existing catalog item"""
    # Check if user is authorized (admin or property owner)
    if not (current_user.is_property_owner or current_user.has_admin_role):
        flash('Access denied. This page is only available to property owners and administrators.', 'danger')
        return redirect(url_for('main.index'))
    
    catalog_item = InventoryCatalogItem.query.get_or_404(item_id)
    form = InventoryCatalogItemForm(obj=catalog_item)
    
    if form.validate_on_submit():
        # Get form data
        catalog_item.name = form.name.data
        try:
            # We can't save category directly to the model as it doesn't have this field
            category = ItemCategory(form.category.data)
        except ValueError:
            flash(f'Invalid category: {form.category.data}', 'danger')
            return render_template('inventory/catalog_form.html', title='Edit Catalog Item', form=form, item=catalog_item)
            
        catalog_item.unit = form.unit.data
        catalog_item.description = form.description.data
        catalog_item.unit_price = form.unit_price.data or 0.0
        catalog_item.currency = form.currency.data or 'USD'
        
        db.session.commit()
        
        flash(f'Catalog item "{catalog_item.name}" updated successfully!', 'success')
        return redirect(url_for('inventory.catalog_index'))
    
    return render_template('inventory/catalog_form.html',
                          title='Edit Catalog Item',
                          form=form,
                          item=catalog_item)

@bp.route('/catalog/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_catalog_item(item_id):
    """Delete a catalog item"""
    # Check if user is authorized (admin or property owner)
    if not (current_user.is_property_owner or current_user.has_admin_role):
        flash('Access denied. This page is only available to property owners and administrators.', 'danger')
        return redirect(url_for('main.index'))
    
    catalog_item = InventoryCatalogItem.query.get_or_404(item_id)
    
    # Check if this catalog item is used in any property inventory
    if catalog_item.inventory_instances.count() > 0:
        flash(f'Cannot delete "{catalog_item.name}" because it is used in property inventory. Remove all instances first.', 'danger')
        return redirect(url_for('inventory.catalog_index'))
    
    item_name = catalog_item.name
    db.session.delete(catalog_item)
    db.session.commit()
    
    flash(f'Catalog item "{item_name}" deleted successfully!', 'success')
    return redirect(url_for('inventory.catalog_index'))

@bp.route('/property/<int:property_id>/inventory/add', methods=['GET', 'POST'])
@login_required
def add_item(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Check if user can manage inventory
    if not can_manage_inventory(property_id):
        flash('Access denied. You do not have permission to manage inventory for this property.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    form = InventoryItemForm()
    
    # Set up the catalog item choices
    form.catalog_item_id.query = InventoryCatalogItem.query.order_by(InventoryCatalogItem.name)
    
    if form.validate_on_submit():
        # Check if this catalog item already exists in this property
        existing_item = InventoryItem.query.filter_by(
            property_id=property_id,
            catalog_item_id=form.catalog_item_id.data.id
        ).first()
        
        if existing_item:
            flash(f'This item already exists in this property. Please edit the existing item instead.', 'danger')
            return redirect(url_for('inventory.edit_item', property_id=property_id, item_id=existing_item.id))
        
        item = InventoryItem(
            property_id=property_id,
            catalog_item_id=form.catalog_item_id.data.id,
            current_quantity=form.current_quantity.data,
            storage_location=form.storage_location.data,
            reorder_threshold=form.reorder_threshold.data
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
        flash(f'Inventory item "{item.catalog_item.name}" added successfully!', 'success')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    return render_template('inventory/item_form.html',
                          title='Add Inventory Item',
                          form=form,
                          property=property,
                          is_property_owner=current_user.is_property_owner)

@bp.route('/property/<int:property_id>/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(property_id, item_id):
    property = Property.query.get_or_404(property_id)
    item = InventoryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to this property
    if item.property_id != property_id:
        abort(404)
    
    # Check if user can manage inventory
    if not can_manage_inventory(property_id):
        flash('Access denied. You do not have permission to manage inventory for this property.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    form = InventoryItemForm(obj=item)
    
    # Set up the catalog item choices
    form.catalog_item_id.query = InventoryCatalogItem.query.order_by(InventoryCatalogItem.name)
    
    if form.validate_on_submit():
        # Check if quantity changed
        old_quantity = item.current_quantity
        new_quantity = form.current_quantity.data
        
        # Update item details
        item.catalog_item_id = form.catalog_item_id.data.id
        item.current_quantity = new_quantity
        item.storage_location = form.storage_location.data
        item.reorder_threshold = form.reorder_threshold.data
        
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
        flash(f'Inventory item "{item.catalog_item.name}" updated successfully!', 'success')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    return render_template('inventory/item_form.html',
                          title='Edit Inventory Item',
                          form=form,
                          property=property,
                          item=item,
                          is_property_owner=current_user.is_property_owner)

@bp.route('/property/<int:property_id>/inventory/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(property_id, item_id):
    property = Property.query.get_or_404(property_id)
    item = InventoryItem.query.get_or_404(item_id)
    
    # Ensure the item belongs to this property
    if item.property_id != property_id:
        abort(404)
    
    # Check if user can manage inventory
    if not can_manage_inventory(property_id):
        flash('Access denied. You do not have permission to manage inventory for this property.', 'danger')
        return redirect(url_for('inventory.index', property_id=property_id))
    
    item_name = item.catalog_item.name
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
            title = f"Low Inventory Alert: {item.catalog_item.name}"
            message = f"The inventory level for {item.catalog_item.name} at {property.name} is low.\n"
            message += f"Current quantity: {item.current_quantity} {item.catalog_item.unit_of_measure}\n"
            message += f"Reorder threshold: {item.reorder_threshold} {item.catalog_item.unit_of_measure}\n"
            
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
    if current_user.is_property_owner:
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
            flash(f'Cannot transfer more than the available quantity ({item.current_quantity} {item.catalog_item.unit_of_measure}).', 'danger')
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
        
        # Check if the same catalog item exists in the destination property
        dest_item = InventoryItem.query.filter_by(
            property_id=destination_property.id,
            catalog_item_id=item.catalog_item_id
        ).first()
        
        if not dest_item:
            # Create a new item in the destination property
            dest_item = InventoryItem(
                property_id=destination_property.id,
                catalog_item_id=item.catalog_item_id,
                current_quantity=0,
                storage_location=item.storage_location,
                reorder_threshold=item.reorder_threshold
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
            title = f"Low Inventory Alert: {item.catalog_item.name}"
            message = f"The inventory level for {item.catalog_item.name} at {property.name} is low after a transfer.\n"
            message += f"Current quantity: {item.current_quantity} {item.catalog_item.unit_of_measure}\n"
            message += f"Reorder threshold: {item.reorder_threshold} {item.catalog_item.unit_of_measure}\n"
            
            # Create in-app notification for property owner
            create_notification(
                user_id=property.owner_id,
                notification_type=NotificationType.INVENTORY_LOW,
                channel=NotificationChannel.IN_APP,
                title=title,
                message=message
            )
        
        db.session.commit()
        flash(f'Successfully transferred {quantity} {item.catalog_item.unit_of_measure} of {item.catalog_item.name} to {destination_property.name}!', 'success')
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
                          title=f'Transaction History - {item.catalog_item.name}',
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

@bp.route('/barcode-search')
@login_required
def barcode_search():
    """Search for an item by barcode"""
    barcode = request.args.get('barcode', '')
    
    if not barcode:
        return jsonify({'found': False, 'message': 'No barcode provided'})
    
    # Search for the item in the catalog
    catalog_item = InventoryCatalogItem.query.filter_by(barcode=barcode).first()
    
    if not catalog_item:
        return jsonify({'found': False, 'message': 'No item found with this barcode'})
    
    # Return the item details
    return jsonify({
        'found': True,
        'item': {
            'id': catalog_item.id,
            'name': catalog_item.name,
            'category': catalog_item.category.value,
            'unit_of_measure': catalog_item.unit_of_measure,
            'description': catalog_item.description or ''
        }
    })