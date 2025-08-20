#!/usr/bin/env python3
"""
Fix enum values in database to match Python enum definitions.
Converts lowercase enum values to uppercase.
"""

import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_enum_values():
    """Fix all enum values to be uppercase"""
    
    # Database connection parameters
    db_params = {
        'host': os.environ.get('DB_HOST', 'db'),  # Use 'db' as default for Docker
        'port': os.environ.get('DB_PORT', '5432'),  # Use internal port 5432
        'database': os.environ.get('DB_NAME', 'flask_app'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'postgres')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("Fixing enum values in database...")
        
        # Fix RecurrencePattern enum values
        updates = [
            ("UPDATE task SET recurrence_pattern = 'NONE' WHERE recurrence_pattern = 'none'", "RecurrencePattern"),
            ("UPDATE task SET recurrence_pattern = 'DAILY' WHERE recurrence_pattern = 'daily'", "RecurrencePattern"),
            ("UPDATE task SET recurrence_pattern = 'WEEKLY' WHERE recurrence_pattern = 'weekly'", "RecurrencePattern"),
            ("UPDATE task SET recurrence_pattern = 'MONTHLY' WHERE recurrence_pattern = 'monthly'", "RecurrencePattern"),
            ("UPDATE task SET recurrence_pattern = 'YEARLY' WHERE recurrence_pattern = 'yearly'", "RecurrencePattern"),
            ("UPDATE task SET recurrence_pattern = 'CUSTOM' WHERE recurrence_pattern = 'custom'", "RecurrencePattern"),
            
            # Fix TaskStatus enum values
            ("UPDATE task SET status = 'PENDING' WHERE status = 'pending'", "TaskStatus"),
            ("UPDATE task SET status = 'IN_PROGRESS' WHERE status = 'in_progress'", "TaskStatus"),
            ("UPDATE task SET status = 'COMPLETED' WHERE status = 'completed'", "TaskStatus"),
            
            # Fix TaskPriority enum values
            ("UPDATE task SET priority = 'LOW' WHERE priority = 'low'", "TaskPriority"),
            ("UPDATE task SET priority = 'MEDIUM' WHERE priority = 'medium'", "TaskPriority"),
            ("UPDATE task SET priority = 'HIGH' WHERE priority = 'high'", "TaskPriority"),
            ("UPDATE task SET priority = 'URGENT' WHERE priority = 'urgent'", "TaskPriority"),
        ]
        
        for query, enum_name in updates:
            try:
                cur.execute(query)
                rowcount = cur.rowcount
                if rowcount > 0:
                    print(f"  Fixed {rowcount} {enum_name} values")
            except psycopg2.Error as e:
                print(f"  Warning: Could not update {enum_name}: {e}")
        
        # Also ensure the enum types in PostgreSQL have the correct values
        # Add uppercase values if they don't exist
        enum_fixes = [
            ("recurrencepattern", ["NONE", "DAILY", "WEEKLY", "MONTHLY", "YEARLY", "CUSTOM"]),
            ("taskstatus", ["PENDING", "IN_PROGRESS", "COMPLETED"]),
            ("taskpriority", ["LOW", "MEDIUM", "HIGH", "URGENT"])
        ]
        
        for enum_name, values in enum_fixes:
            for value in values:
                try:
                    cur.execute(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'")
                except psycopg2.Error:
                    pass  # Value already exists or other error
        
        print("Enum values fixed successfully!")
        
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
    fix_enum_values()