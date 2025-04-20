"""
Migration script to add username column to User model.

This script checks the database type and adds the username column to the appropriate table
(users for PostgreSQL, user for SQLite) if it doesn't already exist.
"""

from flask import current_app
from app import db, create_app
from sqlalchemy import text, inspect

def add_username_column():
    """Add username column to User table if it doesn't exist."""
    app = create_app()
    with app.app_context():
        # Detect database dialect
        dialect = db.engine.dialect.name
        
        # Get the appropriate table name
        table_name = 'users' if dialect == 'postgresql' else 'user'
        
        # Check if username column already exists
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if 'username' not in columns:
            current_app.logger.info(f"Adding username column to {table_name} table")
            
            if dialect == 'postgresql':
                # PostgreSQL syntax
                sql = text(f"""
                ALTER TABLE {table_name} 
                ADD COLUMN username VARCHAR(64) UNIQUE;
                
                CREATE INDEX IF NOT EXISTS idx_{table_name}_username 
                ON {table_name} (username);
                """)
            else:
                # SQLite syntax
                sql = text(f"""
                ALTER TABLE {table_name} 
                ADD COLUMN username VARCHAR(64) UNIQUE;
                """)
                
            db.session.execute(sql)
            db.session.commit()
            
            # Generate usernames for existing users
            if dialect == 'postgresql':
                sql = text(f"""
                UPDATE {table_name}
                SET username = SUBSTRING(email FROM 1 FOR POSITION('@' IN email) - 1)
                WHERE username IS NULL;
                """)
            else:
                sql = text(f"""
                UPDATE {table_name}
                SET username = SUBSTR(email, 1, INSTR(email, '@') - 1)
                WHERE username IS NULL;
                """)
                
            db.session.execute(sql)
            db.session.commit()
            
            current_app.logger.info(f"Username column added to {table_name} table")
        else:
            current_app.logger.info(f"Username column already exists in {table_name} table")

if __name__ == '__main__':
    add_username_column()
