"""
Auth Dependencies for AI Modules
Compatibility layer for existing AI module imports
"""

import sys
import os

# Add the backend root to the path
backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Import from the correct location
from auth.dependencies import get_current_user

# Re-export for backward compatibility
__all__ = ['get_current_user']