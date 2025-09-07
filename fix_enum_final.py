#!/usr/bin/env python3

from app import create_app, db
from config import Config
from sqlalchemy import text

def fix_enum_final():
    app = create_app(Config)
    with app.app_context():
        try:
            # Create a new enum type with only the correct values
            db.session.execute(text("""
                CREATE TYPE servicetype_new AS ENUM (
                    'cleaning', 'handyman', 'lawn_care', 'pool_maintenance', 
                    'general_maintenance', 'other'
                );
            """))
            
            # Update all tables that use the enum
            tables_to_update = [
                'task_assignment',
                'task_template',
                'task_price',
                'invoice_item'
            ]
            
            for table in tables_to_update:
                try:
                    db.session.execute(text(f"""
                        ALTER TABLE {table} 
                        ALTER COLUMN service_type TYPE servicetype_new 
                        USING service_type::text::servicetype_new;
                    """))
                    print(f"Updated {table}")
                except Exception as e:
                    print(f"Could not update {table}: {e}")
            
            # Drop the old enum type and rename the new one
            db.session.execute(text("DROP TYPE servicetype;"))
            db.session.execute(text("ALTER TYPE servicetype_new RENAME TO servicetype;"))
            
            db.session.commit()
            print("Successfully recreated the enum type with correct values")
            
        except Exception as e:
            print(f"Error recreating enum: {e}")
            db.session.rollback()

if __name__ == '__main__':
    fix_enum_final() 