# -*- coding: utf-8 -*-
"""Database manager — SQLite backend with MySQL fallback interface."""

import sqlite3
import os
import threading
from typing import Any, Optional

from config.settings import FILE_PATHS


_CREATE_USER_TABLE = """
CREATE TABLE IF NOT EXISTS user (
    StudentId  VARCHAR(20) PRIMARY KEY,
    Name       VARCHAR(20) NOT NULL,
    Password   VARCHAR(32) NOT NULL,
    IsAdmin    INTEGER DEFAULT 0,
    tel        VARCHAR(30),
    CreateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_CREATE_BOOK_TABLE = """
CREATE TABLE IF NOT EXISTS book (
    BookName      VARCHAR(30) NOT NULL,
    BookId        CHAR(30)    PRIMARY KEY,
    Auth          VARCHAR(20) NOT NULL,
    Category      VARCHAR(10),
    Publisher     VARCHAR(30),
    PublishTime   DATE,
    NumStorage    INTEGER DEFAULT 0,
    NumCanBorrow  INTEGER DEFAULT 0,
    NumBookinged  INTEGER DEFAULT 0,
    CreateTime    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdateTime    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_CREATE_USER_BOOK_TABLE = """
CREATE TABLE IF NOT EXISTS user_book (
    StudentId    CHAR(10)  NOT NULL,
    BookId       CHAR(30)  NOT NULL,
    BorrowTime   DATE      NOT NULL DEFAULT (date('now')),
    ReturnTime   DATE,
    BorrowState  INTEGER DEFAULT 1,
    BookingState INTEGER DEFAULT 0,
    CreateTime   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdateTime   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (StudentId, BookId, BorrowTime)
)
"""


class DatabaseManager:
    """Thread-safe SQLite database manager with a MySQL-compatible interface."""

    def __init__(self) -> None:
        self.mode: str = 'sqlite'
        self.db_path: str = FILE_PATHS['sqlite_db']
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self.initialize()

    # ── Public API ──────────────────────────────────────────────────────────

    def initialize(self) -> bool:
        """Create tables if they do not exist."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with self._get_conn() as conn:
                cur = conn.cursor()
                cur.execute(_CREATE_USER_TABLE)
                cur.execute(_CREATE_BOOK_TABLE)
                cur.execute(_CREATE_USER_BOOK_TABLE)
                conn.commit()
            return True
        except Exception as e:
            print(f"Database initialization error: {e}")
            return False

    def test_connection(self) -> bool:
        """Return True if a connection can be established."""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            return True
        except Exception:
            return False

    def execute_query(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        """Execute a SELECT statement and return rows as dicts."""
        try:
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Query error: {e}")
            return []

    def execute_update(
        self,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> int:
        """Execute an INSERT/UPDATE/DELETE and return rows affected."""
        try:
            with self._get_conn() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                conn.commit()
                return cur.rowcount
        except Exception as e:
            print(f"Update error: {e}")
            return -1

    def execute_many(
        self,
        sql: str,
        params_list: list[tuple[Any, ...]],
    ) -> int:
        """Execute a batch INSERT/UPDATE."""
        try:
            with self._get_conn() as conn:
                cur = conn.cursor()
                cur.executemany(sql, params_list)
                conn.commit()
                return cur.rowcount
        except Exception as e:
            print(f"Batch update error: {e}")
            return -1

    # ── Internal ────────────────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)


db_manager = DatabaseManager()
