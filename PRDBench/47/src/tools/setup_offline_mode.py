#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setup script — configures SQLite offline mode and initialises the database."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    try:
        from config.database_mode import db_mode_manager
        db_mode_manager.switch_to_sqlite()
        from utils.database import db_manager
        db_manager.initialize()
        print("Offline mode configured: SQLite database initialised at", db_manager.db_path)
        return 0
    except Exception as e:
        print(f"Setup failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
