import os
import sys

# Add root directory and expense_tracker module to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tracker_dir = os.path.join(root_dir, "expense_tracker")

if tracker_dir not in sys.path:
    sys.path.insert(0, tracker_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app
