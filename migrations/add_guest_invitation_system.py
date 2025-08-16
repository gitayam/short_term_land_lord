#!/usr/bin/env python3
"""
Database migration: Add guest invitation system

This migration adds:
1. guest_invitations table for invitation codes
2. guest_bookings table for tracking guest bookings
3. Additional guest-related fields to users table

Usage:
    python migrations/add_guest_invitation_system.py
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from sqlalchemy import text

def run_migration():
    """Run the migration to add guest invitation system"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check current database structure
            print("Checking existing database structure...")
            
            with db.engine.connect() as conn:
                # Create guest_invitations table
                print("Creating guest_invitations table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS guest_invitations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code VARCHAR(24) UNIQUE NOT NULL,
                        property_id INTEGER,
                        created_by_id INTEGER NOT NULL,
                        email VARCHAR(120),
                        guest_name VARCHAR(200),
                        expires_at DATETIME NOT NULL,
                        used_at DATETIME,
                        used_by_id INTEGER,
                        is_active BOOLEAN DEFAULT 1 NOT NULL,
                        max_uses INTEGER DEFAULT 1 NOT NULL,
                        current_uses INTEGER DEFAULT 0 NOT NULL,
                        notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        FOREIGN KEY (property_id) REFERENCES property (id),
                        FOREIGN KEY (created_by_id) REFERENCES users (id),
                        FOREIGN KEY (used_by_id) REFERENCES users (id)
                    )
                """))
                
                # Create index on invitation code for fast lookups
                print("Creating index on guest_invitations.code...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_guest_invitations_code 
                    ON guest_invitations (code)
                """))
                
                # Create guest_bookings table
                print("Creating guest_bookings table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS guest_bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guest_user_id INTEGER NOT NULL,
                        property_id INTEGER NOT NULL,
                        check_in_date DATE NOT NULL,
                        check_out_date DATE NOT NULL,
                        guest_count INTEGER DEFAULT 1 NOT NULL,
                        booking_source VARCHAR(50) NOT NULL,
                        external_booking_id VARCHAR(100),
                        external_booking_url VARCHAR(500),
                        total_amount DECIMAL(10, 2),
                        currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
                        status VARCHAR(20) DEFAULT 'confirmed' NOT NULL,
                        confirmation_code VARCHAR(50),
                        special_requests TEXT,
                        host_notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        FOREIGN KEY (guest_user_id) REFERENCES users (id),
                        FOREIGN KEY (property_id) REFERENCES property (id)
                    )
                """))
                
                # Check if guest fields already exist in users table
                print("Checking users table structure...")
                result = conn.execute(text("PRAGMA table_info(users)"))
                existing_columns = [row[1] for row in result.fetchall()]
                
                # Add guest-specific fields to users table
                guest_fields = [
                    ("invitation_code_id", "INTEGER"),
                    ("guest_preferences", "TEXT"),
                    ("last_check_in", "DATETIME"),
                    ("guest_rating", "REAL"),
                    ("guest_notes", "TEXT"),
                    ("marketing_emails_consent", "BOOLEAN DEFAULT 0 NOT NULL"),
                    ("booking_reminders_consent", "BOOLEAN DEFAULT 1 NOT NULL"),
                    ("email_verified", "BOOLEAN DEFAULT 0 NOT NULL"),
                    ("email_verification_token", "VARCHAR(64)"),
                    ("email_verification_sent_at", "DATETIME")
                ]
                
                for field_name, field_type in guest_fields:
                    if field_name not in existing_columns:
                        print(f"Adding {field_name} column to users table...")
                        conn.execute(text(f"""
                            ALTER TABLE users ADD COLUMN {field_name} {field_type}
                        """))
                    else:
                        print(f"Column {field_name} already exists in users table.")
                
                # Add foreign key constraint for invitation_code_id (SQLite limitation workaround)
                print("Note: Foreign key constraint for invitation_code_id will be enforced at application level.")
                
                # Create indexes for performance
                print("Creating performance indexes...")
                
                # Index for guest bookings by user
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_guest_bookings_user 
                    ON guest_bookings (guest_user_id)
                """))
                
                # Index for guest bookings by property
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_guest_bookings_property 
                    ON guest_bookings (property_id)
                """))
                
                # Index for guest bookings by date range
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_guest_bookings_dates 
                    ON guest_bookings (check_in_date, check_out_date)
                """))
                
                # Index for invitation expiration cleanup
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_guest_invitations_expires 
                    ON guest_invitations (expires_at, is_active)
                """))
                
                # Commit the transaction
                conn.commit()
            
            print("Migration completed successfully!")
            print("")
            print("Summary of changes:")
            print("✓ Created guest_invitations table")
            print("✓ Created guest_bookings table") 
            print("✓ Added guest-specific fields to users table")
            print("✓ Created performance indexes")
            print("")
            print("The guest invitation system is now ready!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    print("Starting guest invitation system migration...")
    success = run_migration()
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)