#!/usr/bin/env python3
"""
Add recommendation_type column to recommendation_blocks table
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def add_recommendation_type_column():
    """Add the recommendation_type column to recommendation_blocks table"""
    app = create_app()
    
    with app.app_context():
        print("Adding recommendation_type column to recommendation_blocks table...")
        
        try:
            # Check if column already exists
            check_sql = """
            SELECT COUNT(*) as count 
            FROM pragma_table_info('recommendation_blocks') 
            WHERE name='recommendation_type';
            """
            result = db.session.execute(text(check_sql)).first()
            
            if result and result.count > 0:
                print("✓ Column recommendation_type already exists")
                return
            
            # Add the recommendation_type column with a default value
            alter_sql = """
            ALTER TABLE recommendation_blocks 
            ADD COLUMN recommendation_type VARCHAR(30) DEFAULT 'place';
            """
            
            db.session.execute(text(alter_sql))
            print("✓ Added recommendation_type column")
            
            # Update existing rows to have the default value
            update_sql = """
            UPDATE recommendation_blocks 
            SET recommendation_type = 'place' 
            WHERE recommendation_type IS NULL;
            """
            
            db.session.execute(text(update_sql))
            print("✓ Updated existing rows with default value")
            
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
    add_recommendation_type_column()