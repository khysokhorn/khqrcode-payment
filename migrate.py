#!/usr/bin/env python
"""Migration script to create/update database tables."""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.db import create_db_and_tables

if __name__ == "__main__":
    print("Running migrations...")
    try:
        create_db_and_tables()
        print("✓ Migrations completed successfully!")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
