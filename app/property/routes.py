from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.property import bp
from app.property.forms import PropertyForm, PropertyImageForm, PropertyCalendarForm, RoomForm, GuestAccessForm
from app.models import Property, PropertyImage, UserRoles, PropertyCalendar, Room, RoomFurniture, Task, TaskProperty, CleaningSession, RepairRequest, ServiceType, GuestReview, TaskAssignment
from datetime import datetime, timedelta
import os
import uuid
import requests
from icalendar import Calendar
from dateutil import rrule, parser
import pytz
from sqlalchemy.orm import aliased
import secrets

def property_owner_required(f):
    """Decorator to ensure only property owners, admins, and property managers can access a route"""
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_property_owner or current_user.has_admin_role or current_user.is_property_manager):
            flash('Access denied. You must be a property owner, admin, or property manager to view this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/')
@property_owner_required
def index():
    # Get all properties if admin or property manager
    if current_user.has_admin_role or current_user.is_property_manager:
        properties = Property.query.order_by(Property.created_at.desc()).all()
    # Property owners see only their properties
    elif current_user.is_property_owner:
        properties = Property.query.filter_by(owner_id=current_user.id).order_by(Property.created_at.desc()).all()
    else:
        properties = []
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
            # Construct the full address from components
            address=f"{form.street_address.data}, {form.city.data}, {form.state.data} {form.zip_code.data}, {form.country.data}",
            property_type=form.property_type.data,
            bedrooms=form.bedrooms.data,
            bathrooms=form.bathrooms.data,
            square_feet=form.square_feet.data,
            ical_url=form.ical_url.data,
            
            # New fields
            checkin_time=form.checkin_time.data,
            checkout_time=form.checkout_time.data,
            trash_day=form.trash_day.data,
            recycling_day=form.recycling_day.data,
            recycling_notes=form.recycling_notes.data,
            
            # Utility information
            internet_provider=form.internet_provider.data,
            internet_account=form.internet_account.data,
            internet_contact=form.internet_contact.data,
            electric_provider=form.electric_provider.data,
            electric_account=form.electric_account.data,
            electric_contact=form.electric_contact.data,
            water_provider=form.water_provider.data,
            water_account=form.water_account.data,
            water_contact=form.water_contact.data,
            trash_provider=form.trash_provider.data,
            trash_account=form.trash_account.data,
            trash_contact=form.trash_contact.data,
            
            cleaning_supplies_location=form.cleaning_supplies_location.data,
            wifi_network=form.wifi_network.data,
            wifi_password=form.wifi_password.data,
            special_instructions=form.special_instructions.data,
            entry_instructions=form.entry_instructions.data,
            owner_id=current_user.id,
            
            # Generate guide book token
            guide_book_token=secrets.token_urlsafe(32)
        )
        db.session.add(property)
        db.session.commit()
        
        # Process room data from the form
        room_names = request.form.getlist('room_name')
        room_types = request.form.getlist('room_type')
        room_sqft = request.form.getlist('room_sqft')
        has_tvs = request.form.getlist('has_tv')
        tv_details = request.form.getlist('tv_details')
        bed_types = request.form.getlist('bed_type')
        has_showers = request.form.getlist('has_shower')
        has_tubs = request.form.getlist('has_tub')
        has_bathrooms = request.form.getlist('has_bathroom')
        
        # Create rooms
        for i in range(len(room_names)):
            if room_names[i]:  # Only create rooms with names
                room = Room(
                    property_id=property.id,
                    name=room_names[i],
                    room_type=room_types[i] if i < len(room_types) else 'other',
                    square_feet=int(room_sqft[i]) if i < len(room_sqft) and room_sqft[i] else None,
                    has_tv=f"new_{i}" in has_tvs,
                    tv_details=tv_details[i] if i < len(tv_details) and f"new_{i}" in has_tvs else None,
                    bed_type=bed_types[i] if i < len(bed_types) and bed_types[i] else None,
                    has_shower=f"new_{i}" in has_showers,
                    has_tub=f"new_{i}" in has_tubs,
                    has_bathroom=f"new_{i}" in has_bathrooms
                )
                db.session.add(room)
                db.session.flush()  # To get the room ID
                
                # Process furniture items for this room
                furniture_types = request.form.getlist(f'furniture_type_new_{i}[]')
                furniture_details = request.form.getlist(f'furniture_details_new_{i}[]')
                furniture_quantities = request.form.getlist(f'furniture_quantity_new_{i}[]')
                
                for j in range(len(furniture_types)):
                    if furniture_types[j]:  # Only create items with a type
                        furniture = RoomFurniture(
                            room_id=room.id,
                            name=furniture_types[j].title(),  # Use the furniture type as the name
                            furniture_type=furniture_types[j],
                            description=furniture_details[j] if j < len(furniture_details) else None,
                            quantity=int(furniture_quantities[j]) if j < len(furniture_quantities) and furniture_quantities[j] else 1
                        )
                        db.session.add(furniture)
        
        # Update property totals based on room data (re-query to get newly added rooms)
        db.session.commit()
        
        # Calculate totals
        bed_count = 0
        tv_count = 0
        shower_count = 0
        tub_count = 0
        bed_sizes_list = []
        
        rooms = Room.query.filter_by(property_id=property.id).all()
        for room in rooms:
            if room.bed_type:
                bed_count += 1
                bed_sizes_list.append(f"1 {room.bed_type.title()}")
            if room.has_tv:
                tv_count += 1
            if room.has_shower:
                shower_count += 1
            if room.has_tub:
                tub_count += 1
        
        property.total_beds = bed_count
        property.bed_sizes = ", ".join(bed_sizes_list) if bed_sizes_list else None
        property.number_of_tvs = tv_count
        property.number_of_showers = shower_count
        property.number_of_tubs = tub_count
        
        # If a main calendar URL was added, create a property calendar
        if property.ical_url:
            main_calendar = PropertyCalendar(
                property_id=property.id,
                name='Main Property Calendar',
                ical_url=property.ical_url,
                service='other',  # Default as "other" since we don't know the source
                is_entire_property=True
            )
            db.session.add(main_calendar)
            
            # Try to sync the calendar
            try:
                response = requests.get(property.ical_url)
                if response.status_code == 200:
                    # Try to parse the iCal data to validate
                    cal = Calendar.from_ical(response.text)
                    
                    # Set sync status
                    main_calendar.last_synced = datetime.utcnow()
                    main_calendar.sync_status = 'Success'
                    main_calendar.sync_error = None
                else:
                    main_calendar.sync_status = 'Error'
                    main_calendar.sync_error = f"HTTP error: {response.status_code}"
            except Exception as e:
                main_calendar.sync_status = 'Failed'
                main_calendar.sync_error = str(e)[:255]  # Limit error message length
        
        db.session.commit()
        flash('Property created successfully! 🎉', 'success')
        return redirect(url_for('property.view', id=property.id))
    
    return render_template('property/create.html', title='Add Property', form=form, rooms=[])

@bp.route('/<int:id>/view')
@login_required
def view(id):
    property = Property.query.get_or_404(id)
    
    # Permission check
    can_view = False
    
    # Property owners can view their own properties
    if current_user.is_property_owner and property.owner_id == current_user.id:
        can_view = True
    # Admins can view all properties
    elif current_user.has_admin_role:
        can_view = True
    # Property managers can view all properties
    elif current_user.is_property_manager:
        can_view = True
    # Service staff can view properties they have tasks for
    elif current_user.is_service_staff:
        # Use aliases to avoid duplicate table errors
        task_property_alias = aliased(TaskProperty)
        task_assignment_alias = aliased(TaskAssignment)
        
        # Check if the service staff has any assigned tasks for this property
        assigned_tasks = db.session.query(Task).join(
            task_property_alias, Task.id == task_property_alias.task_id
        ).filter(
            task_property_alias.property_id == property.id
        ).join(
            task_assignment_alias, Task.id == task_assignment_alias.task_id
        ).filter(
            task_assignment_alias.user_id == current_user.id
        ).first()
        
        if assigned_tasks:
            can_view = True
    
    if not can_view:
        flash('You do not have permission to view this property.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get guest review counts
    reviews_count = GuestReview.query.filter_by(property_id=id).count()
    
    # Get service history
    service_history = {}
    
    # Get tasks for this property
    tasks = db.session.query(Task).join(
        TaskProperty, TaskProperty.task_id == Task.id
    ).filter(
        TaskProperty.property_id == id
    ).order_by(Task.due_date.asc(), Task.priority.desc()).all()
    service_history['tasks'] = tasks
    
    # Get cleaning sessions for this property
    cleaning_sessions = CleaningSession.query.filter_by(property_id=id).all()
    service_history['cleaning_sessions'] = cleaning_sessions
    
    # Get repair requests for this property
    repair_requests = RepairRequest.query.filter_by(property_id=id).all()
    service_history['repair_requests'] = repair_requests
    
    # Get other services for this property
    other_services = []  # Add query for other services if available
    service_history['other_services'] = other_services
    
    # For service staff, also get their specific assigned tasks
    service_staff_tasks = []
    if current_user.is_service_staff:
        service_staff_tasks = db.session.query(Task).join(
            TaskProperty, TaskProperty.task_id == Task.id
        ).join(
            TaskAssignment, TaskAssignment.task_id == Task.id
        ).filter(
            TaskProperty.property_id == id,
            TaskAssignment.user_id == current_user.id
        ).order_by(Task.due_date.asc(), Task.priority.desc()).all()
    
    return render_template('property/view.html',
                          property=property,
                          reviews_count=reviews_count,
                          service_history=service_history,
                          service_staff_tasks=service_staff_tasks,
                          guest_review_count=reviews_count,
                          rooms_list=property.rooms if hasattr(property, 'rooms') else [])

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@property_owner_required
def edit(id):
    property = Property.query.get_or_404(id)
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only edit your own properties.', 'danger')
        return redirect(url_for('property.index'))
    
    form = PropertyForm()
    
    # Get all rooms for this property
    rooms = Room.query.filter_by(property_id=id).all()
    room_forms = []
    
    if form.validate_on_submit():
        property.name = form.name.data
        property.description = form.description.data
        property.street_address = form.street_address.data
        property.city = form.city.data
        property.state = form.state.data
        property.zip_code = form.zip_code.data
        property.country = form.country.data
        # Update the full address from components
        property.address = f"{form.street_address.data}, {form.city.data}, {form.state.data} {form.zip_code.data}, {form.country.data}"
        property.property_type = form.property_type.data
        property.bedrooms = form.bedrooms.data
        property.bathrooms = form.bathrooms.data
        property.square_feet = form.square_feet.data
        property.ical_url = form.ical_url.data
        
        # New fields
        property.checkin_time = form.checkin_time.data
        property.checkout_time = form.checkout_time.data
        property.trash_day = form.trash_day.data
        property.recycling_day = form.recycling_day.data
        property.recycling_notes = form.recycling_notes.data
        
        # Utility information
        property.internet_provider = form.internet_provider.data
        property.internet_account = form.internet_account.data
        property.internet_contact = form.internet_contact.data
        property.electric_provider = form.electric_provider.data
        property.electric_account = form.electric_account.data
        property.electric_contact = form.electric_contact.data
        property.water_provider = form.water_provider.data
        property.water_account = form.water_account.data
        property.water_contact = form.water_contact.data
        property.trash_provider = form.trash_provider.data
        property.trash_account = form.trash_account.data
        property.trash_contact = form.trash_contact.data
        
        # Update cleaner-specific info
        property.cleaning_supplies_location = form.cleaning_supplies_location.data
        property.wifi_network = form.wifi_network.data
        property.wifi_password = form.wifi_password.data
        property.special_instructions = form.special_instructions.data
        property.entry_instructions = form.entry_instructions.data
        
        property.updated_at = datetime.utcnow()
        
        # Process room data from the form
        existing_room_ids = [room.id for room in rooms]
        room_data = request.form.getlist('room_id')
        room_names = request.form.getlist('room_name')
        room_types = request.form.getlist('room_type')
        room_sqft = request.form.getlist('room_sqft')
        has_tvs = request.form.getlist('has_tv')
        tv_details = request.form.getlist('tv_details')
        bed_types = request.form.getlist('bed_type')
        has_showers = request.form.getlist('has_shower')
        has_tubs = request.form.getlist('has_tub')
        has_bathrooms = request.form.getlist('has_bathroom')
        room_deletes = request.form.getlist('room_delete')
        
        # Update existing rooms and create new ones
        for i in range(len(room_names)):
            if i < len(room_data) and room_data[i]:  # This is an existing room
                room_id = int(room_data[i])
                if str(room_id) in room_deletes:  # Delete the room
                    room = Room.query.get(room_id)
                    if room and room.property_id == property.id:
                        db.session.delete(room)
                else:  # Update the room
                    room = Room.query.get(room_id)
                    if room and room.property_id == property.id:
                        room.name = room_names[i]
                        room.room_type = room_types[i]
                        room.square_feet = int(room_sqft[i]) if room_sqft[i] else None
                        room.has_tv = str(room_id) in has_tvs
                        room.tv_details = tv_details[i] if str(room_id) in has_tvs else None
                        room.bed_type = bed_types[i] if bed_types[i] else None
                        room.has_shower = str(room_id) in has_showers
                        room.has_tub = str(room_id) in has_tubs
                        room.has_bathroom = str(room_id) in has_bathrooms
                        
                        # Process furniture items for this room
                        # First, delete all existing furniture
                        RoomFurniture.query.filter_by(room_id=room_id).delete()
                        
                        # Then add new furniture items
                        furniture_types = request.form.getlist(f'furniture_type_{room_id}[]')
                        furniture_details = request.form.getlist(f'furniture_details_{room_id}[]')
                        furniture_quantities = request.form.getlist(f'furniture_quantity_{room_id}[]')
                        
                        for j in range(len(furniture_types)):
                            if furniture_types[j]:  # Only create items with a type
                                furniture = RoomFurniture(
                                    room_id=room_id,
                                    name=furniture_types[j].title(),  # Use the furniture type as the name
                                    furniture_type=furniture_types[j],
                                    description=furniture_details[j] if j < len(furniture_details) else None,
                                    quantity=int(furniture_quantities[j]) if j < len(furniture_quantities) and furniture_quantities[j] else 1
                                )
                                db.session.add(furniture)
            else:  # This is a new room
                room = Room(
                    property_id=property.id,
                    name=room_names[i],
                    room_type=room_types[i],
                    square_feet=int(room_sqft[i]) if room_sqft[i] else None,
                    has_tv=f"new_{i}" in has_tvs,
                    tv_details=tv_details[i] if f"new_{i}" in has_tvs else None,
                    bed_type=bed_types[i] if bed_types[i] else None,
                    has_shower=f"new_{i}" in has_showers,
                    has_tub=f"new_{i}" in has_tubs,
                    has_bathroom=f"new_{i}" in has_bathrooms
                )
                db.session.add(room)
                db.session.flush()  # To get the room ID
                
                # Process furniture items for this room
                furniture_types = request.form.getlist(f'furniture_type_new_{i}[]')
                furniture_details = request.form.getlist(f'furniture_details_new_{i}[]')
                furniture_quantities = request.form.getlist(f'furniture_quantity_new_{i}[]')
                
                for j in range(len(furniture_types)):
                    if furniture_types[j]:  # Only create items with a type
                        furniture = RoomFurniture(
                            room_id=room.id,
                            name=furniture_types[j].title(),  # Use the furniture type as the name
                            furniture_type=furniture_types[j],
                            description=furniture_details[j] if j < len(furniture_details) else None,
                            quantity=int(furniture_quantities[j]) if j < len(furniture_quantities) and furniture_quantities[j] else 1
                        )
                        db.session.add(furniture)
        
        # Update property totals based on room data
        bed_count = 0
        tv_count = 0
        shower_count = 0
        tub_count = 0
        bed_sizes_list = []
        
        for room in property.rooms:
            if room.bed_type:
                bed_count += 1
                bed_sizes_list.append(f"1 {room.bed_type.title()}")
            if room.has_tv:
                tv_count += 1
            if room.has_shower:
                shower_count += 1
            if room.has_tub:
                tub_count += 1
        
        property.total_beds = bed_count
        property.bed_sizes = ", ".join(bed_sizes_list) if bed_sizes_list else None
        property.number_of_tvs = tv_count
        property.number_of_showers = shower_count
        property.number_of_tubs = tub_count
        
        # If a main calendar URL was added, create or update a property calendar
        if property.ical_url:
            # Check if a main calendar already exists
            main_calendar = PropertyCalendar.query.filter_by(
                property_id=property.id, 
                is_entire_property=True,
                name='Main Property Calendar'
            ).first()
            
            if main_calendar:
                # Update existing calendar
                main_calendar.ical_url = property.ical_url
            else:
                # Create new calendar
                main_calendar = PropertyCalendar(
                    property_id=property.id,
                    name='Main Property Calendar',
                    ical_url=property.ical_url,
                    service='other',  # Default as "other" since we don't know the source
                    is_entire_property=True
                )
                db.session.add(main_calendar)
                
            # Try to sync the calendar
            try:
                response = requests.get(property.ical_url)
                if response.status_code == 200:
                    # Try to parse the iCal data to validate
                    cal = Calendar.from_ical(response.text)
                    
                    # Set sync status
                    main_calendar.last_synced = datetime.utcnow()
                    main_calendar.sync_status = 'Success'
                    main_calendar.sync_error = None
                else:
                    main_calendar.sync_status = 'Error'
                    main_calendar.sync_error = f"HTTP error: {response.status_code}"
            except Exception as e:
                main_calendar.sync_status = 'Failed'
                main_calendar.sync_error = str(e)[:255]  # Limit error message length
            
        db.session.commit()
        flash('Property updated successfully! 🎉', 'success')
        return redirect(url_for('property.view', id=property.id))
    elif request.method == 'GET':
        # Populate the form with existing data
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
        form.ical_url.data = property.ical_url
        
        # Populate new fields
        form.checkin_time.data = property.checkin_time
        form.checkout_time.data = property.checkout_time
        form.trash_day.data = property.trash_day
        form.recycling_day.data = property.recycling_day
        form.recycling_notes.data = property.recycling_notes
        
        # Populate utility information
        form.internet_provider.data = property.internet_provider
        form.internet_account.data = property.internet_account
        form.internet_contact.data = property.internet_contact
        form.electric_provider.data = property.electric_provider
        form.electric_account.data = property.electric_account
        form.electric_contact.data = property.electric_contact
        form.water_provider.data = property.water_provider
        form.water_account.data = property.water_account
        form.water_contact.data = property.water_contact
        form.trash_provider.data = property.trash_provider
        form.trash_account.data = property.trash_account
        form.trash_contact.data = property.trash_contact
        
        # Populate cleaner-specific info
        form.cleaning_supplies_location.data = property.cleaning_supplies_location
        form.wifi_network.data = property.wifi_network
        form.wifi_password.data = property.wifi_password
        form.special_instructions.data = property.special_instructions
        form.entry_instructions.data = property.entry_instructions
        
        # Create a form for each existing room
        for room in rooms:
            room_form = RoomForm()
            room_form.name.data = room.name
            room_form.room_type.data = room.room_type
            room_form.square_feet.data = room.square_feet
            room_form.has_tv.data = room.has_tv
            room_form.tv_details.data = room.tv_details
            room_form.bed_type.data = room.bed_type
            room_form.has_shower.data = room.has_shower
            room_form.has_tub.data = room.has_tub
            room_forms.append((room.id, room_form))
    
    return render_template('property/edit.html', title=f'Edit {property.name}', 
                          form=form, property=property, rooms=room_forms)

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

@bp.route('/<int:id>/guest-access', methods=['GET', 'POST'])
@property_owner_required
def manage_guest_access(id):
    property = Property.query.get_or_404(id)
    # Ensure the current user is the owner
    if property.owner_id != current_user.id:
        flash('Access denied. You can only manage guest access for your own properties.', 'danger')
        return redirect(url_for('property.index'))
    
    form = GuestAccessForm(obj=property)
    
    if form.validate_on_submit():
        property.guest_access_enabled = form.guest_access_enabled.data
        property.guest_rules = form.guest_rules.data
        property.guest_checkin_instructions = form.guest_checkin_instructions.data
        property.guest_checkout_instructions = form.guest_checkout_instructions.data
        property.guest_wifi_instructions = form.guest_wifi_instructions.data
        property.local_attractions = form.local_attractions.data
        property.emergency_contact = form.emergency_contact.data
        property.guest_faq = form.guest_faq.data
        
        # Generate a new token if requested or if enabling access for the first time
        if form.regenerate_token.data or (property.guest_access_enabled and not property.guest_access_token):
            property.generate_guest_access_token()
        
        db.session.commit()
        flash('Guest access settings updated successfully!', 'success')
        return redirect(url_for('property.view', id=property.id))
    
    # Generate guest access URL for display
    guest_url = None
    if property.guest_access_token:
        guest_url = url_for('property.guest_view', token=property.guest_access_token, _external=True)
    
    return render_template('property/guest_access.html', 
                          title=f'Guest Access - {property.name}',
                          form=form, 
                          property=property,
                          guest_url=guest_url)

@bp.route('/guest/<token>')
def guest_view(token):
    # Find property by guest access token
    property = Property.query.filter_by(guest_access_token=token, guest_access_enabled=True).first_or_404()
    
    # Get rooms list
    rooms = property.rooms.all()
    
    return render_template('property/guest_view.html', 
                          title=f'Welcome to {property.name}',
                          property=property,
                          rooms=rooms)

@bp.route('/<int:id>/calendars')
@login_required
def manage_calendars(id):
    property = Property.query.get_or_404(id)
    
    # Check if user is authorized to view this property
    if not property.is_visible_to(current_user):
        abort(403)
    
    # Get all calendars for this property
    calendars = PropertyCalendar.query.filter_by(property_id=id).all()
    
    return render_template('property/calendars.html', property=property, calendars=calendars)

@bp.route('/<int:id>/calendar/add', methods=['GET', 'POST'])
@login_required
def add_calendar(id):
    property = Property.query.get_or_404(id)
    
    # Check if user is authorized to edit this property
    if property.owner_id != current_user.id:
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

@bp.route('/<int:property_id>/calendar/<int:calendar_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_calendar(property_id, calendar_id):
    property = Property.query.get_or_404(property_id)
    calendar = PropertyCalendar.query.get_or_404(calendar_id)
    
    # Check if user is authorized to edit this property
    if property.owner_id != current_user.id:
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

@bp.route('/<int:property_id>/calendar/<int:calendar_id>/delete', methods=['POST'])
@login_required
def delete_calendar(property_id, calendar_id):
    property = Property.query.get_or_404(property_id)
    calendar = PropertyCalendar.query.get_or_404(calendar_id)
    
    # Check if user is authorized to edit this property
    if property.owner_id != current_user.id:
        abort(403)
    
    # Check if calendar belongs to this property
    if calendar.property_id != property_id:
        abort(404)
    
    db.session.delete(calendar)
    db.session.commit()
    
    flash('Calendar deleted successfully!', 'success')
    return redirect(url_for('property.manage_calendars', id=property_id))

@bp.route('/<int:property_id>/calendar/<int:calendar_id>/sync', methods=['POST'])
@login_required
def sync_calendar(property_id, calendar_id):
    property = Property.query.get_or_404(property_id)
    calendar = PropertyCalendar.query.get_or_404(calendar_id)
    
    # Check if user is authorized to edit this property
    if property.owner_id != current_user.id:
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

@bp.route('/<int:id>/calendar')
@login_required
def view_calendar(id):
    property = Property.query.get_or_404(id)
    
    # Check if user has permission to view this property
    if not property.is_visible_to(current_user):
        abort(403)
    
    # Get all calendars for this property
    calendars = PropertyCalendar.query.filter_by(property_id=id).all()
    
    # If no calendars found, still show the page but with message
    if not calendars:
        flash('No calendars have been added to this property. Add a calendar to see bookings.', 'info')
        return render_template('property/calendar_view.html', property=property, calendars=[], events=[])
    
    # Prepare events data for the calendar
    events = []
    success = False
    
    for calendar in calendars:
        try:
            # Log the attempt to fetch
            current_app.logger.info(f"Attempting to fetch calendar {calendar.id}: {calendar.name} - URL: {calendar.ical_url}")
            
            # Fetch the iCal data with timeout to prevent hanging and custom headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                'Accept': 'text/calendar,application/ics,*/*'
            }
            
            # Add debug info 
            current_app.logger.info(f"Fetching calendar URL: {calendar.ical_url}")
            
            response = requests.get(calendar.ical_url, 
                                   headers=headers, 
                                   timeout=15,
                                   verify=True)  # Set to False if SSL issues
            
            current_app.logger.info(f"Calendar fetch response: {response.status_code}")
            
            if response.status_code == 200:
                # Log successful fetch
                current_app.logger.info(f"Successfully fetched calendar data. Content length: {len(response.text)} bytes")
                
                # Debug - log the first 100 chars of response
                content_preview = response.text[:100].replace('\n', '\\n')
                current_app.logger.info(f"Content preview: {content_preview}")
                
                # Parse the iCal data
                try:
                    cal = Calendar.from_ical(response.text)
                    
                    # Log successful parsing
                    current_app.logger.info(f"Successfully parsed iCal data for calendar {calendar.id}")
                    
                    # Count events for logging
                    event_count = 0
                    
                    # Extract events
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            try:
                                # Get event details with extensive error checking
                                summary = ''
                                start_date = None
                                end_date = None
                                
                                # Try to get summary safely
                                if hasattr(component, 'get') and callable(component.get):
                                    summary_value = component.get('summary')
                                    if summary_value:
                                        summary = str(summary_value)
                                    else:
                                        summary = 'Booking'
                                else:
                                    summary = 'Booking'
                                
                                # Try to get start date safely
                                dtstart = component.get('dtstart')
                                if dtstart and hasattr(dtstart, 'dt'):
                                    start_date = dtstart.dt
                                else:
                                    # Skip this event if no start date
                                    current_app.logger.warning(f"Event missing start date in calendar {calendar.id}")
                                    continue
                                
                                # Try to get end date safely
                                dtend = component.get('dtend')
                                if dtend and hasattr(dtend, 'dt'):
                                    end_date = dtend.dt
                                else:
                                    # If no end date, use start date + 1 day
                                    if isinstance(start_date, datetime):
                                        end_date = start_date + timedelta(days=1)
                                    else:
                                        end_date = start_date + timedelta(days=1)
                                
                                # Convert datetime objects to date if necessary
                                if isinstance(start_date, datetime):
                                    start_date = start_date.date()
                                if isinstance(end_date, datetime):
                                    end_date = end_date.date()
                                
                                # Make sure both dates are valid
                                if not (start_date and end_date):
                                    continue
                                
                                # Add event to the list
                                event = {
                                    'title': summary,
                                    'start': start_date.isoformat(),
                                    'end': end_date.isoformat(),
                                    'className': f"{calendar.service.lower()}-event",
                                    'extendedProps': {
                                        'service': calendar.get_service_display(),
                                        'room': None if calendar.is_entire_property else calendar.room_name
                                    }
                                }
                                events.append(event)
                                event_count += 1
                                success = True
                            except (KeyError, AttributeError, ValueError, TypeError) as e:
                                # Just skip this event if there's a problem with it
                                current_app.logger.error(f"Error parsing event in calendar {calendar.id}: {str(e)}")
                                continue
                    
                    # Log event count
                    current_app.logger.info(f"Successfully processed {event_count} events from calendar {calendar.id}")
                    
                    # Update last_synced and status
                    calendar.last_synced = datetime.utcnow()
                    calendar.sync_status = 'Success'
                    calendar.sync_error = None
                    db.session.commit()
                    
                except Exception as e:
                    # Problem parsing the iCal data
                    calendar.sync_status = 'Failed'
                    calendar.sync_error = f"Error parsing iCal data: {str(e)[:255]}"
                    db.session.commit()
                    current_app.logger.error(f"Error parsing iCal for calendar {calendar.id}: {str(e)}")
                    current_app.logger.error(f"iCal Content: {response.text[:500]}")
                    flash(f'Error parsing calendar {calendar.name}: {str(e)}', 'warning')
            else:
                # Update sync status
                calendar.sync_status = 'Error'
                calendar.sync_error = f"HTTP error: {response.status_code}"
                db.session.commit()
                current_app.logger.error(f"HTTP error {response.status_code} for calendar {calendar.id}")
                flash(f'Could not fetch calendar {calendar.name} (HTTP error {response.status_code})', 'warning')
        except requests.exceptions.RequestException as e:
            # Network error
            calendar.sync_status = 'Failed'
            calendar.sync_error = f"Request error: {str(e)[:255]}"
            db.session.commit()
            current_app.logger.error(f"Request error for calendar {calendar.id}: {str(e)}")
            flash(f'Network error fetching calendar {calendar.name}: {str(e)}', 'warning')
        except Exception as e:
            # Any other error
            calendar.sync_status = 'Failed'
            calendar.sync_error = str(e)[:255]
            db.session.commit()
            current_app.logger.error(f"Unexpected error for calendar {calendar.id}: {str(e)}")
            flash(f'Error syncing calendar {calendar.name}: {str(e)}', 'warning')
    
    # If we couldn't fetch any valid events, inform the user
    if not success and calendars:
        flash('Could not fetch calendar data from any of the configured sources. Please check your calendar URLs and try again.', 'warning')
    
    # Log events data size
    current_app.logger.info(f"Total events collected: {len(events)}")
    
    # Ensure events data is JSON serializable
    try:
        import json
        # Attempt to serialize to verify it's valid JSON
        events_json = json.dumps(events)
        current_app.logger.info(f"Events data successfully serialized to JSON. Size: {len(events_json)} bytes")
    except (TypeError, ValueError) as e:
        current_app.logger.error(f"Error serializing events data: {str(e)}")
        flash('Error preparing calendar data for display. Some events may not be shown.', 'warning')
        events = []  # Reset to empty list as fallback
    
    return render_template('property/calendar_view.html', property=property, calendars=calendars, events=events)

# AJAX endpoint to add a new room form
@bp.route('/room-form-template')
@login_required
def room_form_template():
    # Get index from query parameters (default to 0)
    index = request.args.get('index', 0, type=int)
    room_id = None  # New room doesn't have an ID yet
    room_form = RoomForm()
    
    try:
        # Render the room form template
        html = render_template('property/_room_form.html', 
                              room_form=room_form, 
                              room_id=room_id, 
                              index=index,
                              is_new=True)
        
        # Return the rendered HTML as JSON
        return jsonify({'html': html, 'success': True})
    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error rendering room form template: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

# Fix for the duplicated property in URL
@bp.route('/property/<int:id>/calendar')
@login_required
def redirect_to_calendar(id):
    # Redirect to the correct calendar URL
    return redirect(url_for('property.view_calendar', id=id))

@bp.route('/property/<int:id>/calendars')
@login_required
def redirect_to_calendars(id):
    # Redirect to the correct calendars URL
    return redirect(url_for('property.manage_calendars', id=id))


# Guest Guidebook Routes
@bp.route('/guest/<int:property_id>/guidebook')
def guest_guidebook(property_id):
    """Public guest access to property guidebook"""
    property = Property.query.get_or_404(property_id)
    
    # Check for guest access token
    token = request.args.get('token')
    if not token or token != property.guest_access_token:
        if not property.guest_access_enabled:
            abort(404)  # Hide existence of private properties
        abort(403)
    
    # Get guidebook entries
    from app.models import GuidebookEntry
    entries = GuidebookEntry.get_by_property_and_category(property_id)
    featured_entries = GuidebookEntry.get_featured_by_property(property_id)
    
    # Group entries by category
    entries_by_category = {}
    for entry in entries:
        category_name = entry.get_category_display()
        if category_name not in entries_by_category:
            entries_by_category[category_name] = []
        entries_by_category[category_name].append(entry)
    
    # Get map data for entries with coordinates
    map_entries = GuidebookEntry.get_map_data_for_property(property_id)
    
    return render_template('property/guest_guidebook.html',
                          property=property,
                          entries_by_category=entries_by_category,
                          featured_entries=featured_entries,
                          map_entries=map_entries,
                          token=token)


@bp.route('/guest/<int:property_id>/guidebook/map')
def guest_guidebook_map(property_id):
    """Dedicated map view for guest guidebook"""
    property = Property.query.get_or_404(property_id)
    
    # Check for guest access token
    token = request.args.get('token')
    if not token or token != property.guest_access_token:
        if not property.guest_access_enabled:
            abort(404)
        abort(403)
    
    # Get map data
    from app.models import GuidebookEntry
    map_entries = GuidebookEntry.get_map_data_for_property(property_id)
    
    return render_template('property/guest_guidebook_map.html',
                          property=property,
                          map_entries=map_entries,
                          token=token)