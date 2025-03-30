from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
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
    
    # Initialize site settings
    with app.app_context():
        from app.models import migrate_site_settings
        migrate_site_settings()
    return app

from app import models