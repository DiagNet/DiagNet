#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Luka Pacar
Date: 2025-07-21
Description: Parent-Class for defining Tests.
"""

__author__ = "Luka Pacar"
__version__ = "1.2.0"

from typing import List, Dict, Tuple
from collections import defaultdict, deque
import time


# Exceptions
class DependencyException(Exception):
    """Exception raised when a declared dependency test method is not found."""

    pass


class ParameterMissingException(Exception):
    """Exception raised when required parameters are missing."""

    pass


class UnknownParameterException(Exception):
    """Exception raised when an unexpected Parameter is parsed."""

    pass


class IllegalGroupFormingException(Exception):
    """Exception raised when required and optional parameters are mixed in a mutually exclusive group."""

    pass


class MutuallyExclusiveGroupException(Exception):
    """Exception raised when more than 1 element is parsed in a mutually exclusive group relation."""

    pass


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


def skip(arg=None):
    """
    Decorator to mark a test method to be skipped.

    Args:
        reason (str, optional): Explanation why the test is skipped. Defaults to None.
    """
    if callable(arg):
        # Used as @skip
        func = arg
        func._skip = True
        func._skip_reason = None
        return func

    def decorator(func):
        func._skip = True
        func._skip_reason = arg
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


def filter_out_skipped(test_methods, skipped, results, status_map):
    amount_skipped = 0
    # mark skipped tests immediately
    for name, method in test_methods:
        if getattr(method, "_skip", False):
            amount_skipped += 1
            skipped.add(name)
            results[name] = {
                "status": "SKIPPED",
                "message": getattr(method, "_skip_reason", ""),
                "time": 0,
            }
            status_map[name] = "SKIPPED"
            test_methods.remove((name, method))
        elif getattr(method, "_depends_on", None) in skipped:
            amount_skipped += 1
            skipped.add(name)
            results[name] = {
                "status": "SKIPPED_DUE_TO_DEPENDENCY_SKIP",
                "message": getattr(method, "_skip_reason", ""),
                "time": 0,
            }
            status_map[name] = "SKIPPED_DUE_TO_DEPENDENCY_SKIP"
            test_methods.remove((name, method))

    if amount_skipped != 0:
        return filter_out_skipped(
            test_methods, skipped, results, status_map
        )  # Remove depends_on chains

    return results, status_map


class DiagNetTest:
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
    """ Saves the required parameters needed for this Test """

    _optional_params: List[str] = []
    """ Saves the optional parameters needed for this Test """

    _mutually_exclusive_parameters: List[Tuple[str, ...]] = []
    """ Saves which pairs of parameters are mutually exclusive. """

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

    def get_required_params(self) -> Dict[str, str]:
        """
        Returns a dictionary of required parameters with their types.

        Returns:
            dict: A dictionary where keys are parameter names and values are their datatypes as strings.
        """
        params = {}
        for param in self._required_params:
            if ":" in param:
                name, type_ = param.split(":", 1)
                type_ = type_.strip()
                if "|" in type_:
                    type_ = type_.split("|")
                else:
                    type_ = [type_]

                params[name.strip()] = type_
            else:
                params[param.strip()] = "str"

        return params

    def get_optional_params(self) -> Dict[str, str]:
        """
        Returns a dictionary of optional parameters with their types.

        Returns:
            dict: A dictionary where keys are parameter names and values are their datatypes as strings.
        """
        params = {}
        for param in self._optional_params:
            if ":" in param:
                name, type_ = param.split(":", 1)
                type_ = type_.strip()
                if "|" in type_:
                    type_ = type_.split("|")
                else:
                    type_ = [type_]

                params[name.strip()] = type_
            else:
                params[param.strip()] = "str"

        return params

    def run(self, test_method_prefix="test_", verbose=False, **kwargs) -> Dict:
        """
        Runs the test and returns the output.

        Args:
            verbose (bool): verbose output
            test_method_prefix (str): defines the prefix of the test methods

        Returns:
            dict: {
            "result": "PASS"|"FAIL",
            "tests": {
                test_method_name: {
                    "status": "PASS"|"FAIL"|"SKIPPED"|"SKIPPED_DUE_TO_DEPENDENCY_FAIL"|"SKIPPED_DUE_TO_DEPENDENCY_SKIP",
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

        parsed_arguments: List[...] = list(kwargs.keys())

        # --- 1.1 Strip datatype from parameters ---

        # required parameters
        defined_required_arguments: List[...] = []
        for e in self._required_params:
            if ":" in e:
                base_name = e.split(":")[0].strip()
                defined_required_arguments.append(base_name)
            else:
                defined_required_arguments.append(e)

        # optional parameters
        defined_optional_arguments: List[...] = []
        for e in self._optional_params:
            if ":" in e:
                base_name = e.split(":")[0].strip()
                defined_optional_arguments.append(base_name)
            else:
                defined_optional_arguments.append(e)

        # --- 1.2 Check mutually exclusive validity ---

        mutually_ignored_arguments: List[...] = []

        # check mutually exclusive parameters
        for mutually_exclusive_pairs in self._mutually_exclusive_parameters:
            if len(mutually_exclusive_pairs) < 2:
                raise IllegalGroupFormingException(
                    "Mutually Exclusive Group has to contain at least 2 elements."
                )

            # elements of the mutually exclusive pair have to exist as actual parameters.
            for e in mutually_exclusive_pairs:
                if e not in defined_required_arguments and e not in defined_optional_arguments:
                    raise ParameterMissingException(
                        f'Element "{e}" in mutually exclusive group "{mutually_exclusive_pairs}" is not a defined parameter.'
                    )

            # members of a mutually exclusive group have to all be in either "required" or "optional". (mixing them would not make sense)
            required_count = sum(
                1 for e in mutually_exclusive_pairs if e in self._required_params
            )
            if required_count != 0 and required_count is not len(
                    mutually_exclusive_pairs
            ):
                raise IllegalGroupFormingException(
                    f"Unable to mix required and optional parameters in the mutually exclusive group: {mutually_exclusive_pairs}"
                )

            # Count number of parsed elements.
            parsed_elements = sum(
                1 for e in mutually_exclusive_pairs if e in parsed_arguments
            )

            if required_count == 0:  # Optional parameter.
                if parsed_elements > 1:
                    raise MutuallyExclusiveGroupException(
                        f"Unable to process 2 or more parsed parameters of the same mutually exclusive group: {mutually_exclusive_pairs}"
                    )
                # having 1 optional element or none is legal.
            else:
                if parsed_elements == 0:
                    raise MutuallyExclusiveGroupException(
                        f"At least 1 element of the required mutually exclusive group has to be parsed: {mutually_exclusive_pairs}"
                    )
                if parsed_elements > 1:
                    raise MutuallyExclusiveGroupException(
                        f"Unable to process 2 or more parsed parameters of the same mutually exclusive group: {mutually_exclusive_pairs}"
                    )
                # having 1 required element is legal.

            # Remove processed mutually exclusive groups for further checks.
            for e in mutually_exclusive_pairs:
                if e not in parsed_arguments:
                    mutually_ignored_arguments.append(e)

        # missing parameters
        missing = [p for p in defined_required_arguments if
                   p not in parsed_arguments and p not in mutually_ignored_arguments]
        if missing:
            raise ParameterMissingException(f"Missing required parameters: {missing}")

        # unknown parameters
        unknown = [
            k
            for k in parsed_arguments
            if k not in defined_required_arguments and k not in defined_optional_arguments
        ]
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
        results, status_map = filter_out_skipped(
            test_methods[:], set(), results, status_map
        )

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
                        "message": f"{e}",
                        "time": 0,
                    }
            return {
                "result": "FAIL",
                "tests": results,
                "summary": (len(results), 0, len(results), 0),
            }

        # run tests
        for test_name in ordered:
            # if dependency failed or skipped, skip this test
            method = getattr(self, test_name)
            dep = getattr(method, "_depends_on", None)
            if dep and status_map.get(dep) in (
                    "FAIL",
                    "SKIPPED_DUE_TO_DEPENDENCY_FAIL",
            ):
                results[test_name] = {
                    "status": "SKIPPED_DUE_TO_DEPENDENCY_FAIL",
                    "message": f"Skipped due to failed dependency: {dep}",
                    "time": 0,
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
                if (
                        i > 0 and delay > 0
                ):  # sleep when there is a delay and it is minimum the second cycle
                    time.sleep(delay)
                start = time.time()
                try:
                    result = method()

                    # treat None as True (void methods count as a PASS)
                    if result is None:
                        result = True

                    duration = time.time() - start
                    if not isinstance(result, bool):
                        raise ValueError(
                            f"Test method {test_name} must return a boolean or return None"
                        )
                    if result:
                        success = True
                    else:
                        success = False
                        fail_message = f"Test {test_name} returned False"
                except Exception as e:
                    duration = time.time() - start
                    success = False
                    fail_message = f"{e}"

                total_duration += duration

                if success:
                    success_count += 1
                    if verbose:
                        print(
                            f"{test_name} run {i + 1}/{amount_of_repeat} PASS in {duration:.3f}s"
                        )
                else:
                    if verbose:
                        print(
                            f"{test_name} run {i + 1}/{amount_of_repeat} FAIL in {duration:.3f}s"
                        )
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
                    msg = (
                        f"Repetition Fail: {success_count}/{total_runs} successful runs. "
                        f"Last error: {fail_message}"
                    )
                else:
                    status = "FAIL"
                    msg = fail_message or ""

            results[test_name] = {
                "status": status,
                "message": msg,
                "time": total_duration,
            }
            status_map[test_name] = status

        # summarize
        total = len(results)
        passed = sum(1 for r in results.values() if r["status"] == "PASS")
        failed = sum(1 for r in results.values() if r["status"] == "FAIL")
        skipped = sum(
            1
            for r in results.values()
            if r["status"].startswith("SKIPPED")
            or r["status"].startswith("SKIPPED_DUE_TO_DEPENDENCY_FAIL")
            or r["status"].startswith("SKIPPED_DUE_TO_DEPENDENCY_SKIP")
        )

        # run teardown
        try:
            self._teardown()
        except Exception as e:
            # Teardown error, consider as FAIL for whole run
            results["teardown"] = {
                "status": "FAIL",
                "message": f"{e}",
                "time": 0,
            }
            return {
                "result": "FAIL",
                "tests": results,
                "summary": (total, passed, failed, skipped),
            }

        return {
            "result": ("PASS" if failed == 0 else "FAIL"),
            "tests": results,
            "summary": (total, passed, failed, skipped),
        }
