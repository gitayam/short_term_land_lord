from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm, SSOLoginForm, PropertyRegistrationForm, InviteServiceStaffForm
from app.models import User, PasswordReset, UserRoles, RegistrationRequest, ApprovalStatus, Role, ServiceType
from app.auth.email import send_password_reset_email, send_service_staff_invitation
import secrets

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Determine which authentication methods are enabled
    use_sso = current_app.config.get('AUTH_USE_SSO', True)
    use_local = current_app.config.get('AUTH_USE_LOCAL', True)
    
    # Create forms for each enabled authentication method
    local_form = LoginForm() if use_local else None
    sso_form = SSOLoginForm() if use_sso else None
    
    # Handle local authentication form submission
    if use_local and local_form and local_form.validate_on_submit():
        try:
            current_app.logger.info(f"Login form submitted for email: {local_form.email.data}")
            
            # Print the SQL query equivalent for debugging
            from sqlalchemy import text
            sql = text("SELECT * FROM users WHERE email = :email")
            result = db.session.execute(sql, {'email': local_form.email.data})
            user_data = result.fetchone()
            
            if user_data:
                current_app.logger.info(f"User found in database: {user_data.email}")
            else:
                current_app.logger.warning(f"User not found in database: {local_form.email.data}")
            
            user = User.query.filter_by(email=local_form.email.data).first()
            
            if user is None:
                current_app.logger.warning(f"Login attempt with non-existent email: {local_form.email.data}")
                flash('Invalid email or password', 'danger')
                return render_template('auth/login.html', 
                                      title='Sign In', 
                                      local_form=local_form,
                                      sso_form=sso_form,
                                      use_local=use_local,
                                      use_sso=use_sso)
            
            current_app.logger.info(f"Checking password for user: {user.email}, hash: {user.password_hash}")
            if not user.check_password(local_form.password.data):
                current_app.logger.warning(f"Failed login attempt for user: {user.email}")
                flash('Invalid email or password', 'danger')
                return render_template('auth/login.html', 
                                      title='Sign In', 
                                      local_form=local_form,
                                      sso_form=sso_form,
                                      use_local=use_local,
                                      use_sso=use_sso)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            login_user(user, remember=local_form.remember_me.data)
            current_app.logger.info(f"User logged in: {user.email}")
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            flash('You have been logged in successfully!', 'success')
            return redirect(next_page)
        except Exception as e:
            current_app.logger.error(f"Error during login: {str(e)}")
            flash('An error occurred during login. Please try again.', 'danger')
            db.session.rollback()
    
    # Handle SSO form submission (redirect to SSO provider)
    if use_sso and sso_form and sso_form.validate_on_submit():
        # This would typically redirect to your SSO provider
        # For now, just redirect to the main page with a message
        flash('SSO authentication is not yet implemented', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/login.html', 
                          title='Sign In', 
                          local_form=local_form,
                          sso_form=sso_form,
                          use_local=use_local,
                          use_sso=use_sso)

@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Start with a clean session by rolling back any existing transactions
    try:
        db.session.rollback()
    except:
        pass
    
    form = RegistrationForm()
    property_form = None
    
    # Handle property owner registration (two-step process)
    property_step = False
    if request.args.get('role') == 'property_owner' and request.args.get('step') == 'property':
        property_step = True
        property_form = PropertyRegistrationForm()
        
        # Get user data from session
        user_data = session.get('registration_data', {})
        if not user_data:
            flash('Registration information missing. Please start again.', 'danger')
            return redirect(url_for('auth.register'))
            
        # Handle property form submission
        if property_form.validate_on_submit():
            user_data['property_name'] = property_form.property_name.data
            user_data['property_address'] = property_form.property_address.data
            user_data['property_description'] = property_form.property_description.data
            
            try:
                # Start with a new session to avoid any transaction issues
                db.session.close()
                
                # Check if email already exists using direct connection
                with db.engine.connect() as conn:
                    from sqlalchemy import text
                    result = conn.execute(text("SELECT COUNT(*) FROM users WHERE email = :email"), 
                                        {"email": user_data['email']})
                    user_count = result.scalar()
                    
                    result = conn.execute(text("SELECT COUNT(*) FROM registration_requests WHERE email = :email AND status = 'pending'"),
                                        {"email": user_data['email']})
                    request_count = result.scalar()
                
                if user_count > 0 or request_count > 0:
                    flash('Email address already registered or pending approval. Please use a different email.', 'danger')
                    return render_template('auth/register_property.html', title='Register Property', form=property_form)
                    
                # Create the registration request
                request_obj = RegistrationRequest(
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    email=user_data['email'],
                    phone=user_data['phone'] if 'phone' in user_data else None,
                    role=user_data['role'],
                    password_hash=user_data['password_hash'],
                    property_name=user_data['property_name'],
                    property_address=user_data['property_address'],
                    property_description=user_data['property_description'],
                    message=user_data.get('message', ''),
                    status=ApprovalStatus.PENDING
                )
                
                # Use a fresh session
                db.session = db.create_scoped_session()
                db.session.add(request_obj)
                db.session.commit()
                
                # Clear session data
                session.pop('registration_data', None)
                
                flash('Your registration request has been submitted! An administrator will review your request soon.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                from flask import current_app
                current_app.logger.error(f"Registration error: {str(e)}")
                flash(f'An error occurred during registration. Please try again. Error: {str(e)}', 'danger')
                return render_template('auth/register_property.html', title='Register Property', form=property_form)
        
        return render_template('auth/register_property.html', title='Register Property', form=property_form)
    
    # Handle initial registration form
    if form.validate_on_submit():
        try:
            # Start with a new session to avoid any transaction issues
            db.session.close()
            
            # Check if email already exists using direct connection to avoid transaction issues
            with db.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT COUNT(*) FROM users WHERE email = :email"),
                                     {"email": form.email.data})
                user_count = result.scalar()
                
                result = conn.execute(text("SELECT COUNT(*) FROM registration_requests WHERE email = :email AND status = 'pending'"),
                                     {"email": form.email.data})
                request_count = result.scalar()
            
            if user_count > 0 or request_count > 0:
                flash('Email address already registered or pending approval. Please use a different email.', 'danger')
                return render_template('auth/register.html', title='Register', form=form)
                
            # Generate a username if not provided
            username = None
            if hasattr(form, 'username') and form.username.data:
                username = form.username.data
            # Username is now optional, so we're not generating one if not provided
            
            # If this is a property owner, go to step 2
            if form.role.data == UserRoles.PROPERTY_OWNER.value:
                # Store data in session for the next step
                user = User(
                    username=username,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    phone=form.phone.data if hasattr(form, 'phone') else None,
                    role=form.role.data
                )
                user.set_password(form.password.data)
                
                # Store in session
                session['registration_data'] = {
                    'username': username,
                    'first_name': form.first_name.data,
                    'last_name': form.last_name.data,
                    'email': form.email.data,
                    'phone': form.phone.data if hasattr(form, 'phone') else None,
                    'role': form.role.data,
                    'password_hash': user.password_hash,
                    'message': form.message.data
                }
                
                return redirect(url_for('auth.register', role='property_owner', step='property'))
            else:
                # For other roles, create registration request directly
                user = User(
                    username=username,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    phone=form.phone.data if hasattr(form, 'phone') else None,
                    role=form.role.data
                )
                user.set_password(form.password.data)
                
                # Use a fresh session
                db.session = db.create_scoped_session()
                
                request_obj = RegistrationRequest(
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    phone=form.phone.data if hasattr(form, 'phone') else None,
                    role=form.role.data,
                    password_hash=user.password_hash,
                    message=form.message.data,
                    status=ApprovalStatus.PENDING
                )
                
                db.session.add(request_obj)
                db.session.commit()
                flash('Your registration request has been submitted! An administrator will review your request soon.', 'success')
                return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Registration error: {str(e)}")
            flash(f'An error occurred during registration. Please try again. Error: {str(e)}', 'danger')
    
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        
        # Always show this message even if email doesn't exist (security best practice)
        flash('Check your email for instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = PasswordReset.verify_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        
        # Delete the used token
        PasswordReset.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)

@bp.route('/invite_service_staff', methods=['GET', 'POST'])
@login_required
def invite_service_staff():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.index'))
    
    form = InviteServiceStaffForm()
    if form.validate_on_submit():
        # Generate a random password for the new user
        password = User.generate_random_password()
        
        # Create the new user
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=UserRoles.SERVICE_STAFF.value
        )
        user.set_password(password)
        
        # Assign service type if specified
        user.service_type = form.service_type.data
        
        db.session.add(user)
        db.session.commit()
        
        # Get service type display name
        service_type_display = dict((t.value, t.name) for t in ServiceType).get(form.service_type.data, form.service_type.data)
        
        # Send invitation via selected channels
        delivery_status = {'email': False, 'sms': False}
        error_messages = []
        
        # Send email if requested
        if form.send_email.data:
            try:
                # Send invitation email with temporary password
                token = user.generate_confirmation_token()
                send_service_staff_invitation(user, token, password, form.message.data)
                delivery_status['email'] = True
            except Exception as e:
                error_messages.append(f'Email delivery failed: {str(e)}')
                current_app.logger.error(f"Email delivery failed: {str(e)}")
        
        # Send SMS if requested
        if form.send_sms.data and form.phone.data:
            try:
                from app.utils.sms import send_sms
                # Get the country code prefix
                country_code = next((code[1].split(' ')[0] for code in COUNTRY_CODES if code[0] == form.country_code.data), '+1')
                # Format the phone number with country code
                phone_number = form.phone.data.strip()
                # Remove any non-digit characters except +
                phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
                # Remove any existing country code from the phone number
                if phone_number.startswith('+'):
                    phone_number = phone_number[1:]
                # Ensure proper E.164 format
                full_phone = f"{country_code}{phone_number}"
                
                message = (
                    f"Hi {user.first_name}, you've been invited to join Short Term Landlord as a {service_type_display} staff member. "
                    f"Please check your email ({user.email}) for your login credentials and registration link. "
                    f"Contact support@shorttermlandlord.com if you have any questions."
                )
                
                # Log the SMS attempt
                current_app.logger.info(f"Attempting to send SMS to {full_phone}")
                success, error = send_sms(full_phone, message)
                
                if success:
                    delivery_status['sms'] = True
                    current_app.logger.info(f"SMS sent successfully to {full_phone}")
                else:
                    error_messages.append(f'SMS delivery failed: {error}')
                    current_app.logger.error(f"SMS delivery failed: {error}")
            except Exception as e:
                error_msg = f'SMS delivery failed: {str(e)}'
                error_messages.append(error_msg)
                current_app.logger.error(error_msg)
        
        # Prepare flash message based on delivery status
        if delivery_status['email'] or delivery_status['sms']:
            status_msg = []
            if delivery_status['email']:
                status_msg.append('email')
            if delivery_status['sms']:
                status_msg.append('SMS')
            flash(f'Invitation sent to {user.get_full_name()} via {", ".join(status_msg)}.', 'success')
        else:
            flash('Failed to send invitation. Please try again.', 'danger')
        
        if error_messages:
            for error in error_messages:
                flash(error, 'warning')
        
        return redirect(url_for('auth.invite_service_staff'))
    
    return render_template('auth/invite_service_staff.html', title='Invite Service Staff', form=form)