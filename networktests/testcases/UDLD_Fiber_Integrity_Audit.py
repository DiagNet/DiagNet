from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class UDLD_Fiber_Integrity_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-broadcast fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">UDLD Fiber Link Integrity Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Link Integrity</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits the Unidirectional Link Detection (UDLD) protocol state on a specific
                        interface. It first confirms UDLD is globally enabled on the device, then validates that
                        the target link is in a bidirectional state. Optionally, it enforces that the interface
                        is running in Aggressive mode, which actively disables ports on unidirectional failure.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            A unidirectional fiber failure (TX works, RX does not) is invisible to STP and keeps
                            the port in a forwarding state, creating a black hole. UDLD in Aggressive mode detects
                            this condition and disables the port before a loop forms.
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
                                <td class="text-body-secondary">The switch hosting the fiber uplink</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The fiber interface to check for UDLD state</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">require_aggressive</td>
                                <td class="text-body-secondary">Fail if UDLD is not in Aggressive mode on this interface (default: True)</td>
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
            "description": "The switch owning the fiber interface to audit.",
            "requirement": "required",
        },
        {
            "name": "interface",
            "display_name": "Fiber Interface",
            "type": "cisco-interface",
            "description": "The uplink interface to check for UDLD bidirectional state.",
            "requirement": "required",
        },
        {
            "name": "require_aggressive",
            "display_name": "Require Aggressive Mode",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "True",
            "description": "When True, fails if 'udld port aggressive' is not configured on this interface.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.full_int = self.interface

    def test_udld_operational_global(self):
        """Confirms UDLD is globally enabled on the switch."""
        out = self.genie_dev.execute("show udld")
        if "not enabled" in out.lower():
            raise ValueError(
                "UDLD is not globally enabled on this device. Add 'udld enable'."
            )
        return "UDLD protocol globally enabled."

    @depends_on("test_udld_operational_global")
    def test_udld_interface_state(self):
        """Validates the interface link is bidirectional and optionally in Aggressive mode."""
        req_agg = str(getattr(self, "require_aggressive", "True")).lower() == "true"
        out = self.genie_dev.execute(f"show udld {self.full_int}")
        if "Bidirectional" not in out:
            raise ValueError(
                f"UDLD on {self.full_int} is NOT Bidirectional. Check for fiber RX/TX failure."
            )
        is_agg = "Aggressive" in out
        if req_agg and not is_agg:
            raise ValueError(
                f"UDLD on {self.full_int} is not in Aggressive mode. Add 'udld port aggressive'."
            )
        mode = "Aggressive" if is_agg else "Normal"
        return f"UDLD on {self.full_int} is Bidirectional ({mode} mode)."
