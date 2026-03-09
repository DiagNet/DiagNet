import re
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Access_Port_Compliance(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-ethernet fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Access Port Compliance Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Access Layer</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test performs a complete compliance check on an access-layer switchport. It verifies that
                        the port is in static access mode, confirms the correct VLAN assignment, and validates that
                        STP edge features (PortFast and BPDU Guard) are active to ensure fast client convergence
                        and protection against rogue switch injection.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            A port in the wrong VLAN silently isolates users from the correct broadcast domain.
                            BPDU Guard on edge ports prevents a client from sending BPDUs to trigger STP topology
                            changes, which could be used to intercept traffic via root bridge spoofing.
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
                                <td class="text-body-secondary">The switch hosting the access port</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The access-layer port to audit</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_vlan <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The VLAN ID that must be assigned to this port</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">require_portfast</td>
                                <td class="text-body-secondary">Fail if PortFast (STP edge) is not active (default: True)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">require_bpduguard</td>
                                <td class="text-body-secondary">Fail if BPDU Guard is not enabled on this port (default: True)</td>
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
            "description": "The switch that owns the access port.",
            "requirement": "required",
        },
        {
            "name": "interface",
            "display_name": "Access Port Interface",
            "type": "cisco-interface",
            "description": "The switchport to audit for access mode compliance.",
            "requirement": "required",
        },
        {
            "name": "expected_vlan",
            "display_name": "Expected VLAN",
            "type": "positive-number",
            "description": "The VLAN ID that must be assigned to this port.",
            "requirement": "required",
        },
        {
            "name": "require_portfast",
            "display_name": "Require PortFast",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "True",
            "description": "Fail the audit if STP PortFast (edge mode) is not active on this port.",
            "requirement": "optional",
        },
        {
            "name": "require_bpduguard",
            "display_name": "Require BPDU Guard",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "True",
            "description": "Fail the audit if BPDU Guard is not enabled on this port.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.full_int = self.interface
        self._sp_out = self.genie_dev.execute(
            f"show interfaces {self.full_int} switchport"
        )

    def test_switchport_mode(self):
        """Verifies the port is in static access mode."""
        if "Administrative Mode: static access" not in self._sp_out:
            m = re.search(r"Administrative Mode:\s+(.*)", self._sp_out)
            mode = m.group(1).strip() if m else "unknown"
            raise ValueError(
                f"Port {self.full_int} is in '{mode}' mode, expected 'static access'."
            )
        return f"Port {self.full_int} is in static access mode."

    @depends_on("test_switchport_mode")
    def test_vlan_assignment(self):
        """Confirms the correct VLAN is assigned to the access port."""
        m = re.search(r"Access Mode VLAN:\s+(\d+)", self._sp_out)
        if not m:
            raise ValueError(
                f"Could not parse 'Access Mode VLAN' from output for {self.full_int}."
            )
        actual = m.group(1)
        if actual != str(self.expected_vlan):
            raise ValueError(
                f"VLAN mismatch on {self.full_int}: assigned {actual}, expected {self.expected_vlan}."
            )
        return f"VLAN {actual} correctly assigned."

    def test_spanning_tree_edge(self):
        """Validates PortFast and BPDU Guard are active on the edge port."""
        out = self.genie_dev.execute(
            f"show spanning-tree interface {self.full_int} detail"
        )
        pf = "portfast" in out.lower() or "edge" in out.lower()
        bg = "bpdu guard is enabled" in out.lower()

        results = []
        if str(getattr(self, "require_portfast", "True")).lower() == "true" and not pf:
            raise ValueError(
                f"PortFast NOT active on {self.full_int}. Add 'spanning-tree portfast'."
            )
        if pf:
            results.append("PortFast OK")

        if str(getattr(self, "require_bpduguard", "True")).lower() == "true" and not bg:
            raise ValueError(
                f"BPDU Guard NOT active on {self.full_int}. Add 'spanning-tree bpduguard enable'."
            )
        if bg:
            results.append("BPDU Guard OK")

        return " / ".join(results) if results else "STP edge checks passed."
