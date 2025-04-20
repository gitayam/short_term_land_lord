#!/usr/bin/env python
"""
Fix for the InventoryCatalogItem model to use the correct foreign key target.
This script patches the model to use the correct user table name in foreign keys.
"""
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(parent_dir))

from app import create_app, db
from sqlalchemy import inspect, text
from app.user_model_fix import get_user_fk_target, get_user_table_name

def fix_inventory_models():
    """
    Fix the InventoryCatalogItem model to use the correct foreign key target
    based on the database dialect.
    """
    print("Fixing InventoryCatalogItem model foreign keys...")
    
    # Get the database dialect and correct foreign key target
    dialect = db.engine.dialect.name
    fk_target = get_user_fk_target()
    table_name = get_user_table_name()
    print(f"Detected database dialect: {dialect}")
    print(f"Using FK target: {fk_target}")
    print(f"Using table name: {table_name}")
    
    # Import the models
    from app.models import InventoryCatalogItem, User
    
    # First ensure User model has correct table name
    if User.__tablename__ != table_name:
        print(f"Updating User.__tablename__ from {User.__tablename__} to {table_name}")
        User.__tablename__ = table_name
    
    # Create a deeper fix that removes and recreates the relationship and foreign key at runtime
    try:
        # Store the original creator relationship if it exists
        creator_rel = None
        if hasattr(InventoryCatalogItem, 'creator'):
            creator_rel = getattr(InventoryCatalogItem, 'creator')
            print(f"Found existing creator relationship: {creator_rel}")
            
            # Remove the relationship attribute
            delattr(InventoryCatalogItem, 'creator')
            print("Removed existing creator relationship")
        
        # Clear and rebuild SQLAlchemy's model registry cache
        db.Model.metadata.clear()
        
        # Redefine the relationship using class attribute assignment
        from sqlalchemy.orm import relationship
        from sqlalchemy import Column, Integer, ForeignKey
        
        # Replace the creator_id column with the correct FK
        # First, find the existing column
        if hasattr(InventoryCatalogItem, 'creator_id'):
            # Save column definition parameters
            col = getattr(InventoryCatalogItem, 'creator_id')
            print(f"Found existing creator_id column: {col}")
            
            # Remove the column attribute
            delattr(InventoryCatalogItem, 'creator_id')
            print("Removed existing creator_id column")
            
            # Add the column back with correct FK
            setattr(InventoryCatalogItem, 'creator_id', 
                    Column('creator_id', Integer, ForeignKey(fk_target), nullable=False))
            print(f"Added creator_id column with FK: {fk_target}")
        
        # Add the relationship back
        setattr(InventoryCatalogItem, 'creator', 
                relationship('User', foreign_keys=[InventoryCatalogItem.creator_id], 
                            backref='created_catalog_items'))
        print("Added creator relationship")
        
        # Now let's clear everything and let SQLAlchemy rebuild
        db.Model.metadata.clear()
        
        print("Inventory models fixed successfully!")
        return True
    except Exception as e:
        print(f"Error fixing inventory models: {e}")
        return False

def test_inventory_model():
    """Test if the InventoryCatalogItem model works correctly"""
    try:
        from app.models import InventoryCatalogItem
        
        # Test query
        count = InventoryCatalogItem.query.count()
        print(f"Successfully queried InventoryCatalogItem - found {count} items")
        return True
    except Exception as e:
        print(f"Error testing InventoryCatalogItem model: {e}")
        return False

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Apply model fix
        if fix_inventory_models():
            # Test if it worked
            test_inventory_model() 