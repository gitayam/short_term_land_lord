"""
Routes for guidebook management
"""
import os
import json
from flask import (
    render_template, redirect, url_for, flash, request, 
    current_app, jsonify, abort, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from app import db
from app.guidebook import bp
from app.models import Property, GuidebookEntry, GuidebookCategory
from app.forms.guidebook_forms import (
    GuidebookEntryForm, GuidebookSearchForm, GuidebookBulkActionForm, QuickAddForm
)
from app.utils.error_handling import handle_errors, ValidationError, NotFoundError
try:
    from app.utils.validation import sanitize_filename, validate_coordinate
except ImportError:
    def sanitize_filename(*args, **kwargs):
        return args[0] if args else "default"
    def validate_coordinate(*args, **kwargs):
        pass
from app.utils.performance import timed_operation
from sqlalchemy import or_


@bp.route('/property/<int:property_id>')
@login_required
@handle_errors
def property_guidebook(property_id):
    """Display guidebook entries for a property"""
    property = Property.query.get_or_404(property_id)
    
    # Check permissions
    if not property.is_visible_to(current_user):
        abort(403)
    
    # Get search/filter form
    search_form = GuidebookSearchForm()
    
    # Build query
    query = GuidebookEntry.query.filter_by(property_id=property_id)
    
    # Apply filters from request args
    category = request.args.get('category')
    search_term = request.args.get('search')
    featured_only = request.args.get('featured_only') == 'on'
    
    if category:
        try:
            category_enum = GuidebookCategory(category)
            query = query.filter_by(category=category_enum)
        except ValueError:
            pass
    
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(or_(
            GuidebookEntry.title.ilike(search_pattern),
            GuidebookEntry.description.ilike(search_pattern),
            GuidebookEntry.address.ilike(search_pattern),
            GuidebookEntry.host_tip.ilike(search_pattern)
        ))
    
    if featured_only:
        query = query.filter_by(is_featured=True)
    
    # Get entries ordered by sort_order and title
    entries = query.filter_by(is_active=True).order_by(
        GuidebookEntry.sort_order, GuidebookEntry.title
    ).all()
    
    # Group entries by category for display
    entries_by_category = {}
    for entry in entries:
        category_name = entry.get_category_display()
        if category_name not in entries_by_category:
            entries_by_category[category_name] = []
        entries_by_category[category_name].append(entry)
    
    # Get stats
    stats = {
        'total_entries': len(entries),
        'featured_count': len([e for e in entries if e.is_featured]),
        'categories_count': len(entries_by_category),
        'entries_with_coordinates': len([e for e in entries if e.has_coordinates()])
    }
    
    return render_template('guidebook/property_guidebook.html',
                          property=property,
                          entries_by_category=entries_by_category,
                          stats=stats,
                          search_form=search_form)


@bp.route('/property/<int:property_id>/entry/new', methods=['GET', 'POST'])
@login_required
@handle_errors
def add_entry(property_id):
    """Add a new guidebook entry"""
    property = Property.query.get_or_404(property_id)
    
    # Check permissions
    if not property.is_visible_to(current_user):
        abort(403)
    
    form = GuidebookEntryForm()
    form.property_id.data = property_id
    
    if form.validate_on_submit():
        # Create new entry
        entry = GuidebookEntry(
            property_id=property_id,
            title=form.title.data,
            description=form.description.data,
            category=GuidebookCategory(form.category.data),
            address=form.address.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            website_url=form.website_url.data,
            phone_number=form.phone_number.data,
            price_range=form.price_range.data,
            host_notes=form.host_notes.data,
            host_tip=form.host_tip.data,
            recommended_for=form.recommended_for.data,
            is_featured=form.is_featured.data,
            is_active=form.is_active.data,
            sort_order=form.sort_order.data or 0,
            created_by=current_user.id
        )
        
        # Handle opening hours
        if form.opening_hours_text.data:
            # Convert simple text to structured format
            # This is a basic implementation - could be enhanced
            entry.opening_hours = json.dumps({'general': form.opening_hours_text.data})
        
        # Handle image upload
        image_saved = False
        if form.image.data:
            image_saved = save_entry_image(entry, form.image.data, property_id)
        elif form.image_url.data:
            entry.image_url = form.image_url.data
            image_saved = True
        
        try:
            db.session.add(entry)
            db.session.commit()
            
            if image_saved:
                flash(f'Guidebook entry "{entry.title}" created successfully with image!', 'success')
            else:
                flash(f'Guidebook entry "{entry.title}" created successfully!', 'success')
            
            return redirect(url_for('guidebook.property_guidebook', property_id=property_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating guidebook entry: {str(e)}')
            flash('Error creating guidebook entry. Please try again.', 'danger')
    
    return render_template('guidebook/edit_entry.html',
                          title='Add Guidebook Entry',
                          form=form,
                          property=property)


@bp.route('/entry/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
@handle_errors
def edit_entry(entry_id):
    """Edit an existing guidebook entry"""
    entry = GuidebookEntry.query.get_or_404(entry_id)
    property = entry.property_ref
    
    # Check permissions
    if not property.is_visible_to(current_user):
        abort(403)
    
    form = GuidebookEntryForm(obj=entry)
    form.property_id.data = property.id
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.category.data = entry.category.value
        form.opening_hours_text.data = entry.get_opening_hours_display()
    
    if form.validate_on_submit():
        # Update entry fields
        entry.title = form.title.data
        entry.description = form.description.data
        entry.category = GuidebookCategory(form.category.data)
        entry.address = form.address.data
        entry.latitude = form.latitude.data
        entry.longitude = form.longitude.data
        entry.website_url = form.website_url.data
        entry.phone_number = form.phone_number.data
        entry.price_range = form.price_range.data
        entry.host_notes = form.host_notes.data
        entry.host_tip = form.host_tip.data
        entry.recommended_for = form.recommended_for.data
        entry.is_featured = form.is_featured.data
        entry.is_active = form.is_active.data
        entry.sort_order = form.sort_order.data or 0
        
        # Handle opening hours update
        if form.opening_hours_text.data:
            entry.opening_hours = json.dumps({'general': form.opening_hours_text.data})
        else:
            entry.opening_hours = None
        
        # Handle image updates
        if form.image.data:
            # Delete old image if exists
            if entry.image_path:
                delete_entry_image(entry.image_path)
            save_entry_image(entry, form.image.data, property.id)
        elif form.image_url.data != entry.image_url:
            # Clear local image if switching to URL
            if entry.image_path:
                delete_entry_image(entry.image_path)
                entry.image_path = None
            entry.image_url = form.image_url.data
        
        try:
            db.session.commit()
            flash(f'Guidebook entry "{entry.title}" updated successfully!', 'success')
            return redirect(url_for('guidebook.property_guidebook', property_id=property.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating guidebook entry: {str(e)}')
            flash('Error updating guidebook entry. Please try again.', 'danger')
    
    return render_template('guidebook/edit_entry.html',
                          title='Edit Guidebook Entry',
                          form=form,
                          property=property,
                          entry=entry)


@bp.route('/entry/<int:entry_id>/delete', methods=['POST'])
@login_required
@handle_errors
def delete_entry(entry_id):
    """Delete a guidebook entry"""
    entry = GuidebookEntry.query.get_or_404(entry_id)
    property = entry.property_ref
    
    # Check permissions
    if not property.is_visible_to(current_user):
        abort(403)
    
    try:
        # Delete associated image if exists
        if entry.image_path:
            delete_entry_image(entry.image_path)
        
        entry_title = entry.title
        db.session.delete(entry)
        db.session.commit()
        
        flash(f'Guidebook entry "{entry_title}" deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting guidebook entry: {str(e)}')
        flash('Error deleting guidebook entry. Please try again.', 'danger')
    
    return redirect(url_for('guidebook.property_guidebook', property_id=property.id))


@bp.route('/api/property/<int:property_id>/entries')
@login_required
@handle_errors
def api_property_entries(property_id):
    """API endpoint to get guidebook entries for a property"""
    property = Property.query.get_or_404(property_id)
    
    # Check permissions - allow guests with valid token
    if not property.is_visible_to(current_user):
        # Check for guest access token
        guest_token = request.args.get('token')
        if not guest_token or guest_token != property.guest_access_token:
            abort(403)
    
    entries_data = GuidebookEntry.get_map_data_for_property(property_id)
    
    return jsonify({
        'success': True,
        'property_id': property_id,
        'property_name': property.name,
        'entries': entries_data,
        'total_count': len(entries_data)
    })


@bp.route('/api/entry/<int:entry_id>')
@login_required
@handle_errors
def api_entry_details(entry_id):
    """API endpoint to get detailed information about a specific entry"""
    entry = GuidebookEntry.query.get_or_404(entry_id)
    property = entry.property_ref
    
    # Check permissions
    if not property.is_visible_to(current_user):
        # Check for guest access token
        guest_token = request.args.get('token')
        if not guest_token or guest_token != property.guest_access_token:
            abort(403)
    
    entry_data = entry.get_map_data()
    if entry_data:
        # Add additional details for API response
        entry_data.update({
            'opening_hours_display': entry.get_opening_hours_display(),
            'host_notes': entry.host_notes if current_user.is_authenticated else None,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat()
        })
    
    return jsonify({
        'success': True,
        'entry': entry_data
    })


@bp.route('/property/<int:property_id>/quick-add', methods=['GET', 'POST'])
@login_required
@handle_errors
def quick_add(property_id):
    """Quick add form for basic guidebook entries"""
    property = Property.query.get_or_404(property_id)
    
    # Check permissions
    if not property.is_visible_to(current_user):
        abort(403)
    
    form = QuickAddForm()
    
    if form.validate_on_submit():
        entry = GuidebookEntry(
            property_id=property_id,
            title=form.title.data,
            description=form.host_tip.data or f"Recommended {form.category.data.replace('_', ' ')}",
            category=GuidebookCategory(form.category.data),
            address=form.address.data,
            website_url=form.website_url.data,
            host_tip=form.host_tip.data,
            is_active=True,
            created_by=current_user.id
        )
        
        try:
            db.session.add(entry)
            db.session.commit()
            flash(f'"{entry.title}" added to guidebook!', 'success')
            return redirect(url_for('guidebook.property_guidebook', property_id=property_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating quick entry: {str(e)}')
            flash('Error adding entry. Please try again.', 'danger')
    
    return render_template('guidebook/quick_add.html',
                          title='Quick Add Entry',
                          form=form,
                          property=property)


def save_entry_image(entry, image_file, property_id):
    """Save uploaded image for guidebook entry"""
    try:
        if not image_file:
            return False
        
        # Create directory structure
        upload_dir = os.path.join(
            current_app.config['LOCAL_STORAGE_PATH'],
            'guidebook',
            str(property_id)
        )
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(image_file.filename)
        if not filename:
            filename = f"entry_{entry.id or 'new'}_{int(time.time())}.jpg"
        
        # Add entry ID prefix if available
        if hasattr(entry, 'id') and entry.id:
            name, ext = os.path.splitext(filename)
            filename = f"entry_{entry.id}_{name}{ext}"
        
        filepath = os.path.join(upload_dir, filename)
        
        # Save and optimize image
        image_file.save(filepath)
        
        # Optimize image using PIL
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large (max 1200x1200)
                max_size = (1200, 1200)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized version
                img.save(filepath, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            current_app.logger.warning(f'Image optimization failed: {e}')
        
        # Store relative path
        relative_path = os.path.join('guidebook', str(property_id), filename)
        entry.image_path = relative_path
        
        # Clear image URL if image file is uploaded
        entry.image_url = None
        
        return True
        
    except Exception as e:
        current_app.logger.error(f'Error saving entry image: {str(e)}')
        return False


def delete_entry_image(image_path):
    """Delete guidebook entry image file"""
    try:
        if image_path:
            full_path = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], image_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
    except Exception as e:
        current_app.logger.error(f'Error deleting entry image: {str(e)}')
    return False


@bp.route('/images/<path:filename>')
def serve_image(filename):
    """Serve guidebook images"""
    upload_dir = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], 'guidebook')
    return send_from_directory(upload_dir, filename)