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
            "name": "vrf",
            "display_name": "Default VRF",
            "type": "str",
            "default": "default",
            "requirement": "optional",
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
            "name": "peer_one_vrf",
            "display_name": "Peer 1 - VRF Override",
            "type": "str",
            "requirement": "optional",
            "description": "Only use if Peer 1 VRF differs from Default VRF.",
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
            "name": "peer_two_vrf",
            "display_name": "Peer 2 - VRF Override",
            "type": "str",
            "requirement": "optional",
            "description": "Only use if Peer 2 VRF differs from Default VRF.",
            "required_if": {"two_way_check": "Two-Way-Check"},
        },
        {
            "name": "peer_two_as",
            "display_name": "BGP Peer 2 - AS",
            "type": "positive-number",
            "requirement": "optional",
        },
    ]

    @staticmethod
    def _get_bgp_summary(dev: Device, vrf: str = "default"):
        genie_dev = dev.get_genie_device_object()
        if not genie_dev:
            raise ValueError(f"Connection failed: {dev.name}")

        cmd = "show bgp summary" if vrf == "default" else f"show bgp vrf {vrf} summary"
        return genie_dev.parse(cmd)

    def _to_int_str(self, val) -> Union[str, None]:
        try:
            return str(int(str(val).strip())) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _validate(
        self,
        local: Device,
        remote: Union[Device, str],
        l_as: Union[str, None],
        r_as: Union[str, None],
        vrf_override: str = None,
    ) -> bool:
        vrf = vrf_override or getattr(self, "vrf", "default") or "default"
        summary = self._get_bgp_summary(local, vrf)

        if isinstance(remote, str):
            remote_ips = [remote]
        else:
            remote_ips = (
                remote.get_all_ips()
                if hasattr(remote, "get_all_ips")
                else [remote.ip_address]
            )

        # Robust dictionary traversal for multi-platform support (IOS/XR/NX-OS)
        vrf_data = (
            summary.get("instance", {}).get("default", {}).get("vrf", {}).get(vrf, {})
        )
        if not vrf_data:
            vrf_data = summary.get("vrf", {}).get(vrf, {})

        peers = vrf_data.get("neighbor", {})
        peer_ip = next((ip for ip in remote_ips if ip in peers), None)

        if not peer_ip:
            raise ValueError(
                f"Neighbor {remote_ips} not found on {local.name} (VRF: {vrf})"
            )

        peer_data = peers[peer_ip]
        af_map = peer_data.get("address_family", {})
        if not af_map:
            raise ValueError(
                f"No address family data for neighbor {peer_ip} on {local.name}"
            )

        af_data = next(iter(af_map.values()))

        # BGP State Logic
        up_down = str(af_data.get("up_down", "")).lower()
        if up_down == "never":
            actual = "Idle"
        elif any(char.isdigit() for char in up_down):
            actual = "Established"
        else:
            actual = up_down.capitalize()

        # Attribute Validation
        if l_as and self._to_int_str(af_data.get("local_as")) != l_as:
            raise ValueError(f"Local AS mismatch on {local.name}: Expected {l_as}")

        if r_as and self._to_int_str(af_data.get("as")) != r_as:
            raise ValueError(f"Remote AS mismatch on {local.name}: Expected {r_as}")

        if actual != self.expected_session_state:
            raise ValueError(
                f"State mismatch on {local.name}: Expected {self.expected_session_state}, got {actual}"
            )

        return True

    def test_device_connection(self) -> bool:
        if not self.bgp_peer_one.can_connect():
            raise ValueError(f"Could not connect to Peer 1: {self.bgp_peer_one.name}")

        if self.two_way_check == "Two-Way-Check":
            if not isinstance(self.bgp_peer_two, Device):
                raise ValueError("Two-Way-Check requires Peer 2 to be a Device object")
            if not self.bgp_peer_two.can_connect():
                raise ValueError(
                    f"Could not connect to Peer 2: {self.bgp_peer_two.name}"
                )
        return True

    @depends_on("test_device_connection")
    def test_peering_primary(self) -> bool:
        """One-way validation from Peer 1 to Peer 2."""
        return self._validate(
            local=self.bgp_peer_one,
            remote=self.bgp_peer_two,
            l_as=self._to_int_str(getattr(self, "peer_one_as", None)),
            r_as=self._to_int_str(getattr(self, "peer_two_as", None)),
            vrf_override=getattr(self, "peer_one_vrf", None),
        )

    @depends_on("test_peering_primary")
    def test_peering_secondary(self) -> bool:
        """Validates back from Peer 2 to Peer 1 only if Type is Two-Way."""
        if self.two_way_check != "Two-Way-Check":
            return True

        return self._validate(
            local=self.bgp_peer_two,
            remote=self.bgp_peer_one,
            l_as=self._to_int_str(getattr(self, "peer_two_as", None)),
            r_as=self._to_int_str(getattr(self, "peer_one_as", None)),
            vrf_override=getattr(self, "peer_two_vrf", None),
        )
