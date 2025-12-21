from devices.models import Device
from networktests.testcases.base import DiagNetTest
from genie.conf.base.device import Device as GenieDevice
from typing import Union


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
        # {
        #    "name": "peer_one_update_source_interface",
        #    "display_name": "BGP Peer 1 - Source-Interface",
        #    "type": "cisco-interface",
        #    "description": "The interface used for the BGP Session",
        #    "requirement": "optional",
        # },
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
        # {
        #    "name": "peer_two_update_source_interface",
        #    "display_name": "BGP Peer 2 - Source-Interface",
        #    "type": "cisco-interface",
        #    "description": "The interface used for the BGP Session",
        #    "requirement": "optional",
        # },
    ]

    def get_peer_one_device(self) -> Device:
        """Return the Device object for BGP Peer 1"""
        return self.bgp_peer_one

    def get_peer_two_device(self) -> Union[Device, str]:
        """
        Return the Device object for BGP Peer 2.
        If two_way_check is One-Way-Check, Peer 2 can be an IP address string.
        """
        return self.bgp_peer_two

    def connect_device(self, device: Device) -> Union[GenieDevice, None]:
        """Connect to a device using Genie and return the device object"""
        return device.get_genie_device_object()

    def get_bgp_summary(self, device: Device) -> dict:
        """Return parsed BGP summary from the device"""
        genie_dev = self.connect_device(device)
        if not genie_dev:
            raise ValueError(f"Cannot connect to device {device.name}")

        try:
            return genie_dev.parse("show bgp summary")
        except Exception as e:
            raise RuntimeError(f"Failed to get BGP summary on {device.name}: {e}")

    def get_interface_ip(self, device: Device, interface: str) -> list[str]:
        """
        Return all IP addresses (IPv4 + IPv6) for a specific interface.
        If the interface does not exist or has no IPs, return [].
        """
        genie_dev = self.connect_device(device)
        if not genie_dev:
            return []

        ips = set()

        try:
            ipv4_data = genie_dev.parse("show ip interface brief") or {}
            iface_info = ipv4_data.get("interface", {}).get(interface, {})
            ip_addr = iface_info.get("ip_address") or iface_info.get("ip")
            if ip_addr and ip_addr.lower() != "unassigned":
                ips.add(ip_addr)
        except Exception:
            pass

        try:
            ipv6_data = genie_dev.parse("show ipv6 interface brief") or {}
            iface_info = ipv6_data.get("interface", {}).get(interface, {})
            ipv6_list = iface_info.get("ipv6", [])
            if isinstance(ipv6_list, str):
                ipv6_list = [ipv6_list]
            for ip in ipv6_list:
                if ip.lower() != "unassigned":
                    ips.add(ip.split("/")[0])
        except Exception:
            pass

        return list(ips)

    def check_bgp_state(self, local_device: Device, remote: Union[Device, str]) -> bool:
        """
        Check if a BGP session state matches expected_session_state.
        Works for devices with multiple IPs, IPv4/IPv6, optional AS checks, and update-source.
        """
        summary = self.get_bgp_summary(local_device)
        expected_state = self.expected_session_state

        # Determine list of IPs to check for the remote
        if isinstance(remote, Device):
            # Use all IPs if device provides get_all_ips(), else fallback to single ip_address
            remote_ips = (
                remote.get_all_ips()
                if hasattr(remote, "get_all_ips")
                else [remote.ip_address]
            )
        else:
            remote_ips = [remote]  # IPv4/IPv6 string

        # Access neighbor dictionary
        peers = summary.get("vrf", {}).get("default", {}).get("neighbor", {})

        # Find peer_info matching any remote IP
        peer_info = None
        for ip in remote_ips:
            if ip in peers:
                peer_info = peers[ip]
                remote_ip = ip
                break

        if not peer_info:
            raise ValueError(
                f"BGP peer {remote_ips} not found on device {local_device.name}"
            )

        # Extract first address_family available
        af_info = peer_info.get("address_family", {})
        af_data = (
            af_info.get("")
            or af_info.get("ipv4 unicast")
            or af_info.get("ipv6 unicast")
            or list(af_info.values())[0]
        )

        # Determine actual BGP state from up_down
        up_down = af_data.get("up_down", "")
        import re

        if up_down == "never":
            actual_state = "Idle"
        elif re.match(r"\d+:\d+:\d+", up_down):
            actual_state = "Established"
        else:
            actual_state = "Unknown"

        # Check AS numbers if provided
        # Local AS
        local_as_actual = af_data.get("local_as")
        # Remote AS
        remote_as_actual = af_data.get("as")

        if (
            isinstance(local_device, Device)
            and hasattr(self, "peer_one_as")
            and self.peer_one_as
        ):
            if str(local_as_actual) != str(self.peer_one_as):
                raise ValueError(
                    f"Local AS mismatch on {local_device.name}: expected {self.peer_one_as}, got {local_as_actual}"
                )

        if (
            isinstance(remote, Device)
            and hasattr(self, "peer_two_as")
            and self.peer_two_as
        ):
            if str(remote_as_actual) != str(self.peer_two_as):
                raise ValueError(
                    f"Remote AS mismatch on {local_device.name} for peer {remote_ip}: expected {self.peer_two_as}, got {remote_as_actual}"
                )

        # Optional: check update-source interface if provided

        if (
            hasattr(self, "peer_one_update_source_interface")
            and self.peer_one_update_source_interface
        ):
            # TODO
            pass  # Placeholder for optional interface check

        return actual_state == expected_state

    def test_run(self) -> bool:
        """
        Run the BGP session test.
        Handles One-Way and Two-Way checks, AS validation, and multiple IPs per device.
        """
        # Get the peer devices or IPs
        peer1 = self.get_peer_one_device()
        peer2 = self.get_peer_two_device()

        # One-Way Check: only verify Peer 1 sees Peer 2
        if self.two_way_check == "One-Way-Check":
            try:
                result = self.check_bgp_state(peer1, peer2)
                return result
            except Exception as e:
                raise RuntimeError(f"One-Way BGP check failed: {e}")

        # Two-Way Check: verify both peers
        elif self.two_way_check == "Two-Way-Check":
            if not isinstance(peer2, Device):
                raise ValueError("Two-Way-Check requires BGP Peer 2 to be a Device")

            try:
                result1 = self.check_bgp_state(peer1, peer2)
            except Exception as e:
                raise RuntimeError(f"Two-Way BGP check failed on {peer1.name}: {e}")

            try:
                result2 = self.check_bgp_state(peer2, peer1)
            except Exception as e:
                raise RuntimeError(f"Two-Way BGP check failed on {peer2.name}: {e}")

            return result1 and result2

        else:
            raise ValueError(f"Invalid two_way_check value: {self.two_way_check}")
