from devices.models import Device
from networktests.testcases.base import DiagNetTest, depends_on
from typing import Union

__author__ = "Luka Pacar"


class BGP_Session(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm"
         style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e0e6ed; color: #334155;">

        <div style="background: linear-gradient(90deg, #1e293b 0%, #334155 100%); padding: 20px; border-radius: 8px 8px 0 0; margin: -25px -25px 20px -25px;">
            <h2 style="color: #f8fafc; margin: 0; font-weight: 600; letter-spacing: 0.5px;">BGP Session Validation</h2>
            <p style="color: #cbd5e1; margin: 5px 0 0 0; font-size: 0.95rem;">Peer-to-Peer Connectivity & State Verification</p>
        </div>

        <section style="margin-top: 10px;">
            <p>
                The <strong>BGP_Session</strong> test ensures reliable peering between network nodes. It verifies the
                BGP Finite State Machine (FSM) and ensures consistency across Autonomous Systems (AS).
            </p>
        </section>

        <h4 style="color: #0f172a; border-left: 4px solid #3b82f6; padding-left: 10px; margin-top: 25px;">Validation Modes</h4>
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background: #f1f5f9; padding: 15px; border-radius: 6px; border-top: 3px solid #64748b;">
                <strong style="display: block; margin-bottom: 5px; color: #475569;">One-Way Check</strong>
                <span style="font-size: 0.85rem;">Validates that the primary device sees the neighbor in the target state.</span>
            </div>
            <div style="flex: 1; background: #eff6ff; padding: 15px; border-radius: 6px; border-top: 3px solid #3b82f6;">
                <strong style="display: block; margin-bottom: 5px; color: #1d4ed8;">Two-Way Check</strong>
                <span style="font-size: 0.85rem;">Ensures bidirectional establishment by verifying the state from both peers.</span>
            </div>
        </div>

        <h4 style="color: #0f172a; border-left: 4px solid #3b82f6; padding-left: 10px;">Verification Pillars</h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #10b981; margin-right: 10px;">✔</span>
                <span><strong>FSM State Accuracy:</strong> Confirms the session has reached <code>Established</code>.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #10b981; margin-right: 10px;">✔</span>
                <span><strong>AS Integrity:</strong> Matches Local and Remote AS numbers to prevent configuration errors.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #10b981; margin-right: 10px;">✔</span>
                <span><strong>Multi-Context Awareness:</strong> Full support for <strong>VRF Overrides</strong>.</span>
            </li>
        </ul>

        <h4 style="color: #0f172a; border-left: 4px solid #3b82f6; padding-left: 10px; margin-top: 25px;">Why It Matters</h4>
        <p style="background: #fffbeb; border: 1px solid #fef3c7; padding: 15px; border-radius: 6px; font-size: 0.9rem; color: #92400e;">
            <strong>Crucial for Redundancy:</strong> This test identifies "half-open" sessions that look "Up" on one side but
            stuck in "Connect" on the other, preventing silent traffic blackholes.
        </p>

        <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 20px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 10px;">
            Authored by: Luka Pacar
        </p>
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
