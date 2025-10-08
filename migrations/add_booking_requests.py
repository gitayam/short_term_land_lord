#!/usr/bin/env python3
"""
Add booking requests and guest account request tables
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def add_booking_request_tables():
    """Add the booking_requests and guest_account_requests tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating booking request tables...")
        
        try:
            # Create booking_requests table
            create_booking_requests_sql = """
            CREATE TABLE IF NOT EXISTS booking_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                guest_name VARCHAR(255) NOT NULL,
                guest_email VARCHAR(255) NOT NULL,
                guest_phone VARCHAR(50),
                check_in_date DATE NOT NULL,
                check_out_date DATE NOT NULL,
                number_of_guests INTEGER DEFAULT 1 NOT NULL,
                previous_stay_property VARCHAR(255),
                previous_stay_dates VARCHAR(255),
                notes TEXT,
                special_requests TEXT,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                request_token VARCHAR(100) UNIQUE NOT NULL,
                user_id INTEGER,
                approved_by INTEGER,
                approved_at DATETIME,
                rejection_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                expires_at DATETIME,
                FOREIGN KEY (property_id) REFERENCES property(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            );
            """
            
            db.session.execute(text(create_booking_requests_sql))
            print("✓ Created booking_requests table")
            
            # Create guest_account_requests table
            create_guest_account_requests_sql = """
            CREATE TABLE IF NOT EXISTS guest_account_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(50),
                booking_request_id INTEGER,
                verification_token VARCHAR(100) UNIQUE NOT NULL,
                email_verified BOOLEAN DEFAULT 0 NOT NULL,
                is_approved BOOLEAN DEFAULT 0 NOT NULL,
                approved_by INTEGER,
                approved_at DATETIME,
                user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                FOREIGN KEY (booking_request_id) REFERENCES booking_requests(id),
                FOREIGN KEY (approved_by) REFERENCES users(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
            
            db.session.execute(text(create_guest_account_requests_sql))
            print("✓ Created guest_account_requests table")
            
            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_booking_requests_property_id ON booking_requests(property_id);",
                "CREATE INDEX IF NOT EXISTS idx_booking_requests_status ON booking_requests(status);",
                "CREATE INDEX IF NOT EXISTS idx_booking_requests_guest_email ON booking_requests(guest_email);",
                "CREATE INDEX IF NOT EXISTS idx_booking_requests_check_in_date ON booking_requests(check_in_date);",
                "CREATE INDEX IF NOT EXISTS idx_guest_account_requests_email ON guest_account_requests(email);",
                "CREATE INDEX IF NOT EXISTS idx_guest_account_requests_booking_id ON guest_account_requests(booking_request_id);"
            ]
            
            for index_sql in indexes:
                db.session.execute(text(index_sql))
            
            print("✓ Created database indexes")
            
            # Commit all changes
            db.session.commit()
            print("✓ Migration completed successfully")
            
        except Exception as e:
            print(f"✗ Error during migration: {e}")
            db.session.rollback()
            raise
            
        finally:
            db.session.close()

if __name__ == '__main__':
    add_booking_request_tables()