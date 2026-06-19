# -*- coding: utf-8 -*-
"""Application settings and file path configuration."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILE_PATHS = {
    'db_dir':     os.path.join(BASE_DIR, 'data'),
    'sqlite_db':  os.path.join(BASE_DIR, 'data', 'library.db'),
    'charts_dir': os.path.join(BASE_DIR, 'data', 'charts'),
    'backup_dir': os.path.join(BASE_DIR, 'data', 'backup'),
    'log_dir':    os.path.join(BASE_DIR, 'logs'),
    'log_file':   os.path.join(BASE_DIR, 'logs', 'system.log'),
}

# Ensure required directories exist
for _dir in ('db_dir', 'charts_dir', 'backup_dir', 'log_dir'):
    os.makedirs(FILE_PATHS[_dir], exist_ok=True)

# Database configuration
DB_CONFIG = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': '',
    'database': 'library',
    'charset':  'utf8mb4',
}

# Borrowing limits
BORROW_LIMIT_USER  = 5
BORROW_LIMIT_ADMIN = 10
LOAN_PERIOD_DAYS   = 30
