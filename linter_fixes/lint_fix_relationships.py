#!/usr/bin/env python3
"""Fix relationship issues in models.py."""

import re

def fix_property_user_relationship(content):
    """Fix the relationship between Property and User models."""
    # Fix the properties relationship in User model
    user_properties_pattern = r'properties = db\.relationship\([^)]+\)'
    fixed_user_properties = '''    properties = db.relationship(
        'Property',
        foreign_keys='Property.owner_id',
        backref='owner',
        lazy='dynamic'
    )'''
    content = re.sub(user_properties_pattern, fixed_user_properties, content)

    # Fix the owner relationship in Property model
    property_owner_pattern = r'(\s+)owner = [^\n]+\n'
    fixed_property_owner = r'\1owner = db.relationship("User", foreign_keys=[owner_id], backref="owned_properties")\n'
    content = re.sub(property_owner_pattern, fixed_property_owner, content)

    # Remove overlaps arguments as they're no longer needed
    content = re.sub(r',\s*overlaps="[^"]+"', '', content)
    
    return content

def main():
    """Main function to fix relationship issues."""
    try:
        with open('app/models.py', 'r') as file:
            content = file.read()

        # Apply fixes
        modified_content = fix_property_user_relationship(content)

        # Write back to file
        with open('app/models.py', 'w') as file:
            file.write(modified_content)

        print("Successfully fixed relationship issues in models.py")

    except Exception as e:
        print(f"Error fixing relationship issues: {str(e)}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main()) 