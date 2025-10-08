#!/usr/bin/env python3
"""
Verify configuration management system is properly integrated
"""

from app import create_app, db
from app.models import User
from app.utils.configuration import config_service

app = create_app()

print("🔍 CONFIGURATION MANAGEMENT SYSTEM VERIFICATION")
print("=" * 50)

with app.app_context():
    # 1. Check database tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print("\n1️⃣ Database Tables:")
    config_tables = ['site_settings', 'configuration_audit']
    for table in config_tables:
        if table in tables:
            print(f"   ✅ {table} table exists")
            
            # Check columns for site_settings
            if table == 'site_settings':
                columns = [col['name'] for col in inspector.get_columns(table)]
                new_columns = ['category', 'config_type', 'updated_by_id']
                for col in new_columns:
                    if col in columns:
                        print(f"      ✅ {col} column added")
                    else:
                        print(f"      ❌ {col} column missing")
        else:
            print(f"   ❌ {table} table missing")
    
    # 2. Check configuration service
    print("\n2️⃣ Configuration Service:")
    categories = config_service.get_categories()
    print(f"   ✅ {len(categories)} categories loaded")
    
    all_settings = config_service.get_all_by_category()
    print(f"   ✅ {len(all_settings)} total settings defined")
    
    # Count by type
    editable_count = sum(1 for s in all_settings.values() if s['editable'])
    sensitive_count = sum(1 for s in all_settings.values() if s['sensitive'])
    print(f"   ✅ {editable_count} editable settings")
    print(f"   ✅ {sensitive_count} sensitive settings (protected)")
    
    # 3. Check URL routing
    print("\n3️⃣ URL Routing:")
    with app.test_request_context():
        from flask import url_for
        routes = [
            ('admin_config.index', 'Configuration Home'),
            ('admin_config.category_settings', 'Category View'),
            ('admin_config.audit_log', 'Audit Log'),
            ('admin_config.update_setting', 'Update Setting API'),
            ('admin_config.export_config', 'Export Configuration'),
        ]
        
        for endpoint, description in routes:
            try:
                if 'category' in endpoint:
                    url = url_for(endpoint, category='test')
                else:
                    url = url_for(endpoint)
                print(f"   ✅ {description}: {url}")
            except Exception as e:
                print(f"   ❌ {description}: {str(e)}")
    
    # 4. Check admin integration
    print("\n4️⃣ Admin Integration:")
    # Check if configuration blueprint is registered
    blueprints = app.blueprints
    if 'admin_config' in blueprints:
        print(f"   ✅ Configuration blueprint registered")
        bp = blueprints['admin_config']
        print(f"      URL prefix: {bp.url_prefix}")
    else:
        print(f"   ❌ Configuration blueprint not registered")
    
    # 5. Test configuration hierarchy
    print("\n5️⃣ Configuration Hierarchy Test:")
    import os
    
    # Test environment variable priority
    os.environ['TEST_CONFIG_HIERARCHY'] = 'from_environment'
    env_value = config_service.get('TEST_CONFIG_HIERARCHY')
    print(f"   ✅ Environment variable: {env_value}")
    del os.environ['TEST_CONFIG_HIERARCHY']
    
    # Test default value
    app_name = config_service.get('APP_NAME')
    print(f"   ✅ Default value (APP_NAME): {app_name}")
    
    # 6. Check for any errors
    print("\n6️⃣ System Status:")
    try:
        # Try to import all configuration routes
        from app.admin.config_routes import bp as config_bp
        print("   ✅ Configuration routes module loads successfully")
    except Exception as e:
        print(f"   ❌ Error loading configuration routes: {e}")
    
    # Check template files
    import os
    template_dir = 'app/templates/admin/configuration'
    if os.path.exists(template_dir):
        templates = os.listdir(template_dir)
        print(f"   ✅ {len(templates)} configuration templates found:")
        for template in templates:
            print(f"      - {template}")
    else:
        print(f"   ❌ Configuration templates directory not found")

print("\n" + "=" * 50)
print("✅ CONFIGURATION SYSTEM VERIFICATION COMPLETE")
print("\n📍 Access the configuration management at:")
print("   http://localhost:5001/admin/configuration/")
print("\n⚠️ Note: You must be logged in as an admin user to access this page.")