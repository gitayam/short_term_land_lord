"""
Routes for guest invitation, registration, and portal functionality
"""

from flask import render_template, request, flash, redirect, url_for, current_app, abort, jsonify, session
from flask_login import login_required, current_user, login_user, logout_user
from app.guest import bp
from app.forms.guest_forms import (
    GuestInvitationForm, GuestRegistrationForm, GuestProfileForm, 
    DirectBookingForm, BulkInvitationForm, PropertyBrowseFilterForm,
    EmailVerificationForm, PasswordResetRequestForm, PasswordResetForm
)
from app.models import (
    Property, User, GuestInvitation, GuestBooking, UserRoles, db
)
from app.auth.decorators import property_owner_required, admin_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets


# ============================================================================
# PUBLIC ROUTES (No Authentication Required)
# ============================================================================

@bp.route('/browse')
def browse_properties():
    """Public property browsing for unauthenticated users"""
    form = PropertyBrowseFilterForm(request.args)
    
    # Build query for public properties
    query = Property.query.filter_by(status='active')
    
    # Apply filters
    if form.city.data:
        query = query.filter(Property.city.ilike(f'%{form.city.data}%'))
    
    if form.state.data:
        query = query.filter_by(state=form.state.data)
    
    if form.property_type.data:
        query = query.filter_by(property_type=form.property_type.data)
    
    # Filter by minimum bedrooms if specified
    if form.min_bedrooms.data:
        min_bedrooms = int(form.min_bedrooms.data)
        query = query.filter(Property.bedrooms >= min_bedrooms)
    
    # Get properties with limited public information
    properties = query.order_by(Property.name).limit(50).all()
    
    # Create safe property data for public view
    public_properties = []
    for prop in properties:
        public_properties.append({
            'id': prop.id,
            'name': prop.name,
            'city': prop.city,
            'state': prop.state,
            'property_type': prop.property_type,
            'bedrooms': getattr(prop, 'bedrooms', None),
            'bathrooms': getattr(prop, 'bathrooms', None),
            'max_guests': getattr(prop, 'max_guests', None),
            'image_url': getattr(prop, 'image_url', '/static/img/default-property.jpg'),
            'description': getattr(prop, 'description', '')[:200] + '...' if getattr(prop, 'description', '') else '',
            'amenities': getattr(prop, 'amenities', [])[:5]  # Show first 5 amenities only
        })
    
    return render_template('guest/browse_properties.html',
                         title='Browse Properties',
                         properties=public_properties,
                         form=form)


@bp.route('/browse/property/<int:property_id>')
def view_property_public(property_id):
    """Public property details view"""
    property = Property.query.get_or_404(property_id)
    
    if property.status != 'active':
        abort(404)
    
    # Create safe property data for public view (no sensitive information)
    public_property = {
        'id': property.id,
        'name': property.name,
        'city': property.city,
        'state': property.state,
        'property_type': property.property_type,
        'bedrooms': getattr(property, 'bedrooms', None),
        'bathrooms': getattr(property, 'bathrooms', None),
        'max_guests': getattr(property, 'max_guests', None),
        'image_url': getattr(property, 'image_url', '/static/img/default-property.jpg'),
        'description': getattr(property, 'description', ''),
        'amenities': getattr(property, 'amenities', []),
        'local_attractions': getattr(property, 'local_attractions', ''),
        'nearby_restaurants': getattr(property, 'nearby_restaurants', ''),
        'transportation_info': getattr(property, 'transportation_info', '')
    }
    
    return render_template('guest/property_public.html',
                         title=f'{property.name} - Property Details',
                         property=public_property)


@bp.route('/register/<invitation_code>', methods=['GET', 'POST'])
def register_with_code(invitation_code):
    """Guest registration using invitation code"""
    # Verify invitation code exists and is valid
    invitation = GuestInvitation.get_by_code(invitation_code)
    if not invitation or not invitation.is_available:
        flash('Invalid or expired invitation code.', 'error')
        return redirect(url_for('guest.register_help'))
    
    form = GuestRegistrationForm()
    form.invitation_code.data = invitation_code
    
    if form.validate_on_submit():
        try:
            # Create new guest user
            user = User(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                password_hash=generate_password_hash(form.password.data),
                role=UserRoles.PROPERTY_GUEST.value,
                invitation_code_id=invitation.id,
                marketing_emails_consent=form.marketing_emails_consent.data,
                booking_reminders_consent=form.booking_reminders_consent.data,
                is_active=True
            )
            
            # Generate email verification token
            user.email_verification_token = secrets.token_urlsafe(32)
            user.email_verification_sent_at = datetime.utcnow()
            
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Mark invitation as used
            invitation.mark_as_used(user.id)
            
            db.session.commit()
            
            # TODO: Send verification email
            current_app.logger.info(f"New guest user registered: {user.email} with invitation {invitation_code}")
            
            flash('Account created successfully! Please check your email to verify your account.', 'success')
            return redirect(url_for('guest.verify_email', token=user.email_verification_token))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating guest user: {str(e)}")
            flash('An error occurred creating your account. Please try again.', 'error')
    
    return render_template('guest/register.html',
                         title='Create Guest Account',
                         form=form,
                         invitation=invitation)


@bp.route('/register/help')
def register_help():
    """Help page for users without invitation codes"""
    return render_template('guest/register_help.html',
                         title='Guest Registration Help')


@bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification endpoint"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Invalid verification token.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.email_verified:
        flash('Email already verified. You can log in.', 'info')
        return redirect(url_for('auth.login'))
    
    # Check if token is expired (7 days)
    if (datetime.utcnow() - user.email_verification_sent_at) > timedelta(days=7):
        flash('Verification token has expired. Please contact support.', 'error')
        return redirect(url_for('guest.register_help'))
    
    # Verify email
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_sent_at = None
    db.session.commit()
    
    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


# ============================================================================
# AUTHENTICATED GUEST ROUTES
# ============================================================================

@bp.route('/dashboard')
@login_required
def dashboard():
    """Guest dashboard - only for guest users"""
    if not current_user.is_guest_user:
        abort(403)
    
    # Get guest's booking history
    bookings = GuestBooking.get_by_guest(current_user.id)
    
    # Get properties the guest has stayed at
    properties = current_user.get_guest_properties()
    
    # Get current/upcoming bookings
    current_bookings = [b for b in bookings if b.is_current or b.is_future]
    past_bookings = [b for b in bookings if b.is_past]
    
    return render_template('guest/dashboard.html',
                         title='My Account',
                         current_bookings=current_bookings,
                         past_bookings=past_bookings,
                         properties=properties)


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Guest profile management"""
    if not current_user.is_guest_user:
        abort(403)
    
    form = GuestProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.timezone = form.timezone.data
        current_user.language = form.language.data
        current_user.theme_preference = form.theme_preference.data
        current_user.marketing_emails_consent = form.marketing_emails_consent.data
        current_user.booking_reminders_consent = form.booking_reminders_consent.data
        current_user.email_notifications = form.email_notifications.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('guest.profile'))
    
    return render_template('guest/profile.html',
                         title='My Profile',
                         form=form)


@bp.route('/bookings')
@login_required
def bookings():
    """Guest booking history and management"""
    if not current_user.is_guest_user:
        abort(403)
    
    # Get all bookings for the guest
    all_bookings = GuestBooking.get_by_guest(current_user.id)
    
    # Separate by status
    upcoming_bookings = [b for b in all_bookings if b.is_future]
    current_bookings = [b for b in all_bookings if b.is_current]
    past_bookings = [b for b in all_bookings if b.is_past]
    
    return render_template('guest/bookings.html',
                         title='My Bookings',
                         upcoming_bookings=upcoming_bookings,
                         current_bookings=current_bookings,
                         past_bookings=past_bookings)


@bp.route('/book/<int:property_id>', methods=['GET', 'POST'])
@login_required
def book_property(property_id):
    """Direct booking for verified guests"""
    if not current_user.is_guest_user:
        abort(403)
    
    if not current_user.email_verified:
        flash('Please verify your email before making bookings.', 'warning')
        return redirect(url_for('guest.dashboard'))
    
    property = Property.query.get_or_404(property_id)
    
    # Check if guest has previous booking history with this property
    previous_bookings = GuestBooking.query.filter_by(
        guest_user_id=current_user.id,
        property_id=property_id
    ).count()
    
    if previous_bookings == 0:
        flash('Direct booking is only available for returning guests.', 'info')
        return redirect(url_for('guest.view_property_public', property_id=property_id))
    
    form = DirectBookingForm()
    form.property_id.data = property_id
    
    if form.validate_on_submit():
        try:
            # Create direct booking
            booking = GuestBooking.create_direct_booking(
                guest_user_id=current_user.id,
                property_id=property_id,
                check_in_date=form.check_in_date.data,
                check_out_date=form.check_out_date.data,
                guest_count=form.guest_count.data,
                special_requests=form.special_requests.data
            )
            
            flash(f'Booking request submitted! Confirmation code: {booking.confirmation_code}', 'success')
            return redirect(url_for('guest.bookings'))
            
        except Exception as e:
            current_app.logger.error(f"Error creating direct booking: {str(e)}")
            flash('An error occurred processing your booking. Please try again.', 'error')
    
    return render_template('guest/book_property.html',
                         title=f'Book {property.name}',
                         form=form,
                         property=property,
                         previous_bookings=previous_bookings)


# ============================================================================
# PROPERTY OWNER/ADMIN ROUTES (Invitation Management)
# ============================================================================

@bp.route('/admin/invitations')
@login_required
@property_owner_required
def manage_invitations():
    """Manage guest invitations - property owners only"""
    # Get user's properties for invitation filtering
    if current_user.has_admin_role or current_user.is_property_manager:
        properties = Property.query.all()
    else:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    
    # Get active invitations
    property_ids = [p.id for p in properties]
    
    if property_ids:
        invitations = GuestInvitation.query.filter(
            GuestInvitation.property_id.in_(property_ids + [None])  # Include property-specific and general invitations
        ).order_by(GuestInvitation.created_at.desc()).all()
    else:
        invitations = []
    
    return render_template('guest/admin/manage_invitations.html',
                         title='Manage Guest Invitations',
                         invitations=invitations,
                         properties=properties)


@bp.route('/admin/invitations/create', methods=['GET', 'POST'])
@login_required
@property_owner_required
def create_invitation():
    """Create new guest invitation"""
    form = GuestInvitationForm()
    
    # Populate property choices
    if current_user.has_admin_role or current_user.is_property_manager:
        properties = Property.query.all()
    else:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    
    form.property_id.choices = [(0, 'All Properties')] + [(p.id, p.name) for p in properties]
    
    if form.validate_on_submit():
        try:
            property_id = form.property_id.data if form.property_id.data != 0 else None
            
            invitation = GuestInvitation.create_invitation(
                created_by_id=current_user.id,
                property_id=property_id,
                email=form.email.data or None,
                guest_name=form.guest_name.data or None,
                expires_in_days=form.expires_in_days.data,
                max_uses=form.max_uses.data,
                notes=form.notes.data or None
            )
            
            flash(f'Guest invitation created! Code: {invitation.code}', 'success')
            return redirect(url_for('guest.manage_invitations'))
            
        except Exception as e:
            current_app.logger.error(f"Error creating invitation: {str(e)}")
            flash('An error occurred creating the invitation. Please try again.', 'error')
    
    return render_template('guest/admin/create_invitation.html',
                         title='Create Guest Invitation',
                         form=form)


@bp.route('/admin/invitations/bulk', methods=['GET', 'POST'])
@login_required
@property_owner_required
def bulk_invitations():
    """Create multiple guest invitations"""
    form = BulkInvitationForm()
    
    # Populate property choices
    if current_user.has_admin_role or current_user.is_property_manager:
        properties = Property.query.all()
    else:
        properties = Property.query.filter_by(owner_id=current_user.id).all()
    
    form.property_id.choices = [(0, 'All Properties')] + [(p.id, p.name) for p in properties]
    
    if form.validate_on_submit():
        try:
            emails = [email.strip() for email in form.guest_emails.data.split('\n') if email.strip()]
            property_id = form.property_id.data if form.property_id.data != 0 else None
            
            created_invitations = []
            
            for email in emails:
                invitation = GuestInvitation.create_invitation(
                    created_by_id=current_user.id,
                    property_id=property_id,
                    email=email,
                    expires_in_days=form.expires_in_days.data,
                    notes=form.notes.data or None
                )
                created_invitations.append(invitation)
            
            flash(f'Created {len(created_invitations)} guest invitations successfully!', 'success')
            return redirect(url_for('guest.manage_invitations'))
            
        except Exception as e:
            current_app.logger.error(f"Error creating bulk invitations: {str(e)}")
            flash('An error occurred creating the invitations. Please try again.', 'error')
    
    return render_template('guest/admin/bulk_invitations.html',
                         title='Create Bulk Invitations',
                         form=form)


@bp.route('/admin/invitations/<int:invitation_id>/deactivate', methods=['POST'])
@login_required
@property_owner_required
def deactivate_invitation(invitation_id):
    """Deactivate a guest invitation"""
    invitation = GuestInvitation.query.get_or_404(invitation_id)
    
    # Check permissions
    if not (current_user.has_admin_role or current_user.is_property_manager or 
            invitation.created_by_id == current_user.id):
        abort(403)
    
    invitation.is_active = False
    db.session.commit()
    
    flash('Invitation deactivated successfully.', 'success')
    return redirect(url_for('guest.manage_invitations'))


# ============================================================================
# API ENDPOINTS
# ============================================================================

@bp.route('/api/properties')
def api_properties():
    """API endpoint for property search"""
    # Get query parameters
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    property_type = request.args.get('type', '')
    
    # Build query
    query = Property.query.filter_by(status='active')
    
    if city:
        query = query.filter(Property.city.ilike(f'%{city}%'))
    if state:
        query = query.filter_by(state=state)
    if property_type:
        query = query.filter_by(property_type=property_type)
    
    properties = query.order_by(Property.name).limit(20).all()
    
    # Return safe property data
    property_data = []
    for prop in properties:
        property_data.append({
            'id': prop.id,
            'name': prop.name,
            'city': prop.city,
            'state': prop.state,
            'property_type': prop.property_type,
            'image_url': getattr(prop, 'image_url', '/static/img/default-property.jpg')
        })
    
    return jsonify({
        'success': True,
        'properties': property_data,
        'total': len(property_data)
    })


@bp.route('/api/invitation/<code>/status')
def api_invitation_status(code):
    """API endpoint to check invitation status"""
    invitation = GuestInvitation.get_by_code(code)
    
    if not invitation:
        return jsonify({
            'valid': False,
            'message': 'Invalid invitation code'
        })
    
    return jsonify({
        'valid': invitation.is_available,
        'expired': invitation.is_expired,
        'used': invitation.current_uses >= invitation.max_uses,
        'expires_at': invitation.expires_at.isoformat(),
        'property_name': invitation.property_ref.name if invitation.property_ref else 'All Properties'
    })