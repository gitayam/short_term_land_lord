#!/usr/bin/env python
"""
Database check script for short_term_land_lord project.
This script checks all the tables in the database and reports any issues.
"""
import os
import sys
from pathlib import Path
import sqlalchemy as sa

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.models import TaskStatus, GuestReviewRating, SiteSettings

def check_database():
    """Check database tables and structure"""
    print("Starting database check...")

    # Check database type (SQLite or PostgreSQL)
    db_uri = db.engine.url
    db_type = db_uri.drivername
    print(f"Detected database type: {db_type}")

    try:
        conn = db.engine.connect()

        # Get list of all tables
        if 'postgres' in db_type:
            result = conn.execute(sa.text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """))
        else:
            result = conn.execute(sa.text("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """))

        tables = [row[0] for row in result]
        print(f"Found {len(tables)} tables in the database:")
        for table in tables:
            print(f"  - {table}")

        # Check site_settings table
        if 'site_settings' in tables:
            result = conn.execute(sa.text("SELECT COUNT(*) FROM site_settings"))
            count = result.scalar()
            print(f"site_settings table has {count} rows")
        else:
            print("site_settings table NOT FOUND")

        # Check task table for status values
        if 'task' in tables:
            if 'postgres' in db_type:
                # PostgreSQL can list the enum values
                try:
                    result = conn.execute(sa.text("""
                    SELECT e.enumlabel
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'taskstatus'
                    """))

                    enum_values = [row[0] for row in result]
                    print(f"taskstatus enum values: {', '.join(enum_values)}")

                    # Compare with expected values
                    expected_values = [status.value for status in TaskStatus]
                    if set(enum_values) == set(expected_values):
                        print("✅ taskstatus enum values match the model definition")
                    else:
                        print("⚠️ taskstatus enum values do NOT match the model definition")
                        print(f"Expected: {', '.join(expected_values)}")
                except Exception as e:
                    print(f"Error checking taskstatus enum: {e}")

            # Check actual task status values in use
            result = conn.execute(sa.text("""
            SELECT status, COUNT(*)
            FROM task
            GROUP BY status
            ORDER BY status
            """))

            status_counts = {str(row[0]): row[1] for row in result}
            print(f"Task status counts: {status_counts}")
        else:
            print("task table NOT FOUND")

        # Check guest_review table for rating values
        if 'guest_review' in tables:
            if 'postgres' in db_type:
                # PostgreSQL can list the enum values
                try:
                    result = conn.execute(sa.text("""
                    SELECT e.enumlabel
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'guestreviewrating'
                    """))

                    enum_values = [row[0] for row in result]
                    print(f"guestreviewrating enum values: {', '.join(enum_values)}")

                    # Compare with expected values
                    expected_values = [rating.value for rating in GuestReviewRating]
                    if set(enum_values) == set(expected_values):
                        print("✅ guestreviewrating enum values match the model definition")
                    else:
                        print("⚠️ guestreviewrating enum values do NOT match the model definition")
                        print(f"Expected: {', '.join(expected_values)}")
                except Exception as e:
                    print(f"Error checking guestreviewrating enum: {e}")

            # Check actual guest review rating values in use
            result = conn.execute(sa.text("""
            SELECT rating, COUNT(*)
            FROM guest_review
            GROUP BY rating
            ORDER BY rating
            """))

            rating_counts = {str(row[0]): row[1] for row in result}
            print(f"Guest review rating counts: {rating_counts}")
        else:
            print("guest_review table NOT FOUND")

    except Exception as e:
        print(f"Error checking database: {e}")

    print("Database check complete!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_database()