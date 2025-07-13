#!/usr/bin/env python3
"""
Migration script to add guidebook tables and fix missing columns
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import GuidebookEntry, GuidebookCategory
from sqlalchemy import text

def run_migration():
    """Run the migration to add guidebook tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if guidebook_entries table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'guidebook_entries'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("Creating guidebook_entries table...")
                
                # Create the guidebook_entries table
                db.session.execute(text("""
                    CREATE TABLE guidebook_entries (
                        id SERIAL PRIMARY KEY,
                        property_id INTEGER NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        description TEXT NOT NULL,
                        category VARCHAR(50) NOT NULL,
                        address VARCHAR(500),
                        latitude DECIMAL(10, 8),
                        longitude DECIMAL(11, 8),
                        phone VARCHAR(20),
                        website VARCHAR(500),
                        hours VARCHAR(200),
                        price_range VARCHAR(50),
                        rating DECIMAL(3, 2),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (property_id) REFERENCES property(id) ON DELETE CASCADE
                    );
                """))
                
                # Create indexes
                db.session.execute(text("""
                    CREATE INDEX idx_guidebook_property ON guidebook_entries(property_id);
                    CREATE INDEX idx_guidebook_category ON guidebook_entries(category);
                    CREATE INDEX idx_guidebook_active ON guidebook_entries(is_active);
                """))
                
                print("✅ Guidebook tables created successfully!")
            else:
                print("✅ Guidebook tables already exist")
            
            # Fix missing is_active columns in other tables
            tables_to_check = [
                'users', 'property', 'task', 'task_assignment', 'task_property',
                'inventory_item', 'inventory_catalog_item', 'inventory_transaction',
                'site_settings', 'task_template'
            ]
            
            for table in tables_to_check:
                try:
                    # Check if is_active column exists
                    result = db.session.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = '{table}' AND column_name = 'is_active'
                        );
                    """))
                    column_exists = result.scalar()
                    
                    if not column_exists:
                        print(f"Adding is_active column to {table} table...")
                        db.session.execute(text(f"""
                            ALTER TABLE {table} ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                        """))
                        print(f"✅ Added is_active column to {table}")
                    else:
                        print(f"✅ is_active column already exists in {table}")
                        
                except Exception as e:
                    print(f"⚠️  Warning: Could not check/add is_active column for {table}: {e}")
            
            db.session.commit()
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    run_migration() 