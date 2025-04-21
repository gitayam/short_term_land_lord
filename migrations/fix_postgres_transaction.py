#!/usr/bin/env python3
"""
This script resets any aborted PostgreSQL transactions and verifies database schema integrity.
It can be run on app startup to ensure clean transactions.
"""

import os
import sys
from sqlalchemy import text
from flask import Flask

def fix_postgres_transactions():
    """Reset any aborted PostgreSQL transactions and verify database schema"""
    # Create a minimal Flask app
    app = Flask(__name__)

    # Configure the app
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    from app import db
    db.init_app(app)

    # Only proceed for PostgreSQL
    if not database_url.startswith('postgresql'):
        print("This fix script is only for PostgreSQL databases. Exiting.")
        return False

    with app.app_context():
        try:
            # Create a new connection with autocommit to reset any aborted transactions
            with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                print("Starting to fix PostgreSQL database issues...")

                # First, kill all existing connections that might be in an aborted state
                print("Checking for problematic database connections...")

                # Find connections in an aborted state
                result = conn.execute(text("""
                    SELECT pid, usename, query, state, backend_xmin, backend_xid
                    FROM pg_stat_activity
                    WHERE state = 'idle in transaction' OR state = 'idle in transaction (aborted)'
                """))

                transactions = result.fetchall()

                if transactions:
                    print(f"Found {len(transactions)} problematic transactions. Terminating them...")
                    for tx in transactions:
                        try:
                            # Force terminate the connections
                            print(f"Terminating connection {tx.pid} in state {tx.state}")
                            conn.execute(text(f"SELECT pg_terminate_backend({tx.pid})"))
                        except Exception as e:
                            print(f"Error terminating connection {tx.pid}: {e}")
                else:
                    print("No problematic transactions found.")

                # Check for any transaction locks
                print("Checking for transaction locks...")
                result = conn.execute(text("""
                    SELECT blocked_locks.pid AS blocked_pid,
                           blocked_activity.usename AS blocked_user,
                           blocking_locks.pid AS blocking_pid,
                           blocking_activity.usename AS blocking_user,
                           blocked_activity.query AS blocked_statement,
                           blocking_activity.query AS blocking_statement
                    FROM pg_catalog.pg_locks blocked_locks
                    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                    JOIN pg_catalog.pg_locks blocking_locks
                        ON blocking_locks.locktype = blocked_locks.locktype
                        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                        AND blocking_locks.pid != blocked_locks.pid
                    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                    WHERE NOT blocked_locks.granted;
                """))

                locks = result.fetchall()
                if locks:
                    print(f"Found {len(locks)} locked transactions. Attempting to terminate blockers...")
                    for lock in locks:
                        try:
                            print(f"Terminating blocker PID: {lock.blocking_pid} (blocking user {lock.blocking_user})")
                            conn.execute(text(f"SELECT pg_terminate_backend({lock.blocking_pid})"))
                        except Exception as e:
                            print(f"Error terminating blocker: {e}")
                else:
                    print("No transaction locks found.")

                # Verify that users table exists and has the right structure
                print("Verifying users table structure...")
                # Check if users table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'users'
                    )
                """))
                if result.scalar():
                    print("Users table found. Checking columns...")

                    # Get column information
                    result = conn.execute(text("""
                        SELECT column_name, data_type, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = 'users'
                        ORDER BY ordinal_position
                    """))

                    columns = {col.column_name: {"type": col.data_type, "length": col.character_maximum_length}
                              for col in result.fetchall()}

                    print(f"Found columns: {', '.join(columns.keys())}")

                    # Check for missing columns or incorrect types
                    required_columns = {
                        "id": {"type": "integer"},
                        "username": {"type": "character varying"},
                        "email": {"type": "character varying"},
                        "password_hash": {"type": "character varying", "min_length": 256},
                        "first_name": {"type": "character varying"},
                        "last_name": {"type": "character varying"},
                        "role": {"type": "character varying"},
                        "is_admin": {"type": "boolean"}
                    }

                    missing_columns = []
                    for col_name, col_props in required_columns.items():
                        if col_name not in columns:
                            missing_columns.append(col_name)
                        elif col_props.get("type") and col_props["type"] != columns[col_name]["type"]:
                            print(f"Column {col_name} has incorrect type: {columns[col_name]['type']} (should be {col_props['type']})")
                        elif col_props.get("min_length") and (not columns[col_name]["length"] or columns[col_name]["length"] < col_props["min_length"]):
                            print(f"Column {col_name} has insufficient length: {columns[col_name]['length']} (should be at least {col_props['min_length']})")

                            # Fix password_hash column length if needed
                            if col_name == "password_hash" and columns[col_name]["length"] < 256:
                                print("Fixing password_hash column length...")
                                conn.execute(text("""
                                    ALTER TABLE users ALTER COLUMN password_hash TYPE VARCHAR(256)
                                """))
                                print("Fixed password_hash column length.")

                    if missing_columns:
                        print(f"Missing columns in users table: {', '.join(missing_columns)}")
                else:
                    print("Users table not found!")

                print("Database verification and cleanup completed.")
                return True

        except Exception as e:
            print(f"Error fixing PostgreSQL transactions: {e}")
            return False

if __name__ == "__main__":
    fix_postgres_transactions()