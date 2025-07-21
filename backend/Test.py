#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Luka Pacar
Date: 2025-07-21
Description: Parent-Class for defining Tests.
"""
__author__ = "Luka Pacar"
__version__ = "1.0.0"

from typing import List, Dict


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

    _required_params: List[str] = []
    """´Saves the required parameters needed for this Test """

    def _setup(self) -> None:
        """
        Called before the execution of the test begins.
        This method functions as a setup space, allowing datastructures, network connections, file interactions ... to be initiated!
        """
        pass

    def _teardown(self) -> None:
        """
        Called after the execution of the test is finished.
        This method functions as a teardown space, allowing datastructures, network connections, file interactions ... to be handled!
        """
        pass

    def __run(self, verbose=False) -> Dict:
        """
        Runs the test and returns the output.

        Args:
            verbose (bool): verbose output

        Returns:
            Dict: {result: PASS/FAIL/SKIPPED, tests: {test_a: {"status": "PASS", "message": "", "time": 0.05}, test_b: {"status": "FAIL", "message": "SetupException: ...", "time": 0.01}}, summary: (total_tests, passed, failed, skipped)}
        """
        pass

