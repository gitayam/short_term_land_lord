from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm, SSOLoginForm, PropertyRegistrationForm, InviteServiceStaffForm
from app.models import User, PasswordReset, UserRoles, RegistrationRequest, ApprovalStatus
from app.auth.email import send_password_reset_email, send_service_staff_invitation
import secrets

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    from flask import current_app
    
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
            password=password,
            confirmed=False
        )
        
        # Assign service staff role
        service_staff_role = Role.query.filter_by(name='Service Staff').first()
        if service_staff_role:
            user.role = service_staff_role
        
        db.session.add(user)
        db.session.commit()
        
        # Send invitation email with temporary password
        token = user.generate_confirmation_token()
        send_service_staff_invitation(user, token, password)
        
        flash('An invitation has been sent to {}.'.format(user.email), 'success')
        return redirect(url_for('auth.invite_service_staff'))
    
    return render_template('auth/invite_service_staff.html', form=form)