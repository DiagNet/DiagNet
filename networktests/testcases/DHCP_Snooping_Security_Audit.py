import re
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class DHCP_Snooping_Security_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-hdd-network fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">DHCP Snooping Security Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">DHCP Security</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test validates the DHCP Snooping configuration on the switch. It confirms that the
                        feature is globally active, verifies that all required VLANs are protected against rogue
                        DHCP server injection, and checks whether the snooping binding database is populated with
                        active lease entries.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            A rogue DHCP server can assign itself as the default gateway to all clients, enabling a
                            man-in-the-middle attack on the entire VLAN. DHCP Snooping is the prerequisite for
                            Dynamic ARP Inspection and IP Source Guard.
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
                                <td class="text-body-secondary">The switch to audit for DHCP Snooping coverage</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">protected_vlans <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Comma-separated VLAN IDs that must be protected by DHCP Snooping</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">trusted_interfaces</td>
                                <td class="text-body-secondary">Comma-separated interfaces that are DHCP trusted uplinks (informational)</td>
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
            "description": "The switch to audit for DHCP Snooping.",
            "requirement": "required",
        },
        {
            "name": "protected_vlans",
            "display_name": "Protected VLANs",
            "type": "str",
            "description": "Comma-separated list of VLAN IDs that must be snooping-enabled (e.g. 10,20,99).",
            "requirement": "required",
        },
        {
            "name": "trusted_interfaces",
            "display_name": "Trusted Interfaces",
            "type": "str",
            "description": "Optional: Comma-separated interfaces configured as DHCP trusted ports.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self._snooping_out = self.genie_dev.execute("show ip dhcp snooping")

    def test_snooping_global_activation(self):
        """Confirms DHCP Snooping is globally enabled."""
        if not re.search(r"switch DHCP snooping is enabled", self._snooping_out, re.I):
            raise ValueError(
                "DHCP Snooping NOT globally enabled. Add 'ip dhcp snooping'."
            )
        return "Global DHCP Snooping is active."

    @depends_on("test_snooping_global_activation")
    def test_vlan_coverage_verification(self):
        """Confirms all required VLANs are covered by DHCP Snooping."""
        req = [v.strip() for v in self.protected_vlans.split(",")]
        missing = [v for v in req if not re.search(rf"\b{v}\b", self._snooping_out)]
        if missing:
            raise ValueError(
                f"VLANs {', '.join(missing)} are NOT protected. Add 'ip dhcp snooping vlan {','.join(missing)}'."
            )
        return f"VLANs {self.protected_vlans} are all covered by DHCP Snooping."

    def test_binding_db_operational(self):
        """Checks whether the snooping binding database contains active entries."""
        out = self.genie_dev.execute("show ip dhcp snooping binding")
        if len(out.strip().splitlines()) > 2:
            return "DHCP Snooping binding database is populated."
        return "Warning: Binding database is empty. This is normal on a fresh device with no active clients."
