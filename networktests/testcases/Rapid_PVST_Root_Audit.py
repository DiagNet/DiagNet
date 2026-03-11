import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Rapid_PVST_Root_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-bezier fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Rapid-PVST Root Bridge Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">STP / L2 Switching</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test validates the Spanning Tree Protocol topology for a specific VLAN. It first confirms
                        that Rapid-PVST+ is the active STP mode on the switch, then verifies whether the device is
                        or is not the Root Bridge for the target VLAN. This ensures that root bridge placement aligns
                        with the intended network design.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            An unintended root bridge (e.g. a misconfigured access switch) creates suboptimal traffic
                            paths and can bring down entire VLANs during convergence. This test enforces deterministic,
                            design-driven STP topology control.
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
                                <td class="text-body-secondary">The switch to evaluate for Root Bridge status</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vlan_id <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The VLAN ID for which the STP topology is checked</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">should_be_root <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Whether this switch is expected to be the Root Bridge for this VLAN</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_priority</td>
                                <td class="text-body-secondary">Optional: The expected STP bridge priority value (default: 32768)</td>
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
            "description": "The switch to check for STP Root Bridge status.",
            "requirement": "required",
        },
        {
            "name": "vlan_id",
            "display_name": "VLAN ID",
            "type": "positive-number",
            "description": "The VLAN instance to inspect (e.g. 10, 20, 99).",
            "requirement": "required",
        },
        {
            "name": "should_be_root",
            "display_name": "Should Be Root Bridge",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "True",
            "description": "Set True if this switch must be the Root Bridge, False if it must not be.",
            "requirement": "required",
        },
        {
            "name": "expected_priority",
            "display_name": "Expected Priority",
            "type": "positive-number",
            "default": 32768,
            "description": "Optional: The expected bridge priority value for informational checking.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)

    def test_stp_mode_rapid(self):
        """Verifies Rapid-PVST+ is the active STP mode."""
        out = self.genie_dev.execute("show spanning-tree summary")
        if "rapid-pvst" not in out.lower():
            raise ValueError(
                "Rapid-PVST+ is NOT active on this switch. Check 'spanning-tree mode rapid-pvst'."
            )
        return "Rapid-PVST+ confirmed active."

    @depends_on("test_stp_mode_rapid")
    def test_root_bridge_role(self):
        """Validates whether this switch is the Root Bridge for the target VLAN."""
        vlan = self.vlan_id
        should_root = str(getattr(self, "should_be_root", "True")).lower() == "true"
        out = self.genie_dev.execute(f"show spanning-tree vlan {vlan}")
        is_root = "this bridge is the root" in out.lower()
        if should_root and not is_root:
            raise ValueError(
                f"Switch is NOT the Root Bridge for VLAN {vlan}. Verify 'spanning-tree vlan {vlan} root primary'."
            )
        if not should_root and is_root:
            raise ValueError(
                f"Switch IS the Root Bridge for VLAN {vlan} (suboptimal). Verify STP priority configuration."
            )
        expected_prio = getattr(self, "expected_priority", None)
        prio_msg = ""
        if expected_prio is not None:
            m = re.search(r"Bridge ID\s+Priority\s+(\d+)", out)
            if m:
                actual_prio = int(m.group(1))
                if actual_prio != int(expected_prio):
                    prio_msg = f" Warning: bridge priority is {actual_prio}, expected {expected_prio}."
                else:
                    prio_msg = f" Bridge priority {actual_prio} matches expected."
        return f"STP role for VLAN {vlan} is correct: {'Root Bridge' if is_root else 'Non-Root'}.{prio_msg}"
