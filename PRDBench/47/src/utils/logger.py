# -*- coding: utf-8 -*-
"""System logging utilities — records key operations to logs/system.log."""

import os
import logging
from datetime import datetime

from config.settings import FILE_PATHS

_log_file = os.path.join(FILE_PATHS['log_dir'], 'system.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(_log_file, encoding='utf-8'),
        logging.StreamHandler(),
    ],
)

_logger = logging.getLogger('library')


def _fmt(operation_type: str, user: str, content: str) -> str:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"[{ts}] [{operation_type}] user={user} | {content}"


def log_operation(operation_type: str, user: str, content: str) -> None:
    """Record a key operation (user login, borrow, modify, etc.)."""
    try:
        _logger.info(_fmt(operation_type, user, content))
    except Exception as e:
        print(f"Logging error: {e}")


def log_error(operation_type: str, content: str, user: str = 'system') -> None:
    """Record an error event."""
    try:
        _logger.error(_fmt(operation_type, user, content))
    except Exception as e:
        print(f"Logging error: {e}")


def log_system_event(event_type: str, content: str) -> None:
    """Record a system-level event."""
    try:
        _logger.info(_fmt(event_type, 'system', content))
    except Exception as e:
        print(f"Logging error: {e}")
