#!/usr/bin/env python3
"""
Run the repair_request migration to add missing fields.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from migrations.repair_request_add_fields import upgrade

app = create_app()
with app.app_context():
    print("Running repair_request migration...")
    upgrade()
    print("Migration completed successfully.") 