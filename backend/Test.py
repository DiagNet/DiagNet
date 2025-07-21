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
from collections import defaultdict, deque
from ParameterMissingException import ParameterMissingException
from UnknownParameterException import UnknownParameterException
from DependencyException import DependencyException
import time


# Decorators
def repeat(times, delay=0):
    """
    Decorator to repeat a test method multiple times with optional delay.

    Args:
        times (int): Number of times to repeat the test.
        delay (float, optional): Delay in seconds between repetitions. Defaults to 0.
    """

    def decorator(func):
        func._repeat = times
        func._repeat_delay = delay
        return func

    return decorator


def skip(reason=None):
    """
    Decorator to mark a test method to be skipped.

    Args:
        reason (str, optional): Explanation why the test is skipped. Defaults to None.
    """

    def decorator(func):
        func._skip = True
        func._skip_reason = reason
        return func

    return decorator


def depends_on(dependency_name):
    """
    Decorator to declare that a test method depends on another test method.

    Args:
        dependency_name (str): Name of the test method this test depends on.
    """

    def decorator(func):
        func._depends_on = dependency_name
        return func

    return decorator


def expected_failure(func):
    """
    Decorator to mark a test method as an expected failure.
    """
    func._expected_failure = True
    return func


# Topological sort for dependencies https://en.wikipedia.org/wiki/Topological_sorting
def sort_by_dependencies(test_methods: dict):
    """
    test_methods: dict of {name: function} where functions may have _depends_on attribute
    Returns a list of method names in dependency-respecting order.
    """

    # Build graph
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    all_methods = set(test_methods.keys())

    for name, func in test_methods.items():
        dep = getattr(func, "_depends_on", None)
        if dep:
            if dep not in test_methods:
                raise DependencyException(f"{dep} not found for {name}")
            graph[dep].append(name)
            in_degree[name] += 1
        else:
            in_degree.setdefault(name, 0)

    # Kahn's algorithm
    queue = deque([n for n in all_methods if in_degree[n] == 0])
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(all_methods):
        raise DependencyException("Cycle detected in test dependencies")

    return result


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

    def __run(self, test_method_prefix="test_", verbose=False, **kwargs) -> Dict:
        """
        Runs the test and returns the output.

        Args:
            verbose (bool): verbose output

        Returns:
            dict: {
            "result": "PASS"|"FAIL",
            "tests": {
                test_method_name: {
                    "status": "PASS"|"FAIL"|"SKIPPED"|"SKIPPED_DUE_TO_DEPENDENCY_FAIL",
                    "message": "",
                    "time": float (seconds)
                },
                test_method_name2: {}
            },
            "summary": (total, passed, failed, skipped)
            }
        """
        # output data structures
        results = {}
        status_map = {}

        #  --- 1. validate parameters ---

        # missing parameters
        missing = [p for p in self._required_params if p not in kwargs]
        if missing:
            raise ParameterMissingException(f"Missing required parameters: {missing}")

        # unknown parameters
        unknown = [k for k in kwargs if k not in self._required_params]
        if unknown:
            raise UnknownParameterException(f"Unknown parameters passed: {unknown}")

        # set parameters as attributes
        for name, value in kwargs.items():
            setattr(self, name, value)

        #  --- 2. find test methods starting with the test_method_prefix ---
        test_methods = []
        for attr in dir(self):
            if attr.startswith(test_method_prefix):
                method = getattr(self, attr)
                if callable(method):  # only accept methods not other attributes
                    test_methods.append((attr, method))

        # mark skipped tests immediately
        for name, method in test_methods:
            if getattr(method, "_skip", False):
                results[name] = {
                    "status": "SKIPPED",
                    "message": getattr(method, "_skip_reason", ""),
                    "time": 0
                }
                status_map[name] = "SKIPPED"

        # --- 3. order tests by dependency ---

        # filter out skipped tests
        active_methods = {
            name: method for name, method in test_methods if name not in status_map
        }

        # sort dependencies using topological sort
        try:
            ordered = sort_by_dependencies(active_methods)
        except DependencyException as e:
            raise e

        #  --- 4. run tests in order ---

        # run setup
        try:
            self._setup()
        except Exception as e:
            # Setup failed, all non-skipped tests fail now
            for name, method in test_methods:
                if name not in results:
                    results[name] = {
                        "status": "FAIL",
                        "message": f"SetupException: {e}",
                        "time": 0
                    }
            return {
                "result": "FAIL",
                "tests": results,
                "summary": (len(results), 0, len(results), 0)
            }

        # run tests
        for test_name in ordered:
            # if dependency failed or skipped, skip this test
            method = getattr(self, test_name)
            dep = getattr(method, "_depends_on", None)
            if dep and status_map.get(dep) in ("FAIL", "SKIPPED", "SKIPPED_DUE_TO_DEPENDENCY_FAIL"):
                results[test_name] = {
                    "status": "SKIPPED_DUE_TO_DEPENDENCY_FAIL",
                    "message": f"Skipped due to failed dependency: {dep}",
                    "time": 0
                }
                status_map[test_name] = "SKIPPED_DUE_TO_DEPENDENCY_FAIL"
                continue

            amount_of_repeat = getattr(method, "_repeat", 1)
            delay = getattr(method, "_repeat_delay", 0)
            test_expected_failure = getattr(method, "_expected_failure", False)
            total_duration = 0

            success_count = 0
            total_runs = amount_of_repeat
            fail_message = None

            for i in range(amount_of_repeat):
                if i > 0 and delay > 0:  # sleep when there is a delay and it is minimum the second cycle
                    time.sleep(delay)
                start = time.time()
                try:
                    result = method()
                    # treat None as implicit True
                    if result is None:
                        result = True

                    duration = time.time() - start
                    if not isinstance(result, bool):
                        raise ValueError(f"Test method {test_name} must return a boolean")
                    if result:
                        success = True
                    else:
                        success = False
                        fail_message = f"Test {test_name} returned False"
                except Exception as e:
                    duration = time.time() - start
                    success = False
                    fail_message = f"Exception: {e}"

                total_duration += duration

                if success:
                    success_count += 1
                    if verbose:
                        print(f"{test_name} run {i + 1}/{amount_of_repeat} PASS in {duration:.3f}s")
                else:
                    if verbose:
                        print(f"{test_name} run {i + 1}/{amount_of_repeat} FAIL in {duration:.3f}s")
                    break

            # determine final test status
            if success_count == total_runs:
                passed = True
            else:
                passed = False

            if test_expected_failure:  # invert result
                passed = not passed

            if passed:
                status = "PASS"
                msg = ""
            else:
                if amount_of_repeat > 1 and success_count > 0:
                    # Partial success on repeats -> REPETITION_FAIL
                    status = "FAIL"
                    msg = (f"Repetition Fail: {success_count}/{total_runs} successful runs. "
                           f"Last error: {fail_message}")
                else:
                    status = "FAIL"
                    msg = fail_message or ""

            results[test_name] = {
                "status": status,
                "message": msg,
                "time": total_duration
            }
            status_map[test_name] = status

        # run teardown
        try:
            self._teardown()
        except Exception as e:
            # Teardown error, consider as FAIL for whole run
            results["teardown"] = {
                "status": "FAIL",
                "message": f"TearDownException: {e}",
                "time": 0
            }
            return {
                "result": "FAIL",
                "tests": results,
                "summary": (len(results), 0, len(results), 0)
            }

        # summarize
        total = len(results)
        passed = sum(1 for r in results.values() if r["status"] == "PASS")
        failed = sum(1 for r in results.values() if r["status"] == "FAIL")
        skipped = sum(1 for r in results.values() if
                      r["status"].startswith("SKIPPED") or r["status"].startswith("SKIPPED_DUE_TO_DEPENDENCY_FAIL"))

        return {
            "result": ("PASS" if failed == 0 else "FAIL"),
            "tests": results,
            "summary": (total, passed, failed, skipped)
        }
