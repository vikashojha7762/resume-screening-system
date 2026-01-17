#!/usr/bin/env python3
"""
Standalone connection test script
Can be run directly or via docker-compose
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.db_connection_test import main

if __name__ == "__main__":
    main()

