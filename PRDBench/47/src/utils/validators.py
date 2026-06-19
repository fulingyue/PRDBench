# -*- coding: utf-8 -*-
"""Input validation utilities with domain-specific error codes."""

import re
from datetime import datetime
from typing import Any


class Validator:
    """Centralized input validation for the library management system."""

    # ── Student ID ──────────────────────────────────────────────────────────

    def validate_student_id(self, value: Any) -> tuple[bool, str]:
        """Validate a student ID.

        Rules:
        - Non-empty, non-None
        - 1–20 characters
        - Alphanumeric only (letters and digits)

        Returns:
            (is_valid, error_message)
        """
        if value is None:
            return False, "NotEnergyasEmpty: Student ID cannot be None"

        try:
            text = str(value)
        except Exception:
            return False, "NotEnergyasEmpty: Invalid student ID type"

        if not text or not text.strip():
            return False, "NotEnergyasEmpty: Student ID cannot be empty"

        if len(text) > 20:
            return False, "LengthRepublic: Student ID cannot exceed 20 characters"

        if not re.match(r'^[A-Za-z0-9]+$', text):
            return False, "CharacterandNumber: Student ID must contain only letters and digits"

        return True, ""

    # ── Password ────────────────────────────────────────────────────────────

    def validate_password(self, value: Any) -> tuple[bool, str]:
        """Validate a password.

        Rules:
        - Non-empty, non-None
        - 6–32 characters

        Returns:
            (is_valid, error_message)
        """
        if value is None:
            return False, "NotEnergyasEmpty: Password cannot be None"

        try:
            text = str(value)
        except Exception:
            return False, "NotEnergyasEmpty: Invalid password type"

        if not text:
            return False, "NotEnergyasEmpty: Password cannot be empty"

        if len(text) < 6 or len(text) > 32:
            return False, "LengthRepublic: Password must be 6–32 characters"

        return True, ""

    # ── Date ────────────────────────────────────────────────────────────────

    def validate_date(self, value: Any) -> tuple[bool, str]:
        """Validate a date string in YYYY-MM-DD format.

        Returns:
            (is_valid, error_message)
        """
        if not value:
            return False, "FormatStyle: Date cannot be empty"

        try:
            text = str(value)
        except Exception:
            return False, "FormatStyle: Invalid date value"

        if not re.match(r'^\d{4}-\d{2}-\d{2}$', text):
            return False, "FormatStyle: Date must be in YYYY-MM-DD format"

        try:
            datetime.strptime(text, '%Y-%m-%d')
        except ValueError:
            return False, "FormatStyle: Invalid calendar date (e.g. Feb 30 does not exist)"

        return True, ""

    # ── Book ID ─────────────────────────────────────────────────────────────

    def validate_book_id(self, value: Any) -> tuple[bool, str]:
        """Validate a book ID (1–30 printable characters, non-empty)."""
        if value is None:
            return False, "NotEnergyasEmpty: Book ID cannot be None"
        text = str(value).strip()
        if not text:
            return False, "NotEnergyasEmpty: Book ID cannot be empty"
        if len(text) > 30:
            return False, "LengthRepublic: Book ID cannot exceed 30 characters"
        return True, ""

    # ── Generic string ──────────────────────────────────────────────────────

    def validate_name(self, value: Any, max_len: int = 20, field: str = "Name") -> tuple[bool, str]:
        if value is None:
            return False, f"NotEnergyasEmpty: {field} cannot be None"
        text = str(value).strip()
        if not text:
            return False, f"NotEnergyasEmpty: {field} cannot be empty"
        if len(text) > max_len:
            return False, f"LengthRepublic: {field} cannot exceed {max_len} characters"
        return True, ""


validator = Validator()
