from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
import os
from app import db
from app.models import RecommendationBlock, Property, MediaType, RecommendationVote, GuideBook, GuideBookSection, GuideBookEntry
from app.forms.recommendation_forms import RecommendationBlockForm
from app.forms.guide_book_forms import GuideBookForm
from app.forms.guide_book_section_forms import GuideBookSectionForm, GuideBookEntryForm, BulkGuideBookEntryForm
from app.utils.storage import allowed_file, save_file_to_storage
from sqlalchemy import func

bp = Blueprint('recommendations', __name__)

def can_manage_recommendations(property):
    return (current_user.has_admin_role or 
            current_user.id == property.owner_id or 
            current_user.is_property_manager)

@bp.route('/property/<int:property_id>/list')
@login_required
def list_recommendations(property_id):
    property = Property.query.get_or_404(property_id)
    if not property.is_visible_to(current_user):
        flash('You do not have permission to view this property.', 'error')
        return redirect(url_for('main.index'))
    
    category = request.args.get('category')
    search = request.args.get('search')
    in_guide_book = request.args.get('in_guide_book') == 'true'
    guest_token = request.headers.get('X-Guest-Token') or request.cookies.get('guest_token')
    
    query = RecommendationBlock.query.filter_by(property_id=property_id)
    
    # Apply filters
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(RecommendationBlock.title.ilike(f'%{search}%') | 
                           RecommendationBlock.description.ilike(f'%{search}%'))
    if in_guide_book:
        query = query.filter_by(in_guide_book=True)
    
    # Order by guide book status (guide book entries first) then by title
    query = query.order_by(RecommendationBlock.in_guide_book.desc(), RecommendationBlock.title)
    
    recommendations = query.all()
    return render_template('recommendations/list.html', 
                         property=property,
                         recommendations=recommendations,
                         current_category=category,
                         search_query=search,
                         guest_token=guest_token)

@bp.route('/property/<int:property_id>/guide-books')
@login_required
def list_guide_books(property_id):
    """List all guide books for a property."""
    property = Property.query.get_or_404(property_id)
    if not property.is_visible_to(current_user):
        flash('You do not have permission to view this property.', 'error')
        return redirect(url_for('main.index'))
    
    guide_books = GuideBook.query.filter_by(property_id=property_id).order_by(GuideBook.name).all()
    return render_template('recommendations/guide_books.html',
                         property=property,
                         guide_books=guide_books)

@bp.route('/property/<int:property_id>/guide-books/new', methods=['GET', 'POST'])
@login_required
def create_guide_book(property_id):
    """Create a new guide book."""
    property = Property.query.get_or_404(property_id)
    
    # Check if user has permission to create guide books
    if not current_user.is_admin and not current_user.is_property_owner and not current_user.is_property_manager:
        flash('You do not have permission to create guide books.', 'error')
        return redirect(url_for('main.index'))
    
    # For property managers, check if they manage this specific property
    if current_user.is_property_manager and not property.is_managed_by(current_user):
        flash('You do not have permission to create guide books for this property.', 'error')
        return redirect(url_for('main.index'))
    
    form = GuideBookForm()
    
    if request.method == 'GET':
        form.property_id.data = property_id
    
    if form.validate_on_submit():
        try:
            guide_book = GuideBook(
                property_id=property_id,
                name=form.name.data,
                description=form.description.data,
                is_public=form.is_public.data
            )
            
            db.session.add(guide_book)
            db.session.commit()
            
            flash('Guide book created successfully!', 'success')
            return redirect(url_for('recommendations.list_guide_books', property_id=property_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the guide book. Please try again.', 'error')
            current_app.logger.error(f'Error creating guide book: {str(e)}')
    
    return render_template('recommendations/guide_book_form.html',
                         form=form,
                         property=property,
                         title='Create New Guide Book')

@bp.route('/guide-books/<int:id>')
def view_guide_book(id):
    """View a specific guide book."""
    guide_book = GuideBook.query.get_or_404(id)
    property = guide_book.associated_property
    
    if not guide_book.is_public and not property.is_visible_to(current_user):
        flash('You do not have permission to view this guide book.', 'error')
        return redirect(url_for('main.index'))
    
    # Group recommendations by category
    categorized_recommendations = {}
    for rec in guide_book.recommendations:
        category = rec.get_category_display()
        if category not in categorized_recommendations:
            categorized_recommendations[category] = []
        categorized_recommendations[category].append(rec)
    
    return render_template('recommendations/guide_book.html',
                         guide_book=guide_book,
                         property=property,
                         categorized_recommendations=categorized_recommendations,
                         guest_token=request.headers.get('X-Guest-Token') or request.cookies.get('guest_token'))

@bp.route('/guide-books/<token>/public')
def public_guide_book(token):
    """Public access to a guide book via token."""
    guide_book = GuideBook.query.filter_by(access_token=token, is_public=True).first_or_404()
    property = guide_book.associated_property
    
    # Group recommendations by category
    categorized_recommendations = {}
    for rec in guide_book.recommendations:
        category = rec.get_category_display()
        if category not in categorized_recommendations:
            categorized_recommendations[category] = []
        categorized_recommendations[category].append(rec)
    
    return render_template('recommendations/guide_book.html',
                         guide_book=guide_book,
                         property=property,
                         categorized_recommendations=categorized_recommendations,
                         is_public_view=True)

@bp.route('/guide-books/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_guide_book(id):
    """Edit a guide book."""
    guide_book = GuideBook.query.get_or_404(id)
    property = guide_book.associated_property
    
    # Check if user has permission to edit guide books
    if not current_user.is_admin and not current_user.is_property_owner and not current_user.is_property_manager:
        flash('You do not have permission to edit guide books.', 'error')
        return redirect(url_for('main.index'))
    
    # For property managers, check if they manage this specific property
    if current_user.is_property_manager and not property.is_managed_by(current_user):
        flash('You do not have permission to edit guide books for this property.', 'error')
        return redirect(url_for('main.index'))
    
    form = GuideBookForm(obj=guide_book)
    form.property_id.data = property.id
    # Store guide_book_id for validation
    form.guide_book_id = guide_book.id
    
    if form.validate_on_submit():
        try:
            guide_book.name = form.name.data
            guide_book.description = form.description.data
            guide_book.is_public = form.is_public.data
            
            # Generate or clear access token based on public status
            if guide_book.is_public:
                guide_book.ensure_access_token()
            elif not guide_book.is_public and guide_book.access_token:
                guide_book.access_token = None
            
            db.session.commit()
            flash('Guide book updated successfully!', 'success')
            return redirect(url_for('recommendations.view_guide_book', id=id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the guide book. Please try again.', 'error')
            current_app.logger.error(f'Error updating guide book: {str(e)}')
    
    return render_template('recommendations/guide_book_form.html',
                         form=form,
                         guide_book=guide_book,
                         property=property,
                         title='Edit Guide Book')

def _get_guide_book_choices(property_id):
    """Get guide book choices for the form select field."""
    guide_books = GuideBook.query.filter_by(property_id=property_id).order_by(GuideBook.name).all()
    return [(gb.id, gb.name) for gb in guide_books]

@bp.route('/property/<int:property_id>/new', methods=['GET', 'POST'])
@login_required
def create_recommendation(property_id):
    property = Property.query.get_or_404(property_id)
    if not can_manage_recommendations(property):
        flash('You do not have permission to add recommendations to this property.', 'error')
        return redirect(url_for('main.index'))
    
    form = RecommendationBlockForm()
    form.guide_books.choices = _get_guide_book_choices(property_id)
    
    if form.validate_on_submit():
        recommendation = RecommendationBlock(
            property_id=property_id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            map_link=form.map_link.data,
            best_time_to_go=form.best_time_to_go.data,
            recommended_meal=form.recommended_meal.data,
            wifi_name=form.wifi_name.data,
            wifi_password=form.wifi_password.data,
            parking_details=form.parking_details.data,
            hours=form.hours.data
        )
        
        # Add to selected guide books
        if form.guide_books.data:
            guide_books = GuideBook.query.filter(GuideBook.id.in_(form.guide_books.data)).all()
            recommendation.guide_books.extend(guide_books)
        
        if form.photo.data:
            file = form.photo.data
            if file and allowed_file(file.filename):
                try:
                    file_path, storage_backend, file_size, mime_type = save_file_to_storage(
                        file, property_id, MediaType.PHOTO
                    )
                    recommendation.photo_path = file_path
                except Exception as e:
                    current_app.logger.error(f"Error saving photo: {str(e)}", exc_info=True)
                    flash('Error saving photo, but recommendation was created successfully.', 'warning')
        
        db.session.add(recommendation)
        db.session.commit()
        flash('Recommendation added successfully!', 'success')
        return redirect(url_for('recommendations.list_recommendations', property_id=property_id))
    
    return render_template('recommendations/create.html', form=form, property=property)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recommendation(id):
    recommendation = RecommendationBlock.query.get_or_404(id)
    property = Property.query.get_or_404(recommendation.property_id)
    if not can_manage_recommendations(property):
        flash('You do not have permission to edit this recommendation.', 'error')
        return redirect(url_for('main.index'))
    
    form = RecommendationBlockForm(obj=recommendation)
    form.guide_books.choices = _get_guide_book_choices(recommendation.property_id)
    
    if request.method == 'GET':
        form.guide_books.data = [gb.id for gb in recommendation.guide_books]
    
    if form.validate_on_submit():
        try:
            recommendation.title = form.title.data
            recommendation.description = form.description.data
            recommendation.category = form.category.data
            recommendation.map_link = form.map_link.data
            recommendation.best_time_to_go = form.best_time_to_go.data
            recommendation.recommended_meal = form.recommended_meal.data
            recommendation.wifi_name = form.wifi_name.data
            recommendation.wifi_password = form.wifi_password.data
            recommendation.parking_details = form.parking_details.data
            recommendation.hours = form.hours.data
            
            # Update guide books
            recommendation.guide_books = []
            if form.guide_books.data:
                guide_books = GuideBook.query.filter(GuideBook.id.in_(form.guide_books.data)).all()
                recommendation.guide_books.extend(guide_books)
            
            if form.photo.data:
                file = form.photo.data
                if file and allowed_file(file.filename):
                    try:
                        file_path, storage_backend, file_size, mime_type = save_file_to_storage(
                            file, recommendation.property_id, MediaType.PHOTO
                        )
                        recommendation.photo_path = file_path
                    except Exception as e:
                        current_app.logger.error(f"Error saving photo: {str(e)}", exc_info=True)
                        flash('Error saving photo, but recommendation was updated successfully.', 'warning')
            
            db.session.commit()
            flash('Recommendation updated successfully!', 'success')
            return redirect(url_for('recommendations.list_recommendations', property_id=recommendation.property_id))
        except Exception as e:
            current_app.logger.error(f"Error updating recommendation: {str(e)}", exc_info=True)
            db.session.rollback()
            flash('Error updating recommendation. Please try again.', 'error')
    
    return render_template('recommendations/edit.html', form=form, recommendation=recommendation)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_recommendation(id):
    recommendation = RecommendationBlock.query.get_or_404(id)
    property = Property.query.get_or_404(recommendation.property_id)
    if not can_manage_recommendations(property):
        flash('You do not have permission to delete this recommendation.', 'error')
        return redirect(url_for('main.index'))
    
    # Delete photo if exists
    if recommendation.photo_path:
        photo_path = os.path.join(current_app.config['LOCAL_STORAGE_PATH'], 
                                'recommendations', 
                                recommendation.photo_path)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    property_id = recommendation.property_id
    db.session.delete(recommendation)
    db.session.commit()
    flash('Recommendation deleted successfully!', 'success')
    return redirect(url_for('recommendations.list_recommendations', property_id=property_id))

@bp.route('/recommendations/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Dashboard for managing recommendations and viewing votes."""
    if not current_user.is_property_owner and not current_user.has_admin_role:
        flash('Access denied. You must be a property owner or admin to view this page.', 'error')
        return redirect(url_for('main.index'))
    
    # Get recommendations for the user's properties, ordered by vote count
    query = RecommendationBlock.query
    
    if not current_user.has_admin_role:
        # Filter by user's properties if not admin
        query = query.join(Property).filter(Property.owner_id == current_user.id)
    
    # Use a subquery to count votes
    vote_count = db.session.query(
        RecommendationVote.recommendation_id,
        func.count(RecommendationVote.id).label('vote_count')
    ).group_by(RecommendationVote.recommendation_id).subquery()
    
    # Join with vote counts and order by votes
    recommendations = query.outerjoin(
        vote_count,
        RecommendationBlock.id == vote_count.c.recommendation_id
    ).order_by(
        vote_count.c.vote_count.desc().nullslast(),
        RecommendationBlock.created_at.desc()
    ).all()
    
    return render_template(
        'recommendations/dashboard.html',
        recommendations=recommendations
    )

@bp.route('/property/api/recommendations/<int:id>/vote', methods=['POST'])
def toggle_recommendation_vote(id):
    """Toggle a vote for a recommendation."""
    guest_token = request.headers.get('X-Guest-Token')
    if not guest_token:
        return jsonify({'error': 'Guest token required'}), 400
    
    recommendation = RecommendationBlock.query.get_or_404(id)
    voted = recommendation.toggle_vote(guest_token)
    
    return jsonify({
        'voted': voted,
        'vote_count': recommendation.vote_count
    })

@bp.route('/property/<int:property_id>/guide')
def view_property_guide_book(property_id):
    """View the guide book for a property."""
    property = Property.query.get_or_404(property_id)
    
    # Get the first guide book for the property
    guide_book = GuideBook.query.filter_by(property_id=property_id).first()
    
    if not guide_book:
        flash('No guide book found for this property.', 'warning')
        return redirect(url_for('recommendations.list_guide_books', property_id=property_id))
    
    return redirect(url_for('recommendations.view_guide_book', id=guide_book.id))

# Guide Book Section Management Routes
@bp.route('/guide-book/<int:guide_book_id>/sections')
@login_required
def manage_sections(guide_book_id):
    """Manage sections for a guide book."""
    guide_book = GuideBook.query.get_or_404(guide_book_id)
    property = guide_book.property
    
    # Check permissions
    if not (current_user.is_admin or current_user.is_property_owner or 
            (current_user.is_property_manager and property.is_managed_by(current_user))):
        flash('You do not have permission to manage this guide book.', 'error')
        return redirect(url_for('main.index'))
    
    sections = GuideBookSection.query.filter_by(
        guide_book_id=guide_book_id,
        is_active=True
    ).order_by(GuideBookSection.order_index).all()
    
    return render_template('recommendations/guide_book_sections.html',
                         guide_book=guide_book,
                         property=property,
                         sections=sections)

@bp.route('/guide-book/<int:guide_book_id>/section/create', methods=['GET', 'POST'])
@login_required
def create_section(guide_book_id):
    """Create a new section for a guide book."""
    guide_book = GuideBook.query.get_or_404(guide_book_id)
    property = guide_book.property
    
    # Check permissions
    if not (current_user.is_admin or current_user.is_property_owner or 
            (current_user.is_property_manager and property.is_managed_by(current_user))):
        flash('You do not have permission to add sections to this guide book.', 'error')
        return redirect(url_for('main.index'))
    
    form = GuideBookSectionForm()
    
    if form.validate_on_submit():
        section = GuideBookSection(
            guide_book_id=guide_book_id,
            section_type=form.section_type.data,
            title=form.title.data,
            content=form.content.data,
            icon=form.icon.data,
            order_index=form.order_index.data,
            is_active=form.is_active.data
        )
        
        # Auto-create common entries based on section type
        if form.section_type.data == 'check_in':
            # Add default check-in entries
            default_entries = [
                ('instruction', 'Check-in Time', '3:00 PM - 10:00 PM'),
                ('instruction', 'Check-out Time', 'Before 11:00 AM'),
                ('instruction', 'Key Location', 'Lockbox on the front door'),
                ('text', 'Late Check-in', 'Please contact us if arriving after 10 PM')
            ]
            for entry_type, title, content in default_entries:
                entry = GuideBookEntry(
                    entry_type=entry_type,
                    title=title,
                    content=content,
                    is_active=True
                )
                section.entries.append(entry)
        
        elif form.section_type.data == 'wifi':
            default_entries = [
                ('text', 'Network Name', 'PropertyWiFi'),
                ('text', 'Password', 'YourPassword123'),
                ('instruction', 'Smart TV', 'Netflix and YouTube are pre-installed')
            ]
            for entry_type, title, content in default_entries:
                entry = GuideBookEntry(
                    entry_type=entry_type,
                    title=title,
                    content=content,
                    is_active=True
                )
                section.entries.append(entry)
        
        elif form.section_type.data == 'emergency':
            default_entries = [
                ('contact', 'Emergency Services', None),
                ('contact', 'Property Manager', None),
                ('contact', 'Nearest Hospital', None)
            ]
            for i, (entry_type, title, content) in enumerate(default_entries):
                entry = GuideBookEntry(
                    entry_type=entry_type,
                    title=title,
                    content=content,
                    is_important=True if i == 0 else False,
                    is_active=True
                )
                if title == 'Emergency Services':
                    entry.phone = '911'
                section.entries.append(entry)
        
        db.session.add(section)
        db.session.commit()
        
        flash('Section created successfully!', 'success')
        return redirect(url_for('recommendations.edit_section', section_id=section.id))
    
    return render_template('recommendations/guide_book_section_form.html',
                         form=form,
                         guide_book=guide_book,
                         property=property,
                         title='Create Section')

@bp.route('/section/<int:section_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_section(section_id):
    """Edit a guide book section and manage its entries."""
    section = GuideBookSection.query.get_or_404(section_id)
    guide_book = section.guide_book
    property = guide_book.property
    
    # Check permissions
    if not (current_user.is_admin or current_user.is_property_owner or 
            (current_user.is_property_manager and property.is_managed_by(current_user))):
        flash('You do not have permission to edit this section.', 'error')
        return redirect(url_for('main.index'))
    
    form = GuideBookSectionForm(obj=section)
    entry_form = GuideBookEntryForm()
    bulk_form = BulkGuideBookEntryForm()
    
    if form.validate_on_submit() and 'update_section' in request.form:
        section.section_type = form.section_type.data
        section.title = form.title.data
        section.content = form.content.data
        section.icon = form.icon.data
        section.order_index = form.order_index.data
        section.is_active = form.is_active.data
        
        db.session.commit()
        flash('Section updated successfully!', 'success')
        return redirect(url_for('recommendations.edit_section', section_id=section_id))
    
    entries = GuideBookEntry.query.filter_by(
        section_id=section_id,
        is_active=True
    ).order_by(GuideBookEntry.order_index).all()
    
    return render_template('recommendations/guide_book_section_edit.html',
                         form=form,
                         entry_form=entry_form,
                         bulk_form=bulk_form,
                         section=section,
                         entries=entries,
                         guide_book=guide_book,
                         property=property)

@bp.route('/section/<int:section_id>/entry/create', methods=['POST'])
@login_required
def create_entry(section_id):
    """Create a new entry in a section."""
    section = GuideBookSection.query.get_or_404(section_id)
    guide_book = section.guide_book
    property = guide_book.property
    
    # Check permissions
    if not (current_user.is_admin or current_user.is_property_owner or 
            (current_user.is_property_manager and property.is_managed_by(current_user))):
        flash('You do not have permission to add entries to this section.', 'error')
        return redirect(url_for('main.index'))
    
    form = GuideBookEntryForm()
    
    if form.validate_on_submit():
        entry = GuideBookEntry(
            section_id=section_id,
            entry_type=form.entry_type.data,
            title=form.title.data,
            subtitle=form.subtitle.data,
            content=form.content.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            url=form.url.data,
            icon=form.icon.data,
            order_index=form.order_index.data,
            is_important=form.is_important.data,
            is_active=form.is_active.data
        )
        
        # Handle image upload
        if form.image.data:
            filename = save_file_to_storage(form.image.data, 'guide_book_entries')
            if filename:
                entry.image_path = filename
        
        db.session.add(entry)
        db.session.commit()
        
        flash('Entry added successfully!', 'success')
    else:
        flash('Error adding entry. Please check the form.', 'error')
    
    return redirect(url_for('recommendations.edit_section', section_id=section_id))

@bp.route('/section/<int:section_id>/entries/bulk', methods=['POST'])
@login_required
def create_bulk_entries(section_id):
    """Create multiple entries at once."""
    section = GuideBookSection.query.get_or_404(section_id)
    guide_book = section.guide_book
    property = guide_book.property
    
    # Check permissions
    if not (current_user.is_admin or current_user.is_property_owner or 
            (current_user.is_property_manager and property.is_managed_by(current_user))):
        flash('You do not have permission to add entries to this section.', 'error')
        return redirect(url_for('main.index'))
    
    form = BulkGuideBookEntryForm()
    
    if form.validate_on_submit():
        entries_text = form.entries.data
        entry_type = form.entry_type.data
        
        # Split by newlines and create entries
        lines = [line.strip() for line in entries_text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            entry = GuideBookEntry(
                section_id=section_id,
                entry_type=entry_type,
                content=line,
                order_index=i * 10,  # Space them out for easy reordering
                is_active=True
            )
            db.session.add(entry)
        
        db.session.commit()
        flash(f'{len(lines)} entries added successfully!', 'success')
    else:
        flash('Error adding entries. Please check the form.', 'error')
    
    return redirect(url_for('recommendations.edit_section', section_id=section_id))

@bp.route('/entry/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """Delete an entry from a section."""
    entry = GuideBookEntry.query.get_or_404(entry_id)
    section = entry.section
    guide_book = section.guide_book
    property = guide_book.property
    
    # Check permissions
    if not (current_user.is_admin or current_user.is_property_owner or 
            (current_user.is_property_manager and property.is_managed_by(current_user))):
        flash('You do not have permission to delete this entry.', 'error')
        return redirect(url_for('main.index'))
    
    entry.is_active = False
    db.session.commit()
    
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('recommendations.edit_section', section_id=section.id)) 