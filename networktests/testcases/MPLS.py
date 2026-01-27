from typing import List, Set

from devices.models import Device
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class MPLS(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #312e81;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">MPLS Core Verification</h2>
            <p style="color: #e0e7ff; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">LDP Adjacency & Interface State Audit</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>MPLS</strong> test class validates the fundamental building blocks of the Label Switching architecture.
                It ensures that the Label Distribution Protocol (LDP) is correctly establishing sessions with peers and that MPLS encapsulation is active on the intended transport interfaces.
            </p>
        </section>

        <h4 style="color: #312e81; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #4f46e5; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Pillars
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #4f46e5; margin-right: 10px;">✔</span>
                <span><strong>Smart Peer Matching:</strong> Automatically identifies LDP neighbors by resolving device objects, eliminating the need to manually lookup LDP Router IDs.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #4f46e5; margin-right: 10px;">✔</span>
                <span><strong>LDP Stability:</strong> Verifies that neighbors are in the <code>Operational</code> state with a fully established TCP session.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #4f46e5; margin-right: 10px;">✔</span>
                <span><strong>Interface Readiness:</strong> Confirms that interfaces are flagged as MPLS-enabled, IP-active, and correctly processing LDP sessions.</span>
            </li>
        </ul>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "MPLS Router",
            "type": "device",
            "description": "The device acting as LSR or LER.",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "VRF Context",
            "type": "str",
            "default": "default",
            "description": "The VRF instance where LDP is running.",
            "requirement": "optional",
        },
        {
            "name": "mpls_interfaces",
            "display_name": "MPLS Interfaces",
            "type": "list",
            "description": "Interfaces that must have MPLS/LDP enabled.",
            "requirement": "optional",
            "parameters": [
                {
                    "name": "interface",
                    "display_name": "Interface Name",
                    "type": "cisco-interface",
                    "requirement": "required",
                }
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
        {
            "name": "ldp_neighbors",
            "display_name": "LDP Neighbors",
            "type": "list",
            "description": "Expected LDP Neighbors (Select the device object).",
            "requirement": "optional",
            "parameters": [
                {
                    "name": "neighbor_device",
                    "display_name": "Neighbor Device",
                    "type": "device",
                    "description": "Select the neighbor device. The test will automatically match it against the LDP Table.",
                    "requirement": "required",
                }
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
    ]

    def _get_clean_peer_id(self, raw_id: str) -> str:
        """Removes label space suffix (e.g. '10.10.10.100:0' -> '10.10.10.100')"""
        return raw_id.split(":")[0].strip()

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(f"Connection failed: {self.device.name}")
        return True

    @depends_on("test_device_connection")
    def test_fetch_telemetry(self) -> bool:
        genie_dev = self.device.get_genie_device_object()

        self.ldp_data = {}
        self.intf_data = {}

        parse_errors = []

        try:
            self.ldp_data = genie_dev.parse("show mpls ldp neighbor detail")
        except Exception as e:
            parse_errors.append(f"LDP Neighbors: {str(e)}")

        try:
            self.intf_data = genie_dev.parse("show mpls interfaces")
        except Exception as e:
            parse_errors.append(f"MPLS Interfaces: {str(e)}")

        # If absolute failure on both commands, we cannot proceed.
        if not self.ldp_data and not self.intf_data:
            raise ValueError(
                f"Telemetry failed. MPLS likely not active. Details: {', '.join(parse_errors)}"
            )

        return True

    @depends_on("test_fetch_telemetry")
    def test_validate_interfaces(self) -> bool:
        # Skip if no interface checks are configured
        if not getattr(self, "mpls_interfaces", None):
            return True

        if not self.intf_data:
            raise ValueError(
                "Skipping interface validation: 'show mpls interfaces' returned no data."
            )

        vrf = getattr(self, "vrf", "default") or "default"

        active_interfaces = (
            self.intf_data.get("vrf", {}).get(vrf, {}).get("interfaces", {})
        )

        errors: List[str] = []

        for entry in self.mpls_interfaces:
            target_intf = entry["interface"]

            if target_intf not in active_interfaces:
                errors.append(
                    f"Interface {target_intf} is missing MPLS configuration or is physically down."
                )
                continue

            intf_details = active_interfaces[target_intf]

            # Validation: IP enabled
            if intf_details.get("ip", "").lower() != "yes":
                errors.append(
                    f"Interface {target_intf} does not have IP processing enabled."
                )

            # Validation: LDP Session
            if intf_details.get("session", "").lower() != "ldp":
                errors.append(
                    f"Interface {target_intf} is not configured for LDP session."
                )

            # Validation: Operational Status
            if intf_details.get("operational", "").lower() != "yes":
                errors.append(f"Interface {target_intf} is not in operational state.")

        if errors:
            raise ValueError("\n".join(errors))

        return True

    @depends_on("test_fetch_telemetry")
    def test_validate_ldp_neighbors(self) -> bool:
        # Skip if no neighbor checks are configured
        if not getattr(self, "ldp_neighbors", None):
            return True

        if not self.ldp_data:
            raise ValueError(
                "LDP neighbor validation failed: 'show mpls ldp neighbor detail' returned no data."
            )

        vrf = getattr(self, "vrf", "default") or "default"

        peers_map = self.ldp_data.get("vrf", {}).get(vrf, {}).get("peers", {})

        normalized_peers = {self._get_clean_peer_id(k): v for k, v in peers_map.items()}

        errors: List[str] = []

        for entry in self.ldp_neighbors:
            target_device: Device = entry["neighbor_device"]

            possible_ips: Set[str] = set()
            if hasattr(target_device, "get_all_ips"):
                possible_ips.update(target_device.get_all_ips())
            if hasattr(target_device, "ip_address") and target_device.ip_address:
                possible_ips.add(str(target_device.ip_address))

            # Try to find a match in the active LDP peers
            found_peer_key = None
            for ip in possible_ips:
                if ip in normalized_peers:
                    found_peer_key = ip
                    break

            if not found_peer_key:
                errors.append(f"LDP Session to '{target_device.name}' not found.")
                continue

            peer_data_root = normalized_peers[found_peer_key]

            if "label_space_id" in peer_data_root:
                label_spaces = peer_data_root["label_space_id"]
                if not label_spaces:
                    errors.append(
                        f"LDP Session to '{target_device.name}' exists but has no detailed status information."
                    )
                    continue
                peer_details = next(iter(label_spaces.values()))
            else:
                peer_details = peer_data_root

            # Validation: State
            actual_state = peer_details.get("state", "unknown").lower()
            peer_state = peer_details.get("peer_state", "unknown").lower()

            if actual_state != "oper":
                errors.append(
                    f"LDP Session with '{target_device.name}' is in state '{actual_state}' (Required: 'oper')."
                )

            if peer_state != "estab":
                errors.append(
                    f"TCP/Adjacency with '{target_device.name}' is '{peer_state}' (Required: 'estab')."
                )

        if errors:
            raise ValueError("\n".join(errors))

        return True
