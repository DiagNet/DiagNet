import re
from typing import Any, Dict, List

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class DMVPN(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-cloud-check-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">DMVPN</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-info text-dark bg-opacity-75 border border-info border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">WAN / Overlay</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks your DMVPN network to ensure the Hub and Spokes are connected.
                        It verifies that the secure tunnels are active and that devices are registered correctly with each other.
                    </p>

                    <div class="p-3 rounded border border-info border-opacity-25 bg-info bg-opacity-10">
                        <h6 class="fw-bold text-primary-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures branch sites are online and can communicate securely with the main site.
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
                                <td class="text-body-secondary">The DMVPN Device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">role <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Device Role: Hub or Spoke</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF Context. Default is default</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_spokes</td>
                                <td class="text-body-secondary">List of Spoke devices. Hub Mode only</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ spoke_device</td>
                                <td class="text-body-secondary fst-italic">The remote Spoke Device object</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">hub_connection</td>
                                <td class="text-body-secondary">Hub connection details. Spoke Mode only</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ hub_device</td>
                                <td class="text-body-secondary fst-italic">The remote Hub Device object</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ wan_interface</td>
                                <td class="text-body-secondary fst-italic">Interface with Public IP</td>
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
        if not raw_output:
            # No output from device; treat as no peers discovered.
            return {}
        if "Invalid input" in raw_output:
            # The DMVPN table command is not supported or was entered incorrectly.
            raise ValueError(
                "DMVPN table command is not supported or returned 'Invalid input' on the device."
            )

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
