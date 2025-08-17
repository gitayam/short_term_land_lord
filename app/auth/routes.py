from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from app import db
from app.auth import bp
from app.auth.forms import RegistrationForm, PropertyRegistrationForm, LoginForm, RequestPasswordResetForm, ResetPasswordForm, InviteServiceStaffForm
from app.models import User, RegistrationRequest, Property, UserRoles, ApprovalStatus
from urllib.parse import urlparse as url_parse
from sqlalchemy import or_
import secrets

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            # Redirect to dashboard for better UX after login
            next_page = url_for('main.dashboard')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Sign In', 
                         local_form=form, use_local=True)


@bp.route('/logout')
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('main.index'))

# ... (other imports and functions remain the same) ...

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Pre-fill invitation code if provided in URL
    invitation_code = request.args.get('invitation_code')
    
    # Start with a clean session by rolling back any existing transactions
    try:
        db.session.rollback()
    except Exception as e:
        # Use try-except to handle cases where current_app might be None
        try:
            if current_app:
                current_app.logger.error(f"Error rolling back session: {str(e)}")
            else:
                print(f"ERROR: Error rolling back session (current_app unavailable): {str(e)}")  # Fallback logging
        except Exception as log_error:
            print(f"ERROR: Failed to log rollback error: {str(e)}, Logging error: {str(log_error)}")
    
    form = RegistrationForm()
    
    # Pre-fill invitation code if provided
    if invitation_code and request.method == 'GET':
        form.invitation_code.data = invitation_code
        form.role.data = 'guest'
    
    property_form = None
    
    # Handle property owner registration (two-step process)
    property_step = False
    if request.args.get('role') == 'property_owner' and request.args.get('step') == 'property':
        property_step = True
        property_form = PropertyRegistrationForm()
        
        # Debug: Print request method and form data
        print("\n=== Property Registration Debug ===")
        print(f"Request method: {request.method}")
        print(f"Form data: {request.form}")
        
        # Get user data from session
        user_data = session.get('registration_data', {})
        print(f"Session registration_data exists: {'registration_data' in session}")
        print(f"User data from session: {user_data}")
        
        if not user_data:
            flash('Registration information missing. Please start again.', 'danger')
            print("No user data in session, redirecting to register")
            return redirect(url_for('auth.register'))
            
        # Handle property form submission
        print(f"Validating property form. Form valid: {property_form.validate()}")
        if not property_form.validate():
            print(f"Property form errors: {property_form.errors}")
            
        if property_form.validate_on_submit():
            print("Property form is valid, processing submission...")
            user_data['property_name'] = property_form.property_name.data
            user_data['property_address'] = property_form.property_address.data
            user_data['property_description'] = property_form.property_description.data
            print(f"Updated user_data with property info: {user_data}")
            
            try:
                # Import models at function level to ensure they're available in all code paths
                from app.models import User, RegistrationRequest
                from sqlalchemy import or_
                
                # In test environment, don't close the session as it's managed by the test client
                if not current_app.testing:
                    db.session.close()
                
                # Only check for duplicates during initial registration, not property registration
                if not property_step:
                    
                    # Check if email exists in users table or has a pending registration request
                    user_exists = db.session.query(
                        db.session.query(User).filter_by(email=user_data['email']).exists()
                    ).scalar()
                    
                    pending_request_exists = db.session.query(
                        db.session.query(RegistrationRequest).filter(
                            RegistrationRequest.email == user_data['email'],
                            RegistrationRequest.status == 'PENDING'
                        ).exists()
                    ).scalar()
                    
                    if user_exists or pending_request_exists:
                        flash('Email address already registered or pending approval. Please use a different email.', 'danger')
                        return render_template('auth/register.html', title='Register', form=form)
                    
                # Create the registration request
                from werkzeug.security import generate_password_hash
                
                # Hash the password if it's in plaintext
                password = user_data.get('password')
                if not password and 'password_hash' in user_data:
                    password = user_data['password_hash']
                elif password:
                    password = generate_password_hash(password)
                else:
                    flash('Password is required', 'danger')
                    return redirect(url_for('auth.register'))
                
                # Start a transaction
                try:
                    # Create registration request
                    request_obj = RegistrationRequest(
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        email=user_data['email'],
                        phone=user_data.get('phone'),
                        role=user_data['role'],
                        password_hash=password,
                        property_name=user_data.get('property_name'),
                        property_address=user_data.get('property_address'),
                        property_description=user_data.get('property_description'),
                        message=user_data.get('message', ''),
                        status=ApprovalStatus.PENDING
                    )
                    db.session.add(request_obj)
                    db.session.flush()  # Flush to get the ID
                    
                    # If this is a property owner with property details, create the property
                    if user_data['role'] == UserRoles.PROPERTY_OWNER.value and 'property_name' in user_data:
                        from app.models import Property
                        
                        property_obj = Property(
                            name=user_data['property_name'],
                            address=user_data.get('property_address', ''),
                            description=user_data.get('property_description', ''),
                            status='inactive',  # New properties start as inactive
                            property_type='house',  # Default property type
                            owner_id=1  # Will be updated after approval
                        )
                        db.session.add(property_obj)
                    
                    # Commit the transaction
                    db.session.commit()
                    
                except Exception as e:
                    db.session.rollback()
                    # Use try-except to handle cases where current_app might be None
                    try:
                        if current_app:
                            current_app.logger.error(f"Error during registration: {str(e)}")
                        else:
                            print(f"Error during registration: {str(e)}")
                    except Exception as log_err:
                        print(f"Error logging registration error: {str(log_err)}")
                    flash('An error occurred during registration. Please try again.', 'danger')
                    return render_template('auth/register_property.html', title='Register Property', form=property_form)
                
                # Clear session data
                session.pop('registration_data', None)
                
                # Ensure the flash message is properly set
                flash_message = 'Your registration request has been submitted! An administrator will review your request soon.'
                flash(flash_message, 'success')
                
                # For debugging in tests
                if current_app.testing:
                    session['_flashes'] = session.get('_flashes', []) + [('success', flash_message)]
                
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                # Use try-except to handle cases where current_app might be None
                try:
                    if current_app:
                        current_app.logger.error(f"Registration error: {str(e)}")
                    else:
                        print(f"ERROR: Registration error (current_app unavailable): {str(e)}")  # Fallback logging
                except Exception as log_error:
                    print(f"ERROR: Failed to log registration error: {str(e)}, Logging error: {str(log_error)}")
                flash(f'An error occurred during registration. Please try again. Error: {str(e)}', 'danger')
                return render_template('auth/register_property.html', title='Register Property', form=property_form)
        
        return render_template('auth/register_property.html', title='Register Property', form=property_form)
    
    # Handle initial registration form
    if form.validate_on_submit():
        try:
            # Start with a new session to avoid any transaction issues
            db.session.close()
            
            # Check if email already exists using SQLAlchemy ORM
            from app.models import User, RegistrationRequest
            
            # Check if email exists in users table or has a pending registration request
            user_exists = User.query.filter_by(email=form.email.data).first() is not None
            
            pending_request_exists = RegistrationRequest.query.filter_by(email=form.email.data, status=ApprovalStatus.PENDING).first() is not None
            
            if user_exists or pending_request_exists:
                flash('Email address already registered or pending approval. Please use a different email.', 'danger')
                return render_template('auth/register.html', title='Register', form=form)
                
            # Generate a username if not provided
            username = None
            if hasattr(form, 'username') and form.username.data:
                username = form.username.data
            
            # If this is a guest registration, handle immediately
            if form.role.data == 'guest':
                try:
                    # Import models
                    from app.models import GuestInvitation, GuestBooking
                    
                    # Get and validate invitation
                    invitation = GuestInvitation.query.filter_by(
                        invitation_code=form.invitation_code.data,
                        is_active=True,
                        is_used=False
                    ).first()
                    
                    if not invitation or invitation.is_expired():
                        flash('Invalid or expired invitation code.', 'danger')
                        return render_template('auth/register.html', title='Register', form=form)
                    
                    # Create guest user directly (no approval needed)
                    guest_user = User(
                        email=form.email.data,
                        first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        phone=form.phone.data if hasattr(form, 'phone') else None,
                        role=UserRoles.GUEST.value,
                        is_active=True,
                        username=form.username.data if hasattr(form, 'username') and form.username.data else None
                    )
                    guest_user.set_password(form.password.data)
                    
                    db.session.add(guest_user)
                    db.session.flush()  # Get the user ID
                    
                    # Create guest booking record
                    guest_booking = GuestBooking(
                        guest_id=guest_user.id,
                        invitation_id=invitation.id,
                        property_id=invitation.property_id
                    )
                    db.session.add(guest_booking)
                    
                    # Mark invitation as used
                    invitation.uses += 1
                    if invitation.uses >= invitation.max_uses:
                        invitation.is_used = True
                    
                    db.session.commit()
                    
                    flash('Registration successful! You can now log in.', 'success')
                    return redirect(url_for('auth.login'))
                    
                except Exception as e:
                    db.session.rollback()
                    try:
                        if current_app:
                            current_app.logger.error(f"Error during guest registration: {str(e)}")
                        else:
                            print(f"ERROR: Error during guest registration: {str(e)}")
                    except Exception as log_error:
                        print(f"ERROR: Failed to log guest registration error: {str(e)}, Logging error: {str(log_error)}")
                    flash('An error occurred during registration. Please try again.', 'danger')
                    return render_template('auth/register.html', title='Register', form=form)
            
            # If this is a property owner, go to step 2
            elif form.role.data == UserRoles.PROPERTY_OWNER.value:
                # Store data in session for the next step
                try:
                    # Create registration request
                    registration = RegistrationRequest(
                        first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        email=form.email.data,
                        password_hash='',  # Will be set below
                        role=form.role.data,
                        phone=form.phone.data if hasattr(form, 'phone') else None,
                        status=ApprovalStatus.PENDING,
                        created_at=datetime.utcnow()
                    )
                    # Set the password using the User model's set_password method
                    user = User()
                    user.set_password(form.password.data)
                    registration.password_hash = user.password_hash
                    
                    db.session.add(registration)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    # Use try-except to handle cases where current_app might be None
                    try:
                        if current_app:
                            current_app.logger.error(f"Error creating registration request: {str(e)}")
                        else:
                            print(f"ERROR: Error creating registration request (current_app unavailable): {str(e)}")  # Fallback logging
                    except Exception as log_error:
                        print(f"ERROR: Failed to log registration request error: {str(e)}, Logging error: {str(log_error)}")
                    flash('An error occurred during registration. Please try again.', 'danger')
                    return render_template('auth/register.html', title='Register', form=form)
                
                # Store in session
                session['registration_data'] = {
                    'username': username,
                    'first_name': form.first_name.data,
                    'last_name': form.last_name.data,
                    'email': form.email.data,
                    'phone': form.phone.data if hasattr(form, 'phone') else None,
                    'role': form.role.data,
                    'password': form.password.data,
                    'message': form.message.data
                }
                
                return redirect(url_for('auth.register', role='property_owner', step='property'))
            else:
                # For other roles, create registration request directly
                try:
                    # Create registration request
                    registration = RegistrationRequest(
                        first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        email=form.email.data,
                        password_hash='',  # Will be set below
                        role=form.role.data,
                        phone=form.phone.data if hasattr(form, 'phone') else None,
                        status=ApprovalStatus.PENDING,
                        created_at=datetime.utcnow(),
                        message=form.message.data
                    )
                    # Set the password using the User model's set_password method
                    user = User()
                    user.set_password(form.password.data)
                    registration.password_hash = user.password_hash
                    
                    db.session.add(registration)
                    db.session.commit()
                    
                    flash('Your registration request has been submitted! An administrator will review your request soon.', 'success')
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    db.session.rollback()
                    # Use try-except to handle cases where current_app might be None
                    try:
                        if current_app:
                            current_app.logger.error(f"Error creating registration request: {str(e)}")
                        else:
                            print(f"ERROR: Error creating registration request (current_app unavailable): {str(e)}")  # Fallback logging
                    except Exception as log_error:
                        print(f"ERROR: Failed to log registration request error: {str(e)}, Logging error: {str(log_error)}")
                    flash('An error occurred during registration. Please try again.', 'danger')
                    return render_template('auth/register.html', title='Register', form=form)
        except Exception as e:
            db.session.rollback()
            # Use try-except to handle cases where current_app might be None
            try:
                if current_app:
                    current_app.logger.error(f"Registration error: {str(e)}")
                else:
                    print(f"ERROR: Registration error (current_app unavailable): {str(e)}")  # Fallback logging
            except Exception as log_error:
                print(f"ERROR: Failed to log registration error: {str(e)}, Logging error: {str(log_error)}")
            flash(f'An error occurred during registration. Please try again. Error: {str(e)}', 'danger')
    
    return render_template('auth/register.html', title='Register', form=form)

# ... (rest of the file remains the same) ...
