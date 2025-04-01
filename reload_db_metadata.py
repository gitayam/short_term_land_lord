#!/usr/bin/env python
"""
Reload SQLAlchemy metadata and regenerate mapped classes to recognize new columns
"""
import sys
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.ext.declarative import declarative_base

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from app.models import User, UserRoles

def reload_metadata():
    """Reload SQLAlchemy metadata to recognize new columns"""
    print("Reloading SQLAlchemy metadata...")
    
    # Get current model attributes before refresh
    print("Current User model columns:")
    inspector = inspect(User)
    for column in inspector.columns:
        print(f"  - {column.name}: {column.type}")
    
    try:
        # Explicitly reflect the user table
        print("\nReflecting user table directly from database:")
        metadata = MetaData()
        user_table = Table('user', metadata, autoload_with=db.engine)
        
        print("Reflected columns:")
        for column in user_table.columns:
            print(f"  - {column.name}: {column.type}")
        
        # Try to create a new, reflective model to test if this works
        Base = declarative_base()
        
        class ReflectedUser(Base):
            __table__ = user_table
        
        print("\nTesting query with reflected model...")
        # This query should work with the reflected model
        with db.session() as session:
            stmt = sa.select(ReflectedUser).limit(1)
            try:
                result = session.execute(stmt).all()
                print(f"Successfully queried {len(result)} users with reflected model")
                for row in result:
                    user = row[0]
                    print(f"User details: {user.id}, {user.email}")
                    # Try to access the new columns
                    print(f"Username: {getattr(user, 'username', 'N/A')}")
                    print(f"Is Admin: {getattr(user, 'is_admin', 'N/A')}")
                    print(f"Is Active: {getattr(user, 'is_active', 'N/A')}")
            except Exception as e:
                print(f"Error querying with reflected model: {e}")
        
        print("\nChecking if SQLAlchemy can now see all columns...")
        inspector = inspect(db.engine)
        columns = inspector.get_columns('user')
        print(f"SQLAlchemy now sees {len(columns)} columns in user table: {[col['name'] for col in columns]}")
        
    except Exception as e:
        print(f"Error during metadata reload: {e}")
    
    print("\nMetadata reload complete!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        reload_metadata() 