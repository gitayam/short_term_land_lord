from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
import os
from app import db
from app.models import RecommendationBlock, Property, MediaType
from app.forms.recommendation_forms import RecommendationBlockForm
from app.utils.storage import allowed_file, save_file_to_storage

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
                         search_query=search)

@bp.route('/property/<int:property_id>/new', methods=['GET', 'POST'])
@login_required
def create_recommendation(property_id):
    property = Property.query.get_or_404(property_id)
    if not can_manage_recommendations(property):
        flash('You do not have permission to add recommendations to this property.', 'error')
        return redirect(url_for('main.index'))
    
    form = RecommendationBlockForm()
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
            in_guide_book=form.add_to_guide.data
        )
        
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
    if not can_manage_recommendations(recommendation.property):
        flash('You do not have permission to edit this recommendation.', 'error')
        return redirect(url_for('main.index'))
    
    form = RecommendationBlockForm(obj=recommendation)
    form.add_to_guide.data = recommendation.in_guide_book
    
    if form.validate_on_submit():
        recommendation.title = form.title.data
        recommendation.description = form.description.data
        recommendation.category = form.category.data
        recommendation.map_link = form.map_link.data
        recommendation.best_time_to_go = form.best_time_to_go.data
        recommendation.recommended_meal = form.recommended_meal.data
        recommendation.wifi_name = form.wifi_name.data
        recommendation.wifi_password = form.wifi_password.data
        recommendation.parking_details = form.parking_details.data
        recommendation.in_guide_book = form.add_to_guide.data
        
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
    
    return render_template('recommendations/edit.html', form=form, recommendation=recommendation)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_recommendation(id):
    recommendation = RecommendationBlock.query.get_or_404(id)
    if not can_manage_recommendations(recommendation.property):
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

@bp.route('/property/<int:property_id>/guide-book')
def view_guide_book(property_id):
    property = Property.query.get_or_404(property_id)
    
    # Get all guide book recommendations
    recommendations = RecommendationBlock.query.filter_by(
        property_id=property_id,
        in_guide_book=True
    ).order_by(RecommendationBlock.category, RecommendationBlock.title).all()
    
    # Group recommendations by category
    categorized_recommendations = {}
    for rec in recommendations:
        category = rec.get_category_display()
        if category not in categorized_recommendations:
            categorized_recommendations[category] = []
        categorized_recommendations[category].append(rec)
    
    return render_template('recommendations/guide_book.html',
                         property=property,
                         categorized_recommendations=categorized_recommendations) 