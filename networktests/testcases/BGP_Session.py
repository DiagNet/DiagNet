import re

from devices.models import Device
from networktests.testcases.base import DiagNetTest, depends_on
from typing import Union

__author__ = "Luka Pacar"


class BGP_Session(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family:Arial,sans-serif; line-height:1.5; max-width:800px;">
        <h2 class="mb-3">BGP_Session Test Class</h2>
        <p>
            The <strong>BGP_Session</strong> test class validates that a BGP session exists between two network devices.
            It can perform a one-way or two-way check depending on the test configuration and ensures that the session reaches the expected state.
        </p>

        <h4 class="mt-4 mb-2">Purpose</h4>
        <p>
            This test verifies that BGP peers are able to establish a session and maintain the expected state.
            It is useful for network diagnostics, automation, and proactive validation of BGP configurations.
        </p>

        <h4 class="mt-4 mb-2">Parameters</h4>

        <h5 class="mt-3">Required Parameters</h5>
        <ul class="list-group mb-3">
            <li class="list-group-item">
                <strong>Type of Test</strong> (<em>choice</em>)<br>
                Marks if the session is supposed to be checked on both devices or only one.<br>
                Choices: One-Way-Check, Two-Way-Check. Default: One-Way-Check.
            </li>
            <li class="list-group-item">
                <strong>BGP Peer 1</strong> (<em>Device</em>)<br>
                The device from which to test the BGP session.
            </li>
            <li class="list-group-item">
                <strong>BGP Peer 2</strong> (<em>Device, IPv4, or IPv6</em>)<br>
                The second device or peer to check the BGP session. If <em>Type of Test</em> is One-Way-Check, IPv4 or IPv6 may also be used.
            </li>
            <li class="list-group-item">
                <strong>Expected Session State</strong> (<em>choice</em>)<br>
                The expected BGP session state between the peers. Choices: Idle, Connect, Active, OpenSent, OpenConfirm, Established.
            </li>
        </ul>

        <h5 class="mt-3">Optional Parameters</h5>
        <ul class="list-group mb-3">
            <li class="list-group-item">
                <strong>BGP Peer 1 - AS</strong> (<em>number</em>)<br>
                Autonomous System number for Peer 1.
            </li>
            <li class="list-group-item">
                <strong>BGP Peer 1 - Source Interface</strong> (<em>cisco-interface</em>)<br>
                Interface used for the BGP session from Peer 1.
            </li>
            <li class="list-group-item">
                <strong>BGP Peer 2 - AS</strong> (<em>number</em>)<br>
                Autonomous System number for Peer 2.
            </li>
            <li class="list-group-item">
                <strong>BGP Peer 2 - Source Interface</strong> (<em>cisco-interface</em>)<br>
                Interface used for the BGP session from Peer 2.
            </li>
        </ul>

        <h4 class="mt-4 mb-2">How it Works</h4>
        <p>
            The test checks if a BGP session is established between the specified peers. Based on the <em>Type of Test</em> parameter:
        </p>
        <ol>
            <li>One-Way Check: Verifies that Peer 1 sees Peer 2 as established.</li>
            <li>Two-Way Check: Verifies that both peers have an established session with each other.</li>
        </ol>
        <p>
            The test will fail if the BGP session does not reach the expected state or is not configured correctly.
        </p>

        <h4 class="mt-4 mb-2">Why Use This Test</h4>
        <ul>
            <li>Automatically verify BGP session establishment between devices.</li>
            <li>Detect misconfigurations or missing BGP connections before impacting network routing.</li>
            <li>Ensure compliance with network BGP policies.</li>
        </ul>
    </div>
    """

    _params = [
        {
            "name": "two_way_check",
            "display_name": "Type of Test",
            "description": "Marks if the session is supposed to be checked on both devices or only one",
            "type": "choice",
            "choices": ["One-Way-Check", "Two-Way-Check"],
            "default_choice": "One-Way-Check",
            "requirement": "required",
        },
        {
            "name": "expected_session_state",
            "display_name": "Expected Session State",
            "type": "choice",
            "choices": [
                "Idle",
                "Connect",
                "Active",
                "OpenSent",
                "OpenConfirm",
                "Established",
            ],
            "default_choice": "Established",
            "description": "The expected type of session state between the two peers",
            "requirement": "required",
        },
        {
            "name": "bgp_peer_one",
            "display_name": "BGP Peer 1",
            "type": "Device",
            "description": "The device from which to test the routes",
            "requirement": "required",
        },
        {
            "name": "peer_one_as",
            "display_name": "BGP Peer 1 - AS",
            "type": "positive-number",
            "requirement": "optional",
        },
        {
            "name": "bgp_peer_two",
            "display_name": "BGP Peer 2",
            "type": [
                "Device",
                {"name": "IPv4", "condition": {"two_way_check": "One-Way-Check"}},
                {"name": "IPv6", "condition": {"two_way_check": "One-Way-Check"}},
            ],
            "requirement": "required",
        },
        {
            "name": "peer_two_as",
            "display_name": "BGP Peer 2 - AS",
            "type": "positive-number",
            "requirement": "optional",
        },
    ]

    @staticmethod
    def _get_bgp_summary(dev: Device):
        genie_dev = dev.get_genie_device_object()
        if not genie_dev:
            raise ValueError(f"Connection failed: {dev.name}")
        return genie_dev.parse("show bgp summary")

    def _validate(
        self,
        local: Device,
        remote: Union[Device, str],
        l_as: int = None,
        r_as: int = None,
    ) -> bool:
        summary = self._get_bgp_summary(local)

        # Get all possible IPs for the remote device to match against neighbor list
        remote_ips = (
            [remote]
            if isinstance(remote, str)
            else (
                remote.get_all_ips()
                if hasattr(remote, "get_all_ips")
                else [remote.ip_address]
            )
        )

        peers = summary.get("vrf", {}).get("default", {}).get("neighbor", {})
        peer_ip = next((ip for ip in remote_ips if ip in peers), None)

        if not peer_ip:
            raise ValueError(f"Neighbor {remote_ips} not found on {local.name}")

        # Access first available address family
        af_data = next(iter(peers[peer_ip].get("address_family", {}).values()), {})

        # Normalize state: IOS returns uptime if established, otherwise state name
        up_down = str(af_data.get("up_down", "")).lower()
        actual = (
            "Established"
            if re.match(r"\d+:\d+:\d+", up_down)
            else ("Idle" if up_down == "never" else up_down.capitalize())
        )

        # Validate AS numbers
        if l_as and str(af_data.get("local_as")) != str(l_as):
            raise ValueError(f"Local AS mismatch on {local.name}")
        if r_as and str(af_data.get("as")) != str(r_as):
            raise ValueError(f"Remote AS mismatch on {local.name}")

        return actual == self.expected_session_state

    def test_device_connection(self) -> bool:
        can_connect_to_device_one = self.bgp_peer_one.can_connect()
        can_connect_to_device_two = self.bgp_peer_two.can_connect()
        if not can_connect_to_device_one:
            raise ValueError(f"Could not connect to Device {self.bgp_peer_one.name}")

        if self.two_way_check == "Two-Way-Check" and not can_connect_to_device_two:
            raise ValueError(f"Could not connect to Device {self.bgp_peer_two.name}")

        return True

    @depends_on("test_device_connection")
    def test_bgp_peering(self) -> bool:
        res1 = self._validate(
            self.bgp_peer_one,
            self.bgp_peer_two,
            getattr(self, "peer_one_as", None),
            getattr(self, "peer_two_as", None),
        )

        if self.two_way_check == "One-Way-Check":
            return res1

        if not isinstance(self.bgp_peer_two, Device):
            raise ValueError("Two-Way-Check requires Peer 2 to be a Device object")

        res2 = self._validate(
            self.bgp_peer_two,
            self.bgp_peer_one,
            getattr(self, "peer_two_as", None),
            getattr(self, "peer_one_as", None),
        )
        return res1 and res2
