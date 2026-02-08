from typing import List, Set

from devices.models import Device
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class MPLS(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-indigo text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #4f46e5;">
                    <i class="bi bi-shuffle fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">MPLS</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white bg-opacity-75 border border-opacity-25" style="background-color: #4338ca; border-color: #4338ca;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">MPLS / L2.5 Switching</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks the status of the Label Distribution Protocol (LDP) on your device.
                        It confirms that MPLS is enabled and working on specific interfaces and that LDP sessions with neighbors are fully established.
                    </p>

                    <div class="p-3 rounded border border-opacity-25 bg-indigo bg-opacity-10" style="border-color: #4f46e5;">
                        <h6 class="fw-bold mb-1" style="color: #4f46e5;">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures that label switching is active and that routers are correctly exchanging labels.
                        </p>
                    </div>
                </div>
            </div>

            <div class="mb-2">
                <h6 class="text-uppercase text-body-secondary fw-bold small border-bottom border-opacity-10 pb-2 mb-0">Configuration Parameters</h6>
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="small text-uppercase text-body-tertiary">
                            <tr>
                                <th scope="col" style="width: 35%;">Name</th>
                                <th scope="col">Description</th>
                            </tr>
                        </thead>
                        <tbody class="small text-body">
                            <tr>
                                <td class="fw-bold font-monospace">device <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The MPLS Router</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF Context</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">mpls_interfaces</td>
                                <td class="text-body-secondary">List of interfaces that must have MPLS enabled</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Interface Name</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">ldp_neighbors</td>
                                <td class="text-body-secondary">List of expected LDP Neighbors</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ neighbor_device <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">The neighbor Device Object</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="mt-2 text-end">
                    <small class="text-danger opacity-75" style="font-size: 0.75rem;">* Required field</small>
                </div>
            </div>

            <div class="mt-4 pt-3 border-top border-opacity-10 d-flex justify-content-end align-items-center">
                <span class="small text-uppercase fw-bold text-body-secondary me-2" style="font-size: 0.7rem; letter-spacing: 0.5px;">Authored by</span>
                <span class="badge bg-primary bg-opacity-10 text-primary-emphasis border border-primary border-opacity-10 rounded-pill px-3 py-1">Luka Pacar</span>
            </div>
        </div>
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
                "Interface validation failed: 'show mpls interfaces' returned no data."
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

            if not possible_ips:
                errors.append(
                    f"Cannot validate LDP session to '{target_device.name}': device has no configured IP addresses."
                )
                continue
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
