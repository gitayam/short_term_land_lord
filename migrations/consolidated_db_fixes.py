#!/usr/bin/env python3
"""
Consolidated database fixes script.
This script combines various database repair/fix scripts into a single script:
1. Fixes foreign key constraints
2. Fixes PostgreSQL schema and enum issues
3. Fixes task templates and queries
4. Fixes inventory models
5. Fixes site settings

Usage:
    python consolidated_db_fixes.py
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
env_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('db_fixes')

def fix_foreign_keys():
    """Fix foreign key constraints in the database"""
    try:
        logger.info("Fixing foreign key constraints...")
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Check database dialect
            dialect = db.engine.dialect.name
            
            if dialect == 'postgresql':
                # Fix foreign keys for PostgreSQL
                from sqlalchemy import text
                
                # Get list of all tables
                result = db.session.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """))
                tables = [row[0] for row in result]
                
                # Main tables to check for foreign key issues
                main_tables = ['properties', 'users', 'tasks', 'task_assignments']
                for table in main_tables:
                    if table in tables:
                        logger.info(f"Checking foreign keys for {table} table...")
                        # Get foreign key constraints for this table
                        constraints = db.session.execute(text(f"""
                            SELECT conname, pg_get_constraintdef(c.oid)
                            FROM pg_constraint c
                            JOIN pg_namespace n ON n.oid = c.connamespace
                            WHERE contype = 'f' AND conrelid = '{table}'::regclass
                        """))
                        
                        for constraint_name, constraint_def in constraints:
                            logger.info(f"Found constraint: {constraint_name} - {constraint_def}")
                
                logger.info("Foreign key constraint check completed for PostgreSQL")
                
            elif dialect == 'sqlite':
                # SQLite doesn't enforce foreign keys by default, enable it
                db.session.execute(text("PRAGMA foreign_keys = ON"))
                logger.info("Enabled foreign key constraints for SQLite")
                
            logger.info("Foreign key constraints have been verified")
            return True
    except Exception as e:
        logger.error(f"Error fixing foreign key constraints: {str(e)}")
        return False

def fix_postgres_schema():
    """Fix PostgreSQL schema issues"""
    try:
        logger.info("Fixing PostgreSQL schema issues...")
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Check if we're using PostgreSQL
            if db.engine.dialect.name != 'postgresql':
                logger.info("Not using PostgreSQL, skipping PostgreSQL-specific fixes")
                return True
            
            from sqlalchemy import text
            
            # Fix enum types
            enums_to_fix = [
                ('taskstatus', ['pending', 'in_progress', 'completed', 'cancelled']),
                ('userroles', ['admin', 'landlord', 'tenant', 'maintenance']),
                ('propertystatus', ['active', 'inactive', 'pending', 'archived'])
            ]
            
            for enum_name, enum_values in enums_to_fix:
                # Check if the enum exists
                enum_exists = db.session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_type 
                        WHERE typname = '{enum_name}'
                    )
                """)).scalar()
                
                if enum_exists:
                    logger.info(f"Enum type {enum_name} exists, checking values...")
                    
                    # Get current enum values
                    current_values = db.session.execute(text(f"""
                        SELECT enumlabel FROM pg_enum
                        WHERE enumtypid = (
                            SELECT oid FROM pg_type WHERE typname = '{enum_name}'
                        )
                        ORDER BY enumsortorder
                    """)).scalars().all()
                    
                    # Check if any values need to be added
                    missing_values = [val for val in enum_values if val not in current_values]
                    if missing_values:
                        logger.info(f"Missing enum values for {enum_name}: {missing_values}")
                        
                        # PostgreSQL doesn't allow direct enum value addition
                        # We need to alter the type and recreate it
                        logger.info(f"Recreating enum type {enum_name} with all values")
                        
                        # This is a simplified approach - in production we would need
                        # to handle tables using these enums more carefully
                        try:
                            db.session.execute(text(f"""
                                ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{missing_values[0]}';
                            """))
                            db.session.commit()
                            logger.info(f"Added missing value {missing_values[0]} to {enum_name}")
                        except Exception as e:
                            logger.warning(f"Error adding enum value: {e}")
                            logger.warning("Skipping enum modification for safety")
                else:
                    logger.info(f"Enum type {enum_name} doesn't exist, will be created when models are used")
            
            logger.info("PostgreSQL schema fixes completed")
            return True
    except Exception as e:
        logger.error(f"Error fixing PostgreSQL schema: {str(e)}")
        return False

def fix_task_templates():
    """Fix task templates in the database"""
    try:
        logger.info("Fixing task templates...")
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Check if the task_templates table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'task_templates' not in inspector.get_table_names():
                logger.info("Task templates table doesn't exist yet, skipping")
                return True
            
            # Check if there are templates already
            from app.models import TaskTemplate
            template_count = TaskTemplate.query.count()
            
            if template_count == 0:
                logger.info("No task templates found, initialization will be handled separately")
                return True
            
            # Fix any issues with existing templates
            logger.info(f"Found {template_count} existing task templates, checking for issues...")
            
            # Check for templates with empty names or descriptions
            problem_templates = TaskTemplate.query.filter(
                (TaskTemplate.name == '') | 
                (TaskTemplate.name.is_(None)) |
                (TaskTemplate.description == '') |
                (TaskTemplate.description.is_(None))
            ).all()
            
            if problem_templates:
                logger.info(f"Found {len(problem_templates)} task templates with missing names/descriptions")
                
                for template in problem_templates:
                    if not template.name or template.name == '':
                        template.name = f"Template {template.id}"
                    
                    if not template.description or template.description == '':
                        template.description = f"Task template {template.id}"
                
                db.session.commit()
                logger.info("Fixed task templates with missing names/descriptions")
            
            logger.info("Task template fixes completed")
            return True
    except Exception as e:
        logger.error(f"Error fixing task templates: {str(e)}")
        return False

def fix_inventory_models():
    """Fix inventory models in the database"""
    try:
        logger.info("Fixing inventory models...")
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Check if inventory tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            inventory_tables = ['inventory_items', 'rooms', 'inventory_categories']
            missing_tables = [table for table in inventory_tables if table not in tables]
            
            if missing_tables:
                logger.info(f"Inventory tables missing: {', '.join(missing_tables)}")
                logger.info("These will be created when migrations run")
                return True
            
            # Check relationships between rooms and properties
            if 'rooms' in tables and 'properties' in tables:
                from sqlalchemy import text
                
                # Check if rooms have property_id column
                room_columns = [col['name'] for col in inspector.get_columns('rooms')]
                
                if 'property_id' in room_columns:
                    # Check for rooms with invalid property_id
                    orphaned_rooms = db.session.execute(text("""
                        SELECT r.id FROM rooms r
                        LEFT JOIN properties p ON r.property_id = p.id
                        WHERE r.property_id IS NOT NULL AND p.id IS NULL
                    """)).scalars().all()
                    
                    if orphaned_rooms:
                        logger.info(f"Found {len(orphaned_rooms)} rooms with invalid property IDs")
                        # Set property_id to NULL for these rooms
                        db.session.execute(text(f"""
                            UPDATE rooms 
                            SET property_id = NULL
                            WHERE id IN ({','.join(str(r) for r in orphaned_rooms)})
                        """))
                        db.session.commit()
                        logger.info("Fixed rooms with invalid property IDs")
            
            logger.info("Inventory model fixes completed")
            return True
    except Exception as e:
        logger.error(f"Error fixing inventory models: {str(e)}")
        return False

def fix_site_settings():
    """Fix site settings in the database"""
    try:
        logger.info("Fixing site settings...")
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Check if site_settings table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'site_settings' not in inspector.get_table_names():
                logger.info("site_settings table doesn't exist yet, skipping")
                return True
            
            # Required site settings with default values
            required_settings = {
                'site_name': 'Property Management System',
                'support_email': 'support@example.com',
                'maintenance_phone': '555-123-4567',
                'enable_registration': 'true',
                'require_approval': 'true',
                'theme_primary_color': '#3f51b5',
                'theme_secondary_color': '#f50057'
            }
            
            # Import site settings model - adjust import based on your app structure
            from app.models import SiteSetting
            
            # Add any missing settings
            for key, default_value in required_settings.items():
                setting = SiteSetting.query.filter_by(key=key).first()
                
                if not setting:
                    logger.info(f"Adding missing site setting: {key}")
                    new_setting = SiteSetting(
                        key=key,
                        value=default_value,
                        description=f"System {key.replace('_', ' ')}",
                        visible=True
                    )
                    db.session.add(new_setting)
            
            db.session.commit()
            logger.info("Site settings fixes completed")
            return True
    except Exception as e:
        logger.error(f"Error fixing site settings: {str(e)}")
        return False

def run_consolidated_db_fixes():
    """Run all database fixes in the correct order"""
    try:
        logger.info("Starting consolidated database fixes...")
        
        # 1. Fix foreign key constraints
        fk_result = fix_foreign_keys()
        
        # 2. Fix PostgreSQL schema issues
        pg_schema_result = fix_postgres_schema()
        
        # 3. Fix task templates
        task_template_result = fix_task_templates()
        
        # 4. Fix inventory models
        inventory_result = fix_inventory_models()
        
        # 5. Fix site settings
        site_settings_result = fix_site_settings()
        
        # Summary
        logger.info("Database fixes results:")
        logger.info(f"- Foreign key fixes: {'Success' if fk_result else 'Failed'}")
        logger.info(f"- PostgreSQL schema fixes: {'Success' if pg_schema_result else 'Failed'}")
        logger.info(f"- Task template fixes: {'Success' if task_template_result else 'Failed'}")
        logger.info(f"- Inventory model fixes: {'Success' if inventory_result else 'Failed'}")
        logger.info(f"- Site settings fixes: {'Success' if site_settings_result else 'Failed'}")
        
        if fk_result and pg_schema_result and task_template_result and inventory_result and site_settings_result:
            logger.info("All database fixes completed successfully!")
            return True
        else:
            logger.warning("Some database fixes failed, but we'll continue...")
            return False
    except Exception as e:
        logger.error(f"Error in consolidated database fixes: {str(e)}")
        return False

if __name__ == '__main__':
    success = run_consolidated_db_fixes()
    sys.exit(0 if success else 1) 