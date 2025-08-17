#!/usr/bin/env python3
"""
Migration script from SQLite to PostgreSQL
Handles data migration for Short Term Landlord application
"""

import os
import sys
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SQLiteToPostgreSQLMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path, postgres_config):
        """
        Initialize migrator
        
        Args:
            sqlite_path: Path to SQLite database file
            postgres_config: PostgreSQL connection parameters dict
        """
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        self.sqlite_conn = None
        self.pg_conn = None
        
    def connect(self):
        """Establish database connections"""
        try:
            # Connect to SQLite
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Connected to SQLite database: {self.sqlite_path}")
            
            # Connect to PostgreSQL
            self.pg_conn = psycopg2.connect(**self.postgres_config)
            logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()
    
    def get_table_order(self):
        """Return tables in dependency order for migration"""
        return [
            # Core tables first
            'users',
            'property',
            
            # Dependent tables
            'property_calendar',
            'calendar_events',
            'room',
            'room_furniture',
            'task',
            'task_property',
            'task_assignment',
            'task_template',
            'cleaning_session',
            'repair_request',
            'inventory_item',
            'inventory_transaction',
            'invoice',
            'invoice_item',
            'service_price',
            'message_thread',
            'message',
            'notification',
            'password_reset',
            'registration_request',
            'guide_book',
            'guide_book_entry',
            'recommendation',
            'guest_review',
            'property_image',
            'task_media',
            'sms_message',
            'sms_conversation',
        ]
    
    def migrate_table(self, table_name):
        """
        Migrate a single table from SQLite to PostgreSQL
        
        Args:
            table_name: Name of table to migrate
        """
        try:
            cursor_sqlite = self.sqlite_conn.cursor()
            cursor_pg = self.pg_conn.cursor()
            
            # Get data from SQLite
            cursor_sqlite.execute(f"SELECT * FROM {table_name}")
            rows = cursor_sqlite.fetchall()
            
            if not rows:
                logger.info(f"No data in table {table_name}")
                return 0
            
            # Get column names
            columns = [description[0] for description in cursor_sqlite.description]
            
            # Prepare PostgreSQL insert
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'"{col}"' for col in columns])
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Insert data into PostgreSQL
            count = 0
            for row in rows:
                try:
                    # Convert SQLite row to tuple
                    values = tuple(row)
                    
                    # Handle special data types
                    processed_values = []
                    for i, value in enumerate(values):
                        col_name = columns[i]
                        
                        # Convert SQLite boolean (0/1) to PostgreSQL boolean
                        if value in (0, 1) and 'is_' in col_name:
                            processed_values.append(bool(value))
                        # Handle datetime strings
                        elif isinstance(value, str) and 'created_at' in col_name or 'updated_at' in col_name:
                            try:
                                # Parse datetime and format for PostgreSQL
                                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                processed_values.append(dt)
                            except:
                                processed_values.append(value)
                        else:
                            processed_values.append(value)
                    
                    cursor_pg.execute(insert_query, processed_values)
                    count += 1
                    
                except psycopg2.IntegrityError as e:
                    logger.warning(f"Skipping duplicate row in {table_name}: {e}")
                    self.pg_conn.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error inserting row in {table_name}: {e}")
                    self.pg_conn.rollback()
                    continue
            
            self.pg_conn.commit()
            logger.info(f"Migrated {count} rows to {table_name}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            self.pg_conn.rollback()
            return 0
    
    def reset_sequences(self):
        """Reset PostgreSQL sequences after migration"""
        try:
            cursor = self.pg_conn.cursor()
            
            # Get all sequences
            cursor.execute("""
                SELECT sequence_name, table_name, column_name
                FROM information_schema.sequences
                JOIN information_schema.columns 
                ON columns.column_default LIKE '%' || sequence_name || '%'
                WHERE sequence_schema = 'public'
            """)
            
            sequences = cursor.fetchall()
            
            for seq_name, table_name, column_name in sequences:
                # Get max value from table
                cursor.execute(f"SELECT MAX({column_name}) FROM {table_name}")
                max_val = cursor.fetchone()[0]
                
                if max_val:
                    # Reset sequence
                    cursor.execute(f"SELECT setval('{seq_name}', {max_val})")
                    logger.info(f"Reset sequence {seq_name} to {max_val}")
            
            self.pg_conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to reset sequences: {e}")
            self.pg_conn.rollback()
    
    def migrate(self):
        """Execute full migration"""
        logger.info("Starting SQLite to PostgreSQL migration...")
        
        try:
            self.connect()
            
            # Get tables in order
            tables = self.get_table_order()
            
            # Check which tables exist
            cursor_sqlite = self.sqlite_conn.cursor()
            cursor_sqlite.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            existing_tables = [row[0] for row in cursor_sqlite.fetchall()]
            
            # Migrate each table
            total_rows = 0
            for table in tables:
                if table in existing_tables:
                    rows = self.migrate_table(table)
                    total_rows += rows
                else:
                    logger.info(f"Table {table} does not exist in SQLite, skipping")
            
            # Reset sequences
            self.reset_sequences()
            
            logger.info(f"Migration completed! Total rows migrated: {total_rows}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.disconnect()


def main():
    """Main migration function"""
    
    # Configuration
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', 'instance/app.db')
    
    # PostgreSQL configuration
    POSTGRES_CONFIG = {
        'host': os.environ.get('PG_HOST', '127.0.0.1'),  # Use IPv4 explicitly
        'port': os.environ.get('PG_PORT', 5432),
        'database': os.environ.get('PG_DATABASE', 'landlord_prod'),
        'user': os.environ.get('PG_USER', 'landlord'),
        'password': os.environ.get('PG_PASSWORD', 'password'),
    }
    
    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB_PATH):
        logger.error(f"SQLite database not found at {SQLITE_DB_PATH}")
        sys.exit(1)
    
    # Create migrator and run migration
    migrator = SQLiteToPostgreSQLMigrator(SQLITE_DB_PATH, POSTGRES_CONFIG)
    
    try:
        migrator.migrate()
        logger.info("✅ Migration successful!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()