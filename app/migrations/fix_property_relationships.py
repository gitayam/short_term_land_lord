#!/usr/bin/env python3
"""Migration script to fix associated_property references.

This script updates the models.py file to use consistent relationship naming,
as well as in other models, ensuring all uses of associated_property are updated
to use property instead, which is the standardized relationship name.
"""

import re
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fix_models_file():
    """Remove all associated_property relationship definitions and update usages in models.py"""
    file_path = os.path.join(BASE_DIR, 'models.py')
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove the associated_property relationship from CleaningSession model
    content = re.sub(
        r"associated_property = db\.relationship\('Property', foreign_keys=\[property_id\], backref='cleaning_sessions'\)",
        r"property = db.relationship('Property', foreign_keys=[property_id], backref='cleaning_sessions')",
        content
    )
    
    # Remove the associated_property relationship from RepairRequest model
    content = re.sub(
        r"associated_property = db\.relationship\('Property', foreign_keys=\[property_id\], backref='repair_requests'\)",
        r"property = db.relationship('Property', foreign_keys=[property_id], backref='repair_requests')",
        content
    )
    
    # Remove the associated_property relationship from RecommendationBlock model
    content = re.sub(
        r"# Relationships - rename property to associated_property\s+# associated_property = db\.relationship\('Property', backref='recommendations'\)",
        r"# Relationships",
        content
    )
    
    # Remove the associated_property relationship from GuideBook model
    content = re.sub(
        r"# associated_property = db\.relationship\('Property', backref=db\.backref\('guide_books', lazy=True\)\)",
        r"",
        content
    )
    
    # Remove the commented out associated_property relationship from Booking model
    content = re.sub(
        r"# Relationships - REMOVE associated_property and property_bookings\s+# associated_property = db\.relationship\('Property', backref=db\.backref\('property_bookings', lazy=True\)\)",
        r"# Relationships",
        content
    )
    
    # Update CleaningSession.__repr__ to use property instead of associated_property
    content = re.sub(
        r"return f'<CleaningSession \{self\.id\}: \{self\.associated_property\.name\} on \{self\.cleaning_date\}>'",
        r"return f'<CleaningSession {self.id}: {self.property.name} on {self.cleaning_date}>'",
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated models.py")

def fix_recommendation_routes():
    """Fix references to associated_property in recommendation_routes.py"""
    file_path = os.path.join(BASE_DIR, 'routes', 'recommendation_routes.py')
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace associated_property with property
    content = content.replace("guide_book.associated_property", "guide_book.property")
    content = content.replace("recommendation.associated_property", "recommendation.property")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated recommendation_routes.py")

def fix_property_routes():
    """Fix references to associated_property in property_routes.py"""
    file_path = os.path.join(BASE_DIR, 'routes', 'property_routes.py')
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace associated_property with property
    content = content.replace("recommendation.associated_property", "recommendation.property")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated property_routes.py")

def fix_notifications_service():
    """Fix references to associated_property in notifications/service.py"""
    file_path = os.path.join(BASE_DIR, 'notifications', 'service.py')
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace associated_property with property
    content = content.replace("repair_request.associated_property", "repair_request.property")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated notifications/service.py")

def fix_tasks_routes():
    """Fix references to associated_property in tasks/routes.py"""
    file_path = os.path.join(BASE_DIR, 'tasks', 'routes.py')
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace associated_property with property
    content = content.replace("session.associated_property", "session.property")
    content = content.replace("repair_request.associated_property", "repair_request.property")
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated tasks/routes.py")

def fix_templates():
    """Fix references to associated_property in templates"""
    template_files = [
        os.path.join(BASE_DIR, 'templates', 'tasks', 'repair_request_edit.html'),
        os.path.join(BASE_DIR, 'templates', 'tasks', 'view_repair_request.html'),
        os.path.join(BASE_DIR, 'templates', 'tasks', 'feedback_form.html'),
        os.path.join(BASE_DIR, 'templates', 'tasks', 'cleaning_report.html'),
    ]
    
    for file_path in template_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Replace associated_property with property
            content = content.replace("repair_request.associated_property", "repair_request.property")
            content = content.replace("session.associated_property", "session.property")
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated {file_path}")
        except Exception as e:
            print(f"❌ Error updating {file_path}: {str(e)}")

def main():
    print("Starting property relationship migration...")
    try:
        fix_models_file()
        fix_recommendation_routes()
        fix_property_routes()
        fix_notifications_service()
        fix_tasks_routes()
        fix_templates()
        print("✅ Migration completed successfully!")
        print("Please restart your application and check logs for any errors.")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 