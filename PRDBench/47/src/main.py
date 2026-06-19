#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project 47 — Entry Point.

Starts the Library Management System CLI application.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run import main

if __name__ == '__main__':
    main()
