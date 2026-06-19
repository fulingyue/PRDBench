# -*- coding: utf-8 -*-
"""Cryptographic utilities — MD5 password hashing."""

import hashlib


class Encryptor:
    """Password encryption utilities."""

    def md5_hash(self, text: str) -> str:
        """Return the 32-character lowercase MD5 hex digest of *text*."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def verify_password(self, plaintext: str, hashed: str) -> bool:
        """Return True if *plaintext* hashes to *hashed*."""
        return self.md5_hash(plaintext) == hashed


encryptor = Encryptor()
