#!/usr/bin/env python
"""
Direct PostgreSQL enum fix script.
This script uses raw SQL to fix enum issues in PostgreSQL.
"""
import os
import sys
from pathlib import Path
import sqlalchemy as sa

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db

def fix_postgresql_enums():
    """Fix PostgreSQL enum issues directly"""
    print("Starting PostgreSQL enum fix...")
    
    # Check if we're using PostgreSQL
    db_uri = db.engine.url
    if 'postgres' not in db_uri.drivername:
        print(f"Not a PostgreSQL database ({db_uri.drivername}). No fixes needed.")
        return
    
    # Get raw connection
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()
        
        # Check if guestreviewrating enum exists
        cursor.execute("SELECT 1 FROM pg_type WHERE typname = 'guestreviewrating'")
        if cursor.fetchone():
            print("Found guestreviewrating enum, recreating it...")
            
            # Create a backup table
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS guest_review_backup AS SELECT * FROM guest_review")
                print("Created or verified guest_review_backup table")
            except Exception as e:
                print(f"Could not create backup table: {e}")
            
            # Try to drop the enum constraint and recreate it
            try:
                # Determine the constraint name
                cursor.execute("""
                SELECT conname
                FROM pg_constraint 
                WHERE conrelid = 'guest_review'::regclass 
                AND contype = 'c'
                AND conname LIKE '%rating%'
                """)
                
                result = cursor.fetchone()
                if result:
                    constraint_name = result[0]
                    print(f"Found constraint: {constraint_name}")
                    
                    # Drop the constraint
                    try:
                        cursor.execute(f"ALTER TABLE guest_review DROP CONSTRAINT {constraint_name}")
                        print("Dropped constraint")
                    except Exception as e:
                        print(f"Could not drop constraint (it may already be dropped): {e}")
                    
                    # Modify existing records
                    cursor.execute("""
                    UPDATE guest_review SET rating = 
                    CASE
                        WHEN UPPER(rating) = 'GOOD' THEN 'good'
                        WHEN UPPER(rating) = 'BAD' THEN 'bad'
                        WHEN UPPER(rating) = 'OK' THEN 'ok'
                        ELSE rating
                    END
                    """)
                    
                    # If necessary, try to drop and recreate the enum type
                    try:
                        # First check if any other tables use this enum
                        cursor.execute("""
                        SELECT c.relname AS table_name, a.attname AS column_name
                        FROM pg_attribute a
                        JOIN pg_class c ON a.attrelid = c.oid
                        JOIN pg_namespace n ON c.relnamespace = n.oid
                        JOIN pg_type t ON a.atttypid = t.oid
                        WHERE t.typname = 'guestreviewrating'
                        AND c.relkind = 'r'
                        AND n.nspname = 'public'
                        AND c.relname != 'guest_review'
                        """)
                        
                        other_tables = cursor.fetchall()
                        if not other_tables:
                            # Drop the column temporarily
                            try:
                                cursor.execute("ALTER TABLE guest_review DROP COLUMN rating")
                                print("Dropped rating column")
                            except Exception as e:
                                print(f"Could not drop rating column (it may already be dropped): {e}")
                            
                            # Drop the enum type
                            try:
                                cursor.execute("DROP TYPE IF EXISTS guestreviewrating")
                                print("Dropped guestreviewrating enum")
                            except Exception as e:
                                print(f"Could not drop enum type: {e}")
                            
                            # Recreate the enum type with lowercase values
                            try:
                                cursor.execute("CREATE TYPE guestreviewrating AS ENUM ('good', 'ok', 'bad')")
                                print("Recreated guestreviewrating enum")
                            except Exception as e:
                                print(f"Could not create enum type (it may already exist): {e}")
                            
                            # Add the column back
                            cursor.execute("ALTER TABLE guest_review ADD COLUMN rating guestreviewrating")
                            print("Added rating column back")
                            
                            # Restore data from backup if it exists
                            try:
                                cursor.execute("""
                                UPDATE guest_review g SET rating = 
                                CASE
                                    WHEN UPPER(b.rating) = 'GOOD' THEN 'good'::guestreviewrating
                                    WHEN UPPER(b.rating) = 'BAD' THEN 'bad'::guestreviewrating
                                    WHEN UPPER(b.rating) = 'OK' THEN 'ok'::guestreviewrating
                                    ELSE 'good'::guestreviewrating
                                END
                                FROM guest_review_backup b
                                WHERE g.id = b.id
                                """)
                                print("Restored data from backup")
                            except Exception as e:
                                print(f"Could not restore data: {e}")
                        else:
                            print(f"Cannot drop enum type as it's used by other tables: {other_tables}")
                    except Exception as e:
                        print(f"Error recreating enum: {e}")
                else:
                    print("Could not find constraint name for guest_review.rating")
            except Exception as e:
                print(f"Error updating guest_review: {e}")
        else:
            print("guestreviewrating enum not found, creating it...")
            try:
                cursor.execute("CREATE TYPE guestreviewrating AS ENUM ('good', 'ok', 'bad')")
                print("Created guestreviewrating enum")
            except Exception as e:
                print(f"Could not create enum: {e}")
        
        # Check if taskstatus enum exists
        cursor.execute("SELECT 1 FROM pg_type WHERE typname = 'taskstatus'")
        if cursor.fetchone():
            print("Found taskstatus enum, fixing it...")
            
            # Create a backup table
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS task_backup AS SELECT * FROM task")
                print("Created or verified task_backup table")
            except Exception as e:
                print(f"Could not create backup table: {e}")
            
            # Use the same approach as above to fix taskstatus
            try:
                # Determine the constraint name
                cursor.execute("""
                SELECT conname
                FROM pg_constraint 
                WHERE conrelid = 'task'::regclass 
                AND contype = 'c'
                AND conname LIKE '%status%'
                """)
                
                result = cursor.fetchone()
                if result:
                    constraint_name = result[0]
                    print(f"Found constraint: {constraint_name}")
                    
                    # Drop the constraint
                    try:
                        cursor.execute(f"ALTER TABLE task DROP CONSTRAINT {constraint_name}")
                        print("Dropped constraint")
                    except Exception as e:
                        print(f"Could not drop constraint (it may already be dropped): {e}")
                    
                    # Modify existing records
                    cursor.execute("""
                    UPDATE task SET status = 
                    CASE
                        WHEN UPPER(status) = 'PENDING' THEN 'pending'
                        WHEN UPPER(status) = 'IN_PROGRESS' THEN 'in_progress'
                        WHEN UPPER(status) = 'COMPLETED' THEN 'completed'
                        ELSE status
                    END
                    """)
                    
                    # If necessary, try to drop and recreate the enum type
                    try:
                        # First check if any other tables use this enum
                        cursor.execute("""
                        SELECT c.relname AS table_name, a.attname AS column_name
                        FROM pg_attribute a
                        JOIN pg_class c ON a.attrelid = c.oid
                        JOIN pg_namespace n ON c.relnamespace = n.oid
                        JOIN pg_type t ON a.atttypid = t.oid
                        WHERE t.typname = 'taskstatus'
                        AND c.relkind = 'r'
                        AND n.nspname = 'public'
                        AND c.relname != 'task'
                        """)
                        
                        other_tables = cursor.fetchall()
                        if not other_tables:
                            # Drop the column temporarily
                            try:
                                cursor.execute("ALTER TABLE task DROP COLUMN status")
                                print("Dropped status column")
                            except Exception as e:
                                print(f"Could not drop status column (it may already be dropped): {e}")
                            
                            # Drop the enum type
                            try:
                                cursor.execute("DROP TYPE IF EXISTS taskstatus")
                                print("Dropped taskstatus enum")
                            except Exception as e:
                                print(f"Could not drop enum type: {e}")
                            
                            # Recreate the enum type with lowercase values
                            try:
                                cursor.execute("CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'completed')")
                                print("Recreated taskstatus enum")
                            except Exception as e:
                                print(f"Could not create enum type (it may already exist): {e}")
                            
                            # Add the column back
                            cursor.execute("ALTER TABLE task ADD COLUMN status taskstatus")
                            print("Added status column back")
                            
                            # Restore data from backup if it exists
                            try:
                                cursor.execute("""
                                UPDATE task t SET status = 
                                CASE
                                    WHEN UPPER(b.status) = 'PENDING' THEN 'pending'::taskstatus
                                    WHEN UPPER(b.status) = 'IN_PROGRESS' THEN 'in_progress'::taskstatus
                                    WHEN UPPER(b.status) = 'COMPLETED' THEN 'completed'::taskstatus
                                    ELSE 'pending'::taskstatus
                                END
                                FROM task_backup b
                                WHERE t.id = b.id
                                """)
                                print("Restored data from backup")
                            except Exception as e:
                                print(f"Could not restore data: {e}")
                        else:
                            print(f"Cannot drop enum type as it's used by other tables: {other_tables}")
                    except Exception as e:
                        print(f"Error recreating enum: {e}")
                else:
                    print("Could not find constraint name for task.status")
            except Exception as e:
                print(f"Error updating task: {e}")
        else:
            print("taskstatus enum not found, creating it...")
            try:
                cursor.execute("CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'completed')")
                print("Created taskstatus enum")
            except Exception as e:
                print(f"Could not create enum: {e}")
                
        # Commit all changes
        conn.commit()
        print("Committed all changes")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("PostgreSQL enum fix complete!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        fix_postgresql_enums() 