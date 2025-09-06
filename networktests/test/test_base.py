#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Author: Luka Pacar
Date: 2025-07-23
Description: unittests for base.py
"""

__author__ = "Luka Pacar"
__version__ = "1.0.0"

import unittest
from networktests.testcases.base import (
    DiagNetTest,
    repeat,
    skip,
    depends_on,
    expected_failure,
    ParameterMissingException,
    UnknownParameterException,
    DependencyException, IllegalGroupFormingException, MutuallyExclusiveGroupException,
)


class PingTest(DiagNetTest):
    _required_params = ["host"]
    _optional_params = ["label"]

    hosts = ["google.com", "8.8.8.8", "127.0.0.1"]

    def ping(self, host):
        """Ping for test-cases (not an actual ping command)."""
        if not host:
            return False
        return host in self.hosts

    def test_ping(self):
        """Test network connectivity by pinging the specified host."""
        return self.ping(self.host)

    @expected_failure  # invert output
    def test_fail_ping(self):
        """Test network connectivity by pinging the specified host."""
        return not self.ping(self.host)

    @skip("This test is skipped and should not run.")
    def test_being_skipped(self):
        """This test is skipped and should not run."""
        return False

    @repeat(times=3, delay=0.1)
    def test_being_repeated(self):
        """This test is repeated 3 times with a delay of 0.1 seconds."""
        return True

    @depends_on("test_ping")
    def test_ping_dependency(self):
        """This test depends on the successful execution of test_ping."""
        return True

    @repeat(times=3, delay=1)
    @expected_failure
    @depends_on("test_ping_dependency")
    def test_ping_dependency_dependency(self):
        """This test depends on the successful execution of test_ping_dependency."""
        return False


class TestTest(unittest.TestCase):

    def test_optional(self):
        test_class = PingTest()
        assert test_class.run(host="127.0.0.1", label="hi")["result"] == "PASS" # with optional
        assert test_class.run(host="127.0.0.1")["result"] == "PASS" # without optional

    def test_mutually_exclusive(self):

        class MutuallyExclusiveTest(DiagNetTest):
            _required_params = ["host"]
            _mutually_exclusive_parameters = [("host", "ip")]

            def test_ping(self):
                return True

        test_class = MutuallyExclusiveTest()
        with self.assertRaises(ParameterMissingException):
            _ = test_class.run(host="127.0.0.1")["result"]

        class MutuallyExclusiveTest2(DiagNetTest):
            _required_params = ["host", "ip", "label"]
            _mutually_exclusive_parameters = [("host", "ip", "label")]

            def test_ping(self):
                return True

        test_class = MutuallyExclusiveTest2()
        assert test_class.run(host="127.0.0.1")["result"] == "PASS"

        class MutuallyExclusiveTest3(DiagNetTest):
            _required_params = ["host", "ip"]
            _optional_params = ["label"]
            _mutually_exclusive_parameters = [("host", "ip", "label")]

            def test_ping(self):
                return True

        test_class = MutuallyExclusiveTest3()
        with self.assertRaises(IllegalGroupFormingException):
            _ = test_class.run(host="127.0.0.1")["result"]

        class MutuallyExclusiveTest4(DiagNetTest):
            _required_params = ["host", "ip"]
            _optional_params = ["label"]
            _mutually_exclusive_parameters = [("host", "label")]

            def test_ping(self):
                return True

        test_class = MutuallyExclusiveTest4()
        with self.assertRaises(IllegalGroupFormingException):
            _ = test_class.run(host="127.0.0.1")["result"]

        class MutuallyExclusiveTest5(DiagNetTest):
            _required_params = ["host", "ip"]
            _optional_params = ["label"]
            _mutually_exclusive_parameters = [("host", "ip")]

            def test_ping(self):
                return True

        test_class = MutuallyExclusiveTest5()
        with self.assertRaises(MutuallyExclusiveGroupException):
            _ = test_class.run(host="127.0.0.1", ip="192.168.0.1")["result"]




    def test_run(self):
        test_class = PingTest()
        assert test_class.run(host="127.0.0.1")["result"] == "PASS"
        assert test_class.run(host="8.8.8.8")["result"] == "PASS"
        assert test_class.run(host="google.com")["result"] == "PASS"
        assert test_class.run(host="16.16.16.16")["result"] == "FAIL"
        assert test_class.run(host="google.not_a_domain")["result"] == "FAIL"
        assert test_class.run(host="")["result"] == "FAIL"

    def test_parameter_missing_exception(self):
        test_class = PingTest()
        with self.assertRaises(ParameterMissingException):
            test_class.run()

    def test_unknown_parameter_exception(self):
        test_class = PingTest()
        with self.assertRaises(UnknownParameterException):
            test_class.run(
                host="google.com", source="1.1.1.1"
            )  # "source" is not a valid parameter

    def test_repetition_fail(self):
        class TestClass(DiagNetTest):
            def _setup(self) -> None:
                self.counter = 0

            @repeat(times=3, delay=0.1)
            def test_repeated(self):
                self.counter += 1
                assert self.counter < 3  # Fails on 3rd attempt

        test_class = TestClass()
        result = test_class.run()

        assert result["result"] == "FAIL" and result["tests"]["test_repeated"][
            "message"
        ].startswith("Repetition Fail")

    def test_self_dependency(self):
        class TestClass(DiagNetTest):
            def _setup(self) -> None:
                self.counter = 0

            @depends_on("test_dependency")
            def test_dependent(self):
                return True

        test_class = TestClass()
        with self.assertRaises(DependencyException):
            _ = test_class.run()

    def test_dependency_loop(self):
        class TestClass(DiagNetTest):
            def _setup(self) -> None:
                self.counter = 0

            @depends_on("test_dependent_2")
            def test_dependent_1(self):
                return True

            @depends_on("test_dependent_1")
            def test_dependent_2(self):
                return True

        test_class = TestClass()
        with self.assertRaises(DependencyException):
            _ = test_class.run()

    def test_dependencies(self):
        class TestClass(DiagNetTest):
            def _setup(self) -> None:
                self.counter = 0

            def test_1(self):
                return True

            @skip
            @depends_on("test_1")
            def test_dependent_2(self):
                return True

            @depends_on("test_dependent_2")
            def test_dependent_3(self):
                return True

            @depends_on("test_1")
            def test_dependent_4(self):
                return False

            @depends_on("test_dependent_4")
            def test_dependent_5(self):
                return True

        test_class = TestClass()
        result = test_class.run()
        assert result["tests"]["test_dependent_2"]["status"] == "SKIPPED"
        assert (
            result["tests"]["test_dependent_3"]["status"]
            == "SKIPPED_DUE_TO_DEPENDENCY_SKIP"
        )
        assert result["tests"]["test_dependent_4"]["status"] == "FAIL"
        assert (
            result["tests"]["test_dependent_5"]["status"]
            == "SKIPPED_DUE_TO_DEPENDENCY_FAIL"
        )
