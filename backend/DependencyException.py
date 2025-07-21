#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Luka Pacar
Date: 2025-07-21
Description: DependencyException
"""
__author__ = "Luka Pacar"
__version__ = "1.0.0"

class DependencyException(Exception):
    """Exception raised when a declared dependency test method is not found."""
    pass