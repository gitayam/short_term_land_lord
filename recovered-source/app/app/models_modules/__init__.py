# This file makes the models directory a proper Python package
# Import and re-export classes from the main models.py file

import sys
import os
from pathlib import Path

# Add parent directory to path to resolve import
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import all classes from models.py
from app.models import *
