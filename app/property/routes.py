from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.property import bp
from app.property.forms import PropertyForm, PropertyImageForm, PropertyCalendarForm
from app.models import Property, PropertyImage, UserRoles, PropertyCalendar
from datetime import datetime, timedelta
import os
import uuid
import requests
from icalendar import Calendar
from dateutil import rrule, parser
import pytz

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

@bp.route('/')
@property_owner_required
def index():
    properties = Property.query.filter_by(owner_id=current_user.id).order_by(Property.created_at.desc()).all()
    return render_template('property/index.html', title='My Properties', properties=properties)

@bp.route('/create', methods=['GET', 'POST'])
@property_owner_required
def create():
    form = PropertyForm()
    if form.validate_on_submit():
        property = Property(
            name=form.name.data,
            description=form.description.data,
            street_address=form.street_address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            country=form.country.data,
            property_type=form.property_type.data,
            bedrooms=form.bedrooms.data,
            bathrooms=form.bathrooms.data,
            square_feet=form.square_feet.data,
            year_built=form.year_built.data,
            owner_id=current_user.id
        )
        db.session.add(property)
        db.session.commit()
        flash('Property created successfully!', 'success')
        return redirect(url_for('property.view', id=property.id))
    return render_template('property/create.html', title='Add Property', form=form)

@bp.route('/<int:id>')
@property_owner_required
def view(id):
    property = Property.query.get_or_404(id)
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only view your own properties.', 'danger')
        return redirect(url_for('property.index'))
    return render_template('property/view.html', title=property.name, property=property)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@property_owner_required
def edit(id):
    property = Property.query.get_or_404(id)
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only edit your own properties.', 'danger')
        return redirect(url_for('property.index'))
    
    form = PropertyForm()
    if form.validate_on_submit():
        property.name = form.name.data
        property.description = form.description.data
        property.street_address = form.street_address.data
        property.city = form.city.data
        property.state = form.state.data
        property.zip_code = form.zip_code.data
        property.country = form.country.data
        property.property_type = form.property_type.data
        property.bedrooms = form.bedrooms.data
        property.bathrooms = form.bathrooms.data
        property.square_feet = form.square_feet.data
        property.year_built = form.year_built.data
        property.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Property updated successfully!', 'success')
        return redirect(url_for('property.view', id=property.id))
    elif request.method == 'GET':
        form.name.data = property.name
        form.description.data = property.description
        form.street_address.data = property.street_address
        form.city.data = property.city
        form.state.data = property.state
        form.zip_code.data = property.zip_code
        form.country.data = property.country
        form.property_type.data = property.property_type
        form.bedrooms.data = property.bedrooms
        form.bathrooms.data = property.bathrooms
        form.square_feet.data = property.square_feet
        form.year_built.data = property.year_built
    
    return render_template('property/edit.html', title=f'Edit {property.name}', form=form, property=property)

@bp.route('/<int:id>/delete', methods=['POST'])
@property_owner_required
def delete(id):
    property = Property.query.get_or_404(id)
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only delete your own properties.', 'danger')
        return redirect(url_for('property.index'))
    
    # Delete the property
    db.session.delete(property)
    db.session.commit()
    flash('Property deleted successfully!', 'success')
    return redirect(url_for('property.index'))

@bp.route('/<int:id>/images', methods=['GET', 'POST'])
@property_owner_required
def manage_images(id):
    property = Property.query.get_or_404(id)
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only manage images for your own properties.', 'danger')
        return redirect(url_for('property.index'))
    
    form = PropertyImageForm()
    if form.validate_on_submit():
        # Handle image upload
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        # Generate a unique filename to prevent collisions
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'static/uploads/properties', str(property.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, unique_filename)
        image_file.save(file_path)
        
        # Create database record
        is_primary = bool(int(form.is_primary.data))
        
        # If this is set as primary, unset any existing primary images
        if is_primary:
            PropertyImage.query.filter_by(property_id=property.id, is_primary=True).update({'is_primary': False})
        
        # Create the new image record
        image = PropertyImage(
            property_id=property.id,
            image_path=f'/static/uploads/properties/{property.id}/{unique_filename}',
            is_primary=is_primary,
            caption=form.caption.data
        )
        db.session.add(image)
        db.session.commit()
        
        flash('Image uploaded successfully!', 'success')
        return redirect(url_for('property.manage_images', id=property.id))
    
    images = PropertyImage.query.filter_by(property_id=property.id).all()
    return render_template('property/images.html', title=f'Manage Images - {property.name}', 
                          form=form, property=property, images=images)

@bp.route('/images/<int:image_id>/delete', methods=['POST'])
@property_owner_required
def delete_image(image_id):
    image = PropertyImage.query.get_or_404(image_id)
    property = Property.query.get_or_404(image.property_id)
    
    # Ensure the current user is the owner of the property
    if property.owner_id != current_user.id:
        flash('Access denied. You can only delete images for your own properties.', 'danger')
        return redirect(url_for('property.index'))
    
    # Delete the image file from the filesystem
    try:
        file_path = os.path.join(current_app.root_path, image.image_path.lstrip('/'))
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Log the error but continue with database deletion
        print(f"Error deleting file: {e}")
    
    # Delete the database record
    db.session.delete(image)
    db.session.commit()
    
    flash('Image deleted successfully!', 'success')
    return redirect(url_for('property.manage_images', id=property.id))

@bp.route('/images/<int:image_id>/set-primary', methods=['POST'])
@property_owner_required
def set_primary_image(image_id):
    image = PropertyImage.query.get_or_404(image_id)
    property = Property.query.get_or_404(image.property_id)
    
    # Ensure the current user is the owner of the property
    if property.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('property.index'))
    
    # Unset any existing primary images
    PropertyImage.query.filter_by(property_id=property.id, is_primary=True).update({'is_primary': False})
    
    # Set this image as primary
    image.is_primary = True
    db.session.commit()
    
    flash('Primary image updated successfully!', 'success')
    return redirect(url_for('property.manage_images', id=property.id))

@bp.route('/property/<int:id>/calendars')
@login_required
def manage_calendars(id):
    property = Property.query.get_or_404(id)
    
    # Check if user is authorized to view this property
    if not property.is_visible_to(current_user):
        abort(403)
    
    # Get all calendars for this property
    calendars = PropertyCalendar.query.filter_by(property_id=id).all()
    
    return render_template('property/calendars.html', property=property, calendars=calendars)

@bp.route('/property/<int:id>/calendar/add', methods=['GET', 'POST'])
@login_required
def add_calendar(id):
    property = Property.query.get_or_404(id)
    
    # Check if user is authorized to edit this property
    if property.user_id != current_user.id:
        abort(403)
    
    form = PropertyCalendarForm()
    
    if form.validate_on_submit():
        calendar = PropertyCalendar(
            property_id=id,
            name=form.name.data,
            ical_url=form.ical_url.data,
            service=form.service.data,
            is_entire_property=form.is_entire_property.data,
            room_name=None if form.is_entire_property.data else form.room_name.data
        )
        
        # Try to sync the calendar
        try:
            response = requests.get(form.ical_url.data)
            if response.status_code == 200:
                # Try to parse the iCal data to validate
                cal = Calendar.from_ical(response.text)
                
                # Set sync status
                calendar.last_synced = datetime.utcnow()
                calendar.sync_status = 'Success'
            else:
                calendar.sync_status = 'Error'
                calendar.sync_error = f"HTTP error: {response.status_code}"
        except Exception as e:
            calendar.sync_status = 'Failed'
            calendar.sync_error = str(e)[:255]  # Limit error message length
        
        db.session.add(calendar)
        db.session.commit()
        
        flash('Calendar added successfully!', 'success')
        return redirect(url_for('property.manage_calendars', id=id))
    
    return render_template('property/calendar_form.html', form=form, property=property, title='Add Calendar')

@bp.route('/property/<int:property_id>/calendar/<int:calendar_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_calendar(property_id, calendar_id):
    property = Property.query.get_or_404(property_id)
    calendar = PropertyCalendar.query.get_or_404(calendar_id)
    
    # Check if user is authorized to edit this property
    if property.user_id != current_user.id:
        abort(403)
    
    # Check if calendar belongs to this property
    if calendar.property_id != property_id:
        abort(404)
    
    form = PropertyCalendarForm(obj=calendar)
    
    if form.validate_on_submit():
        form.populate_obj(calendar)
        
        # Update room_name based on is_entire_property
        if calendar.is_entire_property:
            calendar.room_name = None
        
        # Try to sync the calendar
        try:
            response = requests.get(calendar.ical_url)
            if response.status_code == 200:
                # Try to parse the iCal data to validate
                cal = Calendar.from_ical(response.text)
                
                # Set sync status
                calendar.last_synced = datetime.utcnow()
                calendar.sync_status = 'Success'
                calendar.sync_error = None
            else:
                calendar.sync_status = 'Error'
                calendar.sync_error = f"HTTP error: {response.status_code}"
        except Exception as e:
            calendar.sync_status = 'Failed'
            calendar.sync_error = str(e)[:255]  # Limit error message length
        
        db.session.commit()
        
        flash('Calendar updated successfully!', 'success')
        return redirect(url_for('property.manage_calendars', id=property_id))
    
    return render_template('property/calendar_form.html', form=form, property=property, title='Edit Calendar')

@bp.route('/property/<int:property_id>/calendar/<int:calendar_id>/delete', methods=['POST'])
@login_required
def delete_calendar(property_id, calendar_id):
    property = Property.query.get_or_404(property_id)
    calendar = PropertyCalendar.query.get_or_404(calendar_id)
    
    # Check if user is authorized to edit this property
    if property.user_id != current_user.id:
        abort(403)
    
    # Check if calendar belongs to this property
    if calendar.property_id != property_id:
        abort(404)
    
    db.session.delete(calendar)
    db.session.commit()
    
    flash('Calendar deleted successfully!', 'success')
    return redirect(url_for('property.manage_calendars', id=property_id))

@bp.route('/property/<int:property_id>/calendar/<int:calendar_id>/sync', methods=['POST'])
@login_required
def sync_calendar(property_id, calendar_id):
    property = Property.query.get_or_404(property_id)
    calendar = PropertyCalendar.query.get_or_404(calendar_id)
    
    # Check if user is authorized to edit this property
    if property.user_id != current_user.id:
        abort(403)
    
    # Check if calendar belongs to this property
    if calendar.property_id != property_id:
        abort(404)
    
    # Try to sync the calendar
    try:
        response = requests.get(calendar.ical_url)
        if response.status_code == 200:
            # Try to parse the iCal data to validate
            cal = Calendar.from_ical(response.text)
            
            # Set sync status
            calendar.last_synced = datetime.utcnow()
            calendar.sync_status = 'Success'
            calendar.sync_error = None
            
            flash('Calendar synced successfully!', 'success')
        else:
            calendar.sync_status = 'Error'
            calendar.sync_error = f"HTTP error: {response.status_code}"
            flash(f'Failed to sync calendar: HTTP error {response.status_code}', 'danger')
    except Exception as e:
        calendar.sync_status = 'Failed'
        calendar.sync_error = str(e)[:255]  # Limit error message length
        flash(f'Failed to sync calendar: {str(e)}', 'danger')
    
    db.session.commit()
    
    return redirect(url_for('property.manage_calendars', id=property_id))

@bp.route('/property/<int:id>/calendar')
@login_required
def view_calendar(id):
    property = Property.query.get_or_404(id)
    
    # Get all calendars for this property
    calendars = PropertyCalendar.query.filter_by(property_id=id).all()
    
    # Prepare events data for the calendar
    events = []
    
    for calendar in calendars:
        try:
            # Fetch the iCal data
            response = requests.get(calendar.ical_url)
            if response.status_code == 200:
                # Parse the iCal data
                cal = Calendar.from_ical(response.text)
                
                # Extract events
                for component in cal.walk():
                    if component.name == "VEVENT":
                        # Get event details
                        summary = str(component.get('summary', 'Booking'))
                        start_date = component.get('dtstart').dt
                        end_date = component.get('dtend').dt
                        
                        # Convert datetime objects to date if necessary
                        if isinstance(start_date, datetime):
                            start_date = start_date.date()
                        if isinstance(end_date, datetime):
                            end_date = end_date.date()
                        
                        # Add event to the list
                        event = {
                            'title': summary,
                            'start': start_date.isoformat(),
                            'end': end_date.isoformat(),
                            'className': f"{calendar.service.lower()}-event",
                            'extendedProps': {
                                'service': calendar.service,
                                'room': None if calendar.is_entire_property else calendar.room_name
                            }
                        }
                        events.append(event)
                
                # Update last_synced and status
                calendar.last_synced = datetime.utcnow()
                calendar.sync_status = 'Success'
                db.session.commit()
            else:
                # Update sync status
                calendar.sync_status = 'Error'
                calendar.sync_error = f"HTTP error: {response.status_code}"
                db.session.commit()
        except Exception as e:
            # Update sync status
            calendar.sync_status = 'Failed'
            calendar.sync_error = str(e)[:255]  # Limit error message length
            db.session.commit()
    
    return render_template('property/calendar_view.html', property=property, calendars=calendars, events=events)
