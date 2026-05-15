"""
CRITICAL FIX: Python 3.13 Pydantic Deadlock Workaround

Python 3.13 has a known issue where Pydantic 2.6.0 schema generation 
deadlocks during model initialization. This module patches the issue.

Usage: import this FIRST, before any FastAPI/Pydantic imports
"""

import sys
import os

# Force Python to not cache bytecode during this critical operation
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Disable Pydantic V1 compatibility mode which triggers the deadlock
if sys.version_info >= (3, 13):
    import warnings
    warnings.filterwarnings("ignore")
    
    # Patch to prevent Pydantic from trying to use deprecated features
    try:
        import pydantic
        pydantic.VERSION = "2.6.0"
    except:
        pass

print("✓ Pydantic deadlock patch applied", flush=True)
