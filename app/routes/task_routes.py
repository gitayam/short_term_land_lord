from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from app.forms.task_forms import RepairRequestForm
from app.models import Task, Property, TaskStatus, TaskPriority, RepairRequestSeverity, TaskProperty, TaskMedia, MediaType
from app.extensions import db
import uuid
from app.utils.storage import allowed_file, save_file_to_storage
from app.utils.notifications import send_task_assignment_notification
from app.decorators import property_access_required
from sqlalchemy import desc
import logging

tasks = Blueprint('tasks', __name__)

@tasks.route('/repair_requests')
@login_required
def repair_requests():
    """Show repair request tasks"""
    try:
        # Get query parameters for sorting and filtering
        sort_by = request.args.get('sort_by', 'priority')
        property_id = request.args.get('property_id', type=int)
        
        # Base query - get tasks tagged as repair requests
        query = Task.query.filter(Task.tags.like('%repair_request%'))
        
        # Apply property filter if specified
        if property_id:
            query = query.join(
                TaskProperty, TaskProperty.task_id == Task.id
            ).filter(
                TaskProperty.property_id == property_id
            )
        
        # Apply sorting
        if sort_by == 'date':
            query = query.order_by(Task.created_at.desc())
        elif sort_by == 'due_date':
            query = query.order_by(Task.due_date)
        elif sort_by == 'property':
            query = query.join(
                TaskProperty, TaskProperty.task_id == Task.id
            ).join(
                Property, Property.id == TaskProperty.property_id
            ).order_by(Property.name)
        else:  # Default to priority
            query = query.order_by(Task.priority.desc())
        
        # Get properties for filter based on user role
        if current_user.has_admin_role:
            properties = Property.query.all()
        else:
            properties = Property.query.filter(Property.is_visible_to(current_user)).all()
        
        repair_requests = query.all()
        
        return render_template('tasks/repair_requests.html',
                             title='Repair Requests',
                             repair_requests=repair_requests,
                             properties=properties,
                             current_property_id=property_id,
                             sort_by=sort_by)
    except Exception as e:
        current_app.logger.error(f"Error in repair_requests view: {str(e)}", exc_info=True)
        flash('An error occurred while loading repair requests. Please try again.', 'error')
        return redirect(url_for('main.index'))

@tasks.route('/repair_requests/create', methods=['GET', 'POST'])
@login_required
def create_repair_request():
    """Create a new repair request"""
    try:
        property_id = request.args.get('property_id', type=int)
        
        # Validate property exists and access
        if not property_id:
            flash('Property ID is required to create a repair request.', 'warning')
            return redirect(url_for('tasks.repair_requests'))
            
        property = Property.query.get(property_id)
        if not property:
            flash('Property not found.', 'error')
            return redirect(url_for('tasks.repair_requests'))
            
        if not property.is_visible_to(current_user):
            flash('You do not have permission to create repair requests for this property.', 'warning')
            return redirect(url_for('tasks.repair_requests'))
        
        form = RepairRequestForm()
        
        # Set up the property query for the form
        if current_user.has_admin_role:
            properties = Property.query.all()
        else:
            properties = Property.query.filter(Property.is_visible_to(current_user)).all()
        
        if not properties:
            flash('No properties available for repair requests.', 'warning')
            return redirect(url_for('tasks.repair_requests'))
        
        form.property.query = Property.query.filter(Property.id.in_([p.id for p in properties]))
        form.property.data = property
        
        if form.validate_on_submit():
            try:
                # Create the task
                task = Task(
                    title=form.title.data,
                    description=form.description.data,
                    status=TaskStatus.PENDING,
                    priority=TaskPriority[form.priority.data],  # Convert string to enum
                    location=form.location.data,
                    due_date=form.due_date.data,
                    tags='repair_request',
                    creator_id=current_user.id,
                    notes=form.additional_notes.data
                )
                
                # Add property to task
                task_property = TaskProperty(property_id=property_id)
                task.task_properties.append(task_property)
                
                db.session.add(task)
                db.session.commit()
                
                # Handle photo uploads
                photos = request.files.getlist('photos')
                photo_error = False
                
                if photos and photos[0].filename:
                    upload_dir = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], 'repair_requests')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    for photo in photos:
                        if allowed_file(photo.filename, current_app.config['ALLOWED_PHOTO_EXTENSIONS']):
                            try:
                                file_path, storage_backend, file_size, mime_type = save_file_to_storage(
                                    photo, task.id, MediaType.PHOTO
                                )
                                
                                media = TaskMedia(
                                    task_id=task.id,
                                    file_path=file_path,
                                    storage_backend=storage_backend,
                                    file_size=file_size,
                                    mime_type=mime_type,
                                    original_filename=photo.filename
                                )
                                db.session.add(media)
                            except Exception as e:
                                current_app.logger.error(f"Error saving photo: {str(e)}", exc_info=True)
                                photo_error = True
                                continue
                    
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(f"Error committing media files: {str(e)}", exc_info=True)
                        photo_error = True
                
                if photo_error:
                    flash('Some photos could not be saved, but your repair request was created successfully.', 'warning')
                
                # Send notification to property owner
                try:
                    if property.owner:
                        send_task_assignment_notification(task, property.owner)
                    else:
                        current_app.logger.warning(f"No property owner found for property {property_id}")
                except Exception as e:
                    current_app.logger.error(f"Error sending notification: {str(e)}", exc_info=True)
                    flash('Repair request created, but notification could not be sent.', 'warning')
                
                flash('Repair request created successfully!', 'success')
                return redirect(url_for('tasks.repair_requests'))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database error creating repair request: {str(e)}", exc_info=True)
                flash('An error occurred while saving the repair request. Please try again.', 'error')
                return render_template('tasks/create_repair_request.html',
                                    title='Create Repair Request',
                                    form=form,
                                    property=property)
        
        # If form validation failed, check for specific errors
        if form.errors:
            current_app.logger.warning(f"Form validation errors: {form.errors}")
            
        return render_template('tasks/create_repair_request.html',
                             title='Create Repair Request',
                             form=form,
                             property=property)
                             
    except Exception as e:
        current_app.logger.error(f"Unexpected error in create_repair_request: {str(e)}", exc_info=True)
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('tasks.repair_requests'))

# ... existing code ... 