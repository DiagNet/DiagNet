#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Luka Pacar
Date: 2025-07-21
Description: Parent-Class for defining Tests.
"""
__author__ = "Luka Pacar"
__version__ = "1.0.0"


class Test:
    """
        Base class for defining and running test cases.

        This class provides a framework to define tests as methods prefixed with "test_".
        supports test dependencies, skipping, repeating, and expected failure handling.

        Tests are automatically discovered, ordered by dependencies, and executed with
        detailed result reporting, including pass/fail/skip status and logging output.

        Intended to be subclassed to implement specific tests by overriding setup, teardown,
        and defining test methods.
    """
