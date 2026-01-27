import re
from typing import Any, Dict, List

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class DMVPN(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #374151 0%, #111827 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #6366f1;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">DMVPN</h2>
            <p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Device-Centric Tunnel Validation</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>DMVPN_Connectivity</strong> test performs an end-to-end validation of mGRE tunnels.
                It leverages <strong>Device Objects</strong> to verify registration status on the DUT without exposing sensitive IP data in reports.
            </p>
        </section>

        <h4 style="color: #111827; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #6366f1; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Capabilities
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #6366f1; margin-right: 10px;">✔</span>
                <span><strong>Secure Validation:</strong> Verifies connectivity using resolved WAN identifiers while sanitizing error outputs.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #6366f1; margin-right: 10px;">✔</span>
                <span><strong>Role Awareness:</strong> Adapts validation logic for <strong>Hub</strong> (expecting dynamic peers) and <strong>Spoke</strong> (expecting static Hub connection).</span>
            </li>
        </ul>
    </div>
    """

    _params: List[Dict[str, Any]] = [
        {
            "name": "device",
            "display_name": "DMVPN Device (DUT)",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "VRF Context",
            "type": "str",
            "default": "default",
            "requirement": "optional",
        },
        {
            "name": "role",
            "display_name": "Device Role",
            "type": "choice",
            "choices": ["Hub", "Spoke"],
            "default_choice": "Spoke",
            "description": "Defines the validation logic.",
            "requirement": "required",
        },
        {
            "name": "expected_spokes",
            "display_name": "Expected Spokes (Hub Only)",
            "type": "list",
            "description": "List of Spoke devices that must be connected.",
            "requirement": "optional",
            "required_if": {"role": "Hub"},
            "parameters": [
                {
                    "name": "spoke_device",
                    "display_name": "Spoke Device",
                    "type": "device",
                    "description": "The Spoke Device object.",
                    "requirement": "required",
                },
                {
                    "name": "wan_interface",
                    "display_name": "WAN Interface",
                    "type": "cisco-interface",
                    "description": "The interface holding the NBMA IP (e.g. Gig0/0).",
                    "requirement": "required",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
        {
            "name": "hub_connection",
            "display_name": "Hub Connection (Spoke Only)",
            "type": "list",
            "description": "Details of the Hub this Spoke must connect to.",
            "requirement": "optional",
            "required_if": {"role": "Spoke"},
            "parameters": [
                {
                    "name": "hub_device",
                    "display_name": "Hub Device",
                    "type": "device",
                    "description": "The Hub Device object.",
                    "requirement": "required",
                },
                {
                    "name": "wan_interface",
                    "display_name": "WAN Interface",
                    "type": "cisco-interface",
                    "description": "The interface holding the NBMA IP on the Hub.",
                    "requirement": "required",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
    ]

    def _get_ip_from_device(self, target_dev: Any, interface_name: str) -> str:
        # Connectivity Check
        if not target_dev.can_connect():
            raise ValueError(
                f"Connection Error: Unable to connect to peer device '{target_dev.name}'."
            )

        # Command Execution
        cmd = f"show ip interface brief {interface_name}"
        try:
            output = target_dev.get_genie_device_object().execute(cmd)

            # Regex IP Extraction
            match = re.search(
                r"{}\s+(?P<ip>[0-9.]+)\s+".format(re.escape(interface_name)), output
            )
            if not match:
                match = re.search(
                    r"\s+(?P<ip>[0-9]{1,3}(?:\.[0-9]{1,3}){3})\s+", output
                )

            if match:
                return match.group("ip")

            raise ValueError("Pattern mismatch")

        except Exception:
            # Sanitized Error Handling
            raise ValueError(
                f"Resolution Failed: Could not resolve WAN identifier for '{interface_name}' on device '{target_dev.name}'."
            )

    def _parse_dmvpn_output(self, raw_output: str) -> Dict[str, Dict[str, str]]:
        # Input Validation
        parsed_peers = {}
        if not raw_output or "Invalid input" in raw_output:
            return {}

        # Regex Parsing Loop
        pattern = re.compile(
            r"^\s*\d+\s+(?P<nbma>[0-9.]+)\s+(?P<tunnel>[0-9.]+)\s+(?P<state>\w+)\s+[\d:]+\s+(?P<attr>\w+)"
        )

        for line in raw_output.splitlines():
            match = pattern.search(line)
            if match:
                data = match.groupdict()
                parsed_peers[data["nbma"]] = {
                    "state": data["state"].upper(),
                    "type": "static" if "S" in data["attr"] else "dynamic",
                }
        return parsed_peers

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(
                f"Critical: Unable to connect to main DUT '{self.device.name}'."
            )
        return True

    @depends_on("test_device_connection")
    def test_resolve_peer_ips(self) -> bool:
        # Setup & Input Selection
        self.resolved_targets: List[Dict[str, Any]] = []
        role = getattr(self, "role", "Spoke")

        raw_inputs = (
            getattr(self, "expected_spokes", [])
            if role == "Hub"
            else getattr(self, "hub_connection", [])
        )

        if not raw_inputs:
            return True

        # Peer Resolution Loop
        for entry in raw_inputs:
            dev_obj = entry.get("spoke_device") or entry.get("hub_device")
            wan_int = entry.get("wan_interface")

            if not dev_obj or not wan_int:
                continue

            try:
                resolved_ip = self._get_ip_from_device(dev_obj, wan_int)
                target_data = {
                    "name": dev_obj.name,
                    "nbma_ip": resolved_ip,
                }
                self.resolved_targets.append(target_data)
            except ValueError:
                raise

        return True

    @depends_on("test_resolve_peer_ips")
    def test_fetch_dmvpn_table(self) -> bool:
        # Command Preparation
        vrf = getattr(self, "vrf", "default") or "default"
        cmd = "show dmvpn"
        if vrf != "default":
            cmd = f"show dmvpn vrf {vrf}"

        # Execution & Parsing
        try:
            raw_output = self.device.get_genie_device_object().execute(cmd)
            self.peers_table = self._parse_dmvpn_output(raw_output)
        except Exception:
            raise ValueError(
                f"Execution Error: Failed to retrieve DMVPN table on '{self.device.name}'."
            )

        return True

    @depends_on("test_fetch_dmvpn_table")
    def test_validate_peers(self) -> bool:
        # Prerequisite Check
        if not hasattr(self, "resolved_targets") or not self.resolved_targets:
            return True

        errors: List[str] = []
        role = getattr(self, "role", "Spoke")

        # Validation Loop
        for target in self.resolved_targets:
            nbma = target["nbma_ip"]
            name = target["name"]

            # Check 1: Existence
            if nbma not in self.peers_table:
                errors.append(
                    f"[{role} Mode] Peer '{name}' is MISSING from the DMVPN table. "
                    "Verify tunnel status and routing reachability."
                )
                continue

            # Check 2: State
            peer_data = self.peers_table[nbma]
            current_state = peer_data["state"]

            if current_state != "UP":
                errors.append(
                    f"[{role} Mode] Peer '{name}' is in unexpected state '{current_state}' (Expected: 'UP'). "
                    "Check IKE/IPsec or NHRP registration."
                )

        if errors:
            raise ValueError("\n".join(errors))

        return True
