import re
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Switchport_Trunk_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-diagram-3 fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Switchport Trunk Integrity Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Trunk / L2 Switching</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test performs a comprehensive audit of a trunk interface. It verifies that the port is
                        operationally trunking using 802.1Q encapsulation, validates that the native VLAN is explicitly
                        set to a non-default, non-VLAN-1 value to prevent VLAN hopping attacks, and confirms that
                        a specific set of required VLANs is present in the allowed list.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            A trunk using the default native VLAN (1) is vulnerable to VLAN hopping. Pruning the allowed
                            VLAN list prevents the propagation of unnecessary broadcast domains across backbone links,
                            reducing the attack surface and improving convergence time.
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
                                <td class="text-body-secondary">The switch on which the trunk interface resides</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The trunk interface to audit (e.g. GigabitEthernet0/1)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_native_vlan</td>
                                <td class="text-body-secondary">The expected native VLAN ID. Must not be VLAN 1 (default: 999)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">required_vlans</td>
                                <td class="text-body-secondary">Comma-separated list of VLANs that must appear in the allowed list</td>
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
                <span class="badge bg-primary bg-opacity-10 text-primary-emphasis border border-primary border-opacity-10 rounded-pill px-3 py-1">Danijel Stamenkovic</span>
            </div>
        </div>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "Target Switch",
            "type": "device",
            "description": "The switch that owns the trunk interface.",
            "requirement": "required",
        },
        {
            "name": "interface",
            "display_name": "Trunk Interface",
            "type": "cisco-interface",
            "description": "The interface to audit (e.g. GigabitEthernet0/1 or Port-Channel1).",
            "requirement": "required",
        },
        {
            "name": "expected_native_vlan",
            "display_name": "Expected Native VLAN",
            "type": "positive-number",
            "default": 999,
            "description": "The non-default native VLAN ID configured for VLAN hopping prevention.",
            "requirement": "optional",
        },
        {
            "name": "required_vlans",
            "display_name": "Required Allowed VLANs",
            "type": "str",
            "description": "Comma-separated VLAN IDs that must be present in the trunk's allowed list.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.full_int = self.interface
        self._sp_out = self.genie_dev.execute(
            f"show interfaces {self.full_int} switchport"
        )

    def test_trunk_operational_status(self):
        """Verifies the interface is operationally trunking."""
        m = re.search(r"Operational Mode:\s+(\S+)", self._sp_out)
        mode = m.group(1).lower() if m else "unknown"
        if "trunk" not in mode:
            raise ValueError(
                f"Interface {self.full_int} is in '{mode}' mode, expected 'trunk'."
            )
        return f"Interface {self.full_int} is operationally trunking."

    @depends_on("test_trunk_operational_status")
    def test_native_vlan_integrity(self):
        """Validates native VLAN is not VLAN 1 and matches expected value."""
        expected = str(getattr(self, "expected_native_vlan", 999))
        m = re.search(r"Trunking Native Mode VLAN:\s+(\d+)", self._sp_out)
        if not m:
            raise ValueError(
                f"Could not parse native VLAN from 'show interfaces {self.full_int} switchport' output."
            )
        actual = m.group(1)
        if actual == "1":
            raise ValueError(
                f"CRITICAL: VLAN 1 is the native VLAN on {self.full_int}. VLAN hopping risk!"
            )
        if actual != expected:
            raise ValueError(
                f"Native VLAN mismatch on {self.full_int}: found {actual}, expected {expected}."
            )
        return f"Native VLAN {actual} correctly configured."

    @depends_on("test_trunk_operational_status")
    def test_allowed_vlans(self):
        """Validates required VLANs are present in the allowed list."""
        required_str = getattr(self, "required_vlans", None)
        if not required_str:
            return "No required VLANs specified, check skipped."

        out = self.genie_dev.execute(f"show running-config interface {self.full_int}")
        m = re.search(r"switchport trunk allowed vlan ([\d,\-]+)", out)
        if not m:
            raise ValueError(
                "Could not parse 'switchport trunk allowed vlan' from running config."
            )

        actual_allowed = m.group(1)
        required_vlans = [v.strip() for v in required_str.split(",")]
        missing = [
            v
            for v in required_vlans
            if not self._vlan_in_allowed_list(v, actual_allowed)
        ]

        if missing:
            raise ValueError(
                f"VLANs {', '.join(missing)} are NOT in the allowed list on {self.full_int}."
            )
        return f"All required VLANs ({required_str}) are permitted on the trunk."

    def _vlan_in_allowed_list(self, vlan, allowed_list_str):
        parts = allowed_list_str.split(",")
        vlan = vlan.strip()
        if not vlan.isdigit():
            raise ValueError(f"Invalid VLAN ID '{vlan}' in required_vlans list.")
        target = int(vlan)
        for part in parts:
            if "-" in part:
                s, e = map(int, part.split("-"))
                if s <= target <= e:
                    return True
            elif part.isdigit() and int(part) == target:
                return True
        return False
