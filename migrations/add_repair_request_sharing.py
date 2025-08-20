#!/usr/bin/env python3
"""
Add repair request sharing functionality tables
"""

import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def add_sharing_tables():
    """Add tables for repair request sharing feature"""
    
    # Database connection parameters
    db_params = {
        'host': os.environ.get('DB_HOST', 'db'),
        'port': os.environ.get('DB_PORT', '5432'),
        'database': os.environ.get('DB_NAME', 'flask_app'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'postgres')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Creating repair request sharing tables...")
        
        # Create share type enum
        cur.execute("""
            DO $$ BEGIN
                CREATE TYPE share_type AS ENUM ('public', 'password');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Create repair_request_shares table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS repair_request_shares (
                id SERIAL PRIMARY KEY,
                repair_request_id INTEGER REFERENCES repair_request(id) ON DELETE CASCADE,
                task_id INTEGER REFERENCES task(id) ON DELETE CASCADE,
                share_token VARCHAR(255) UNIQUE NOT NULL,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                password_hash VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                view_count INTEGER DEFAULT 0,
                last_viewed_at TIMESTAMP,
                share_type share_type DEFAULT 'public',
                notes TEXT,
                CONSTRAINT valid_expiry CHECK (expires_at IS NULL OR expires_at > created_at),
                CONSTRAINT check_one_reference CHECK (
                    (repair_request_id IS NOT NULL AND task_id IS NULL) OR 
                    (repair_request_id IS NULL AND task_id IS NOT NULL)
                )
            );
        """)
        print("Created repair_request_shares table")
        
        # Create indexes for performance
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_share_token 
            ON repair_request_shares(share_token) 
            WHERE is_active = TRUE;
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_repair_request_shares 
            ON repair_request_shares(repair_request_id) 
            WHERE is_active = TRUE;
        """)
        
        # Create share_access_logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS share_access_logs (
                id SERIAL PRIMARY KEY,
                share_id INTEGER NOT NULL REFERENCES repair_request_shares(id) ON DELETE CASCADE,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT,
                access_granted BOOLEAN DEFAULT TRUE,
                failure_reason VARCHAR(100)
            );
        """)
        print("Created share_access_logs table")
        
        # Create index for access logs
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_share_access_logs 
            ON share_access_logs(share_id, accessed_at DESC);
        """)
        
        print("Sharing tables created successfully!")
        
        # Close connection
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_sharing_tables()