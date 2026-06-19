# -*- coding: utf-8 -*-
"""Database mode manager — selects between MySQL and SQLite."""

import os


class DatabaseModeManager:
    """Manages the active database backend (MySQL vs SQLite)."""

    MODE_SQLITE = 'sqlite'
    MODE_MYSQL  = 'mysql'

    def __init__(self) -> None:
        self._mode: str = self.MODE_SQLITE  # default to SQLite

    @property
    def current_mode(self) -> str:
        return self._mode

    def switch_to_sqlite(self) -> None:
        """Force SQLite mode and (re)initialize the DB manager."""
        self._mode = self.MODE_SQLITE
        self._reinitialize()

    def switch_to_mysql(self) -> None:
        """Switch to MySQL mode."""
        self._mode = self.MODE_MYSQL
        self._reinitialize()

    def select_database_mode(self, prefer_sqlite: bool = True) -> str:
        """Select the best available database mode.

        Args:
            prefer_sqlite: When True, use SQLite if MySQL is unavailable.

        Returns:
            The active mode string ('sqlite' or 'mysql').
        """
        if prefer_sqlite:
            self.switch_to_sqlite()
            return self.MODE_SQLITE

        # Try MySQL; fall back to SQLite
        try:
            import mysql.connector  # noqa: F401
            self._mode = self.MODE_MYSQL
        except Exception:
            self._mode = self.MODE_SQLITE

        self._reinitialize()
        return self._mode

    def _reinitialize(self) -> None:
        """Re-run database initialization after mode switch."""
        try:
            from utils.database import db_manager
            db_manager.mode = self._mode
            db_manager.initialize()
        except Exception:
            pass


db_mode_manager = DatabaseModeManager()
