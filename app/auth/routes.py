from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm, SSOLoginForm, PropertyRegistrationForm
from app.models import User, PasswordReset, UserRoles, RegistrationRequest, ApprovalStatus
from app.auth.email import send_password_reset_email

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
            
            # Check if email already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            existing_request = RegistrationRequest.query.filter_by(email=user_data['email'], 
                                                                  status=ApprovalStatus.PENDING).first()
            
            if existing_user or existing_request:
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
            
            db.session.add(request_obj)
            db.session.commit()
            
            # Clear session data
            session.pop('registration_data', None)
            
            flash('Your registration request has been submitted! An administrator will review your request soon.', 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('auth/register_property.html', title='Register Property', form=property_form)
    
    # Handle initial registration form
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        existing_request = RegistrationRequest.query.filter_by(email=form.email.data, 
                                                              status=ApprovalStatus.PENDING).first()
        
        if existing_user or existing_request:
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
            
            try:
                db.session.commit()
                flash('Your registration request has been submitted! An administrator will review your request soon.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'danger')
    
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