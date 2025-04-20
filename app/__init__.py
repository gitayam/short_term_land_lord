from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

from app.user_model_fix import patch_user_model, patch_user_loader
# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Initialize task permission functions for templates
    from app.tasks.routes import can_view_task, can_edit_task, can_delete_task, can_complete_task
    app.jinja_env.globals.update(
        can_view_task=can_view_task,
        can_edit_task=can_edit_task,
        can_delete_task=can_delete_task,
        can_complete_task=can_complete_task
    )
    
    # Register custom Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s:
            return s.replace('\n', '<br>')
        return s
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.profile import bp as profile_bp
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    from app.property import bp as property_bp
    app.register_blueprint(property_bp, url_prefix='/property')
    
    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    
    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    from app.inventory import bp as inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    
    from app.invoicing import bp as invoicing_bp
    app.register_blueprint(invoicing_bp, url_prefix='/invoicing')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.calendar import bp as calendar_bp
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    
    from app.workforce import bp as workforce_bp
    app.register_blueprint(workforce_bp, url_prefix='/workforce')
    
    # Initialize site settings and User model
    with app.app_context():
        try:
            from app.models import migrate_site_settings, create_admin_user_from_env, init_app as init_user_model
            
            # Initialize User model table name
            init_user_model(app)
            
            # Initialize site settings
            migrate_site_settings()
            
            # Create admin user from environment variables if configured
            create_admin_user_from_env()
        except Exception as e:
            # Handle the case where site_settings table doesn't exist yet
            app.logger.warning(f"Could not initialize site settings: {str(e)}")
            app.logger.info("You may need to run 'flask db upgrade' if this is a new installation")
    
    with app.app_context():
        # Apply database compatibility fixes
        patch_user_model()
        patch_user_loader()
    
    return app

from app import models