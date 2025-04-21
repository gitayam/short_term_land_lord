from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models import Property, GuestReview, GuestReviewRating, User, UserRoles, SiteSettings
from app.auth.decorators import property_owner_required
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

# Form for creating and editing guest reviews
class GuestReviewForm(FlaskForm):
    guest_name = StringField('Guest Name', validators=[DataRequired(), Length(max=100)])
    check_in_date = DateField('Check-in Date', validators=[DataRequired()], format='%Y-%m-%d')
    check_out_date = DateField('Check-out Date', validators=[DataRequired()], format='%Y-%m-%d')
    rating = SelectField('Rating', choices=[
        ('good', '👍 Good - Excellent guest'),
        ('ok', '👌 OK - Average guest'),
        ('bad', '👎 Bad - Problematic guest')
    ], validators=[DataRequired()])
    comment = TextAreaField('Comments/Notes', validators=[Optional()])
    submit = SubmitField('Save Review')

# Routes for guest reviews
def register_guest_review_routes(bp):
    
    @bp.route('/<int:id>/guest-reviews')
    @login_required
    def guest_reviews(id):
        """View all guest reviews for a property"""
        # Check if guest reviews are enabled
        if not SiteSettings.is_guest_reviews_enabled():
            flash('Guest reviews feature is currently disabled.', 'warning')
            return redirect(url_for('property.view', id=id))
            
        property = Property.query.get_or_404(id)
        
        # Check if user has permission to view this property's reviews
        if not can_view_guest_reviews(property):
            flash('Access denied. You do not have permission to view guest reviews for this property.', 'danger')
            return redirect(url_for('main.index'))
        
        # Get all reviews for this property
        reviews = GuestReview.query.filter_by(property_id=id).order_by(GuestReview.created_at.desc()).all()
        
        return render_template('property/guest_reviews.html', 
                              property=property, 
                              reviews=reviews,
                              title=f'Guest Reviews - {property.name}')
    
    @bp.route('/<int:id>/guest-reviews/add', methods=['GET', 'POST'])
    @login_required
    def add_guest_review(id):
        """Add a new guest review for a property"""
        # Check if guest reviews are enabled
        if not SiteSettings.is_guest_reviews_enabled():
            flash('Guest reviews feature is currently disabled.', 'warning')
            return redirect(url_for('property.view', id=id))
            
        property = Property.query.get_or_404(id)
        
        # Check if user has permission to add reviews for this property
        if not can_manage_guest_reviews(property):
            flash('Access denied. You do not have permission to add guest reviews for this property.', 'danger')
            return redirect(url_for('property.guest_reviews', id=id))
        
        form = GuestReviewForm()
        
        if form.validate_on_submit():
            review = GuestReview(
                property_id=property.id,
                guest_name=form.guest_name.data,
                check_in_date=form.check_in_date.data,
                check_out_date=form.check_out_date.data,
                rating=form.rating.data,
                comment=form.comment.data,
                creator_id=current_user.id
            )
            
            db.session.add(review)
            db.session.commit()
            
            flash('Guest review added successfully!', 'success')
            return redirect(url_for('property.guest_reviews', id=id))
        
        return render_template('property/guest_review_form.html',
                              form=form,
                              property=property,
                              title=f'Add Guest Review - {property.name}')
    
    @bp.route('/guest-reviews/<int:review_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_guest_review(review_id):
        """Edit an existing guest review"""
        # Check if guest reviews are enabled
        if not SiteSettings.is_guest_reviews_enabled():
            flash('Guest reviews feature is currently disabled.', 'warning')
            return redirect(url_for('main.index'))
            
        review = GuestReview.query.get_or_404(review_id)
        property = Property.query.get_or_404(review.property_id)
        
        # Check if user has permission to edit this review
        if not can_edit_guest_review(review):
            flash('Access denied. You do not have permission to edit this guest review.', 'danger')
            return redirect(url_for('property.guest_reviews', id=property.id))
        
        form = GuestReviewForm()
        
        if form.validate_on_submit():
            review.guest_name = form.guest_name.data
            review.check_in_date = form.check_in_date.data
            review.check_out_date = form.check_out_date.data
            review.rating = form.rating.data
            review.comment = form.comment.data
            review.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Guest review updated successfully!', 'success')
            return redirect(url_for('property.guest_reviews', id=property.id))
        elif request.method == 'GET':
            # Populate form with existing data
            form.guest_name.data = review.guest_name
            form.check_in_date.data = review.check_in_date
            form.check_out_date.data = review.check_out_date
            form.rating.data = review.rating
            form.comment.data = review.comment
        
        return render_template('property/guest_review_form.html',
                              form=form,
                              property=property,
                              review=review,
                              title=f'Edit Guest Review - {property.name}')
    
    @bp.route('/guest-reviews/<int:review_id>/delete', methods=['POST'])
    @login_required
    def delete_guest_review(review_id):
        """Delete a guest review"""
        # Check if guest reviews are enabled
        if not SiteSettings.is_guest_reviews_enabled():
            flash('Guest reviews feature is currently disabled.', 'warning')
            return redirect(url_for('main.index'))
            
        review = GuestReview.query.get_or_404(review_id)
        property_id = review.property_id
        
        # Check if user has permission to delete this review
        if not can_edit_guest_review(review):
            flash('Access denied. You do not have permission to delete this guest review.', 'danger')
            return redirect(url_for('property.guest_reviews', id=property_id))
        
        db.session.delete(review)
        db.session.commit()
        
        flash('Guest review deleted successfully!', 'success')
        return redirect(url_for('property.guest_reviews', id=property_id))

# Permission check functions
def can_view_guest_reviews(property):
    """Check if the current user can view guest reviews for a property"""
    # Property owners can view reviews for their own properties
    if property.owner_id == current_user.id:
        return True
    
    # Property managers can view reviews for all properties
    if current_user.is_property_manager():
        return True
    
    # Admins can view all reviews
    if current_user.is_admin:
        return True
    
    return False

def can_manage_guest_reviews(property):
    """Check if the current user can add/edit guest reviews for a property"""
    # Property owners can manage reviews for their own properties
    if property.owner_id == current_user.id:
        return True
    
    # Property managers can manage reviews for all properties
    if current_user.is_property_manager():
        return True
    
    # Admins can manage all reviews
    if current_user.is_admin:
        return True
    
    return False

def can_edit_guest_review(review):
    """Check if the current user can edit a specific guest review"""
    # Users can edit their own reviews
    if review.creator_id == current_user.id:
        return True
    
    # Property owners can edit reviews for their own properties
    if review.property.owner_id == current_user.id:
        return True
    
    # Property managers can edit all reviews
    if current_user.is_property_manager():
        return True
    
    # Admins can edit all reviews
    if current_user.is_admin:
        return True
    
    return False
