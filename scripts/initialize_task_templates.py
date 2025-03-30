#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db
from app.models import TaskTemplate, User, UserRoles

def create_cleaning_task_templates():
    """Create the initial cleaning task templates"""
    print("Creating cleaning task templates...")
    
    # Find or create an admin user
    admin = User.query.filter_by(role=UserRoles.ADMIN).first()
    if not admin:
        print("No admin user found. Creating a temporary admin...")
        admin = User(
            first_name="System",
            last_name="Admin",
            email="admin@example.com",
            role=UserRoles.ADMIN
        )
        db.session.add(admin)
        db.session.commit()
    
    # Check if templates already exist
    existing_count = TaskTemplate.query.filter_by(is_global=True).count()
    if existing_count > 0:
        print(f"Found {existing_count} existing global templates. Skipping creation.")
        return
    
    # Create the templates
    templates = [
        {
            "title": "Initial Video Walkthrough",
            "description": "Record a video of the entire property to document current condition, noting damages and areas needing extra attention.",
            "category": "cleaning",
            "sequence_number": 1
        },
        {
            "title": "Linen Management",
            "description": "Remove all used bed linens, towels, and other washable items and send them for laundry immediately since washing/drying takes time.",
            "category": "cleaning",
            "sequence_number": 2
        },
        {
            "title": "Pre-Treatment in Bathrooms",
            "description": "Apply cleaning solutions (especially liquids that require dwell time) to toilets, sinks, showers, and bathtubs. Let them set to break down grime.",
            "category": "cleaning",
            "sequence_number": 3
        },
        {
            "title": "Kitchen Cleaning",
            "description": "While bathrooms are working, empty the dishwasher, clean countertops, appliances, and sink, and replace trash liners.",
            "category": "cleaning",
            "sequence_number": 4
        },
        {
            "title": "Living & Dining Areas",
            "description": "Dust all surfaces, vacuum or sweep floors, mop if needed, and arrange furniture per staging guidelines.",
            "category": "cleaning",
            "sequence_number": 5
        },
        {
            "title": "Finalize Bathroom Cleaning",
            "description": "Once dwell time is complete, scrub and rinse all surfaces, clean mirrors and glass, replace used towels, and restock toiletries.",
            "category": "cleaning",
            "sequence_number": 6
        },
        {
            "title": "Bedrooms",
            "description": "Dust furniture, clean windows, vacuum floors (including under beds), and make beds with fresh linens (once laundry is finished).",
            "category": "cleaning",
            "sequence_number": 7
        },
        {
            "title": "Laundry Room/Utility Areas",
            "description": "Clean and tidy these areas; ensure the washer and dryer are free of lint and restock any necessary supplies.",
            "category": "cleaning",
            "sequence_number": 8
        },
        {
            "title": "Outdoor Spaces",
            "description": "Sweep patios, decks, and entryways, clean outdoor furniture, and remove any debris.",
            "category": "cleaning",
            "sequence_number": 9
        },
        {
            "title": "Restocking Supplies",
            "description": "Replenish essential items throughout the property (toilet paper, paper towels, soaps, etc.).",
            "category": "cleaning",
            "sequence_number": 10
        },
        {
            "title": "Final Inspection & Staging",
            "description": "Conduct a thorough walkthrough to ensure every task is completed and the property is perfectly staged.",
            "category": "cleaning",
            "sequence_number": 11
        },
        {
            "title": "Final Video Walkthrough",
            "description": "Record a concluding video documenting the clean and prepared state, confirming quality for incoming guests.",
            "category": "cleaning",
            "sequence_number": 12
        }
    ]
    
    for template_data in templates:
        template = TaskTemplate(
            title=template_data["title"],
            description=template_data["description"],
            category=template_data["category"],
            sequence_number=template_data["sequence_number"],
            is_global=True,
            creator_id=admin.id
        )
        db.session.add(template)
    
    db.session.commit()
    print(f"Created {len(templates)} task templates.")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        create_cleaning_task_templates() 