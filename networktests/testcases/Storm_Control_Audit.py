import re
from networktests.testcases.base import DiagNetTest

__author__ = "Danijel Stamenkovic"


class Storm_Control_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-lightning-charge fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Storm-Control Suppression Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Traffic Hygiene</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits storm-control on a specified interface. It verifies that the broadcast
                        suppression threshold does not exceed the configured maximum, preventing a broadcast storm
                        from saturating the uplink. It also checks whether a shutdown or trap action is configured
                        for violation events.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Unconstrained broadcast traffic from a misconfigured or compromised endpoint can consume
                            100% of available bandwidth within milliseconds. Storm-control is the last line of defense
                            at the hardware forwarding plane.
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
                                <td class="text-body-secondary">The switch hosting the interface</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The interface to audit for storm-control thresholds</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">broadcast_threshold</td>
                                <td class="text-body-secondary">Maximum allowed broadcast level as a percentage (default: 10.0)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">action_shutdown</td>
                                <td class="text-body-secondary">Set True to require a shutdown action on violation (default: False)</td>
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
            "description": "The switch that owns the interface to audit.",
            "requirement": "required",
        },
        {
            "name": "interface",
            "display_name": "Interface",
            "type": "cisco-interface",
            "description": "The switchport interface to check for storm-control configuration.",
            "requirement": "required",
        },
        {
            "name": "broadcast_threshold",
            "display_name": "Broadcast Threshold (%)",
            "type": "str",
            "default": "10.0",
            "description": "Maximum permissible broadcast suppression level as a percentage (e.g. 10.0).",
            "requirement": "optional",
        },
        {
            "name": "action_shutdown",
            "display_name": "Require Shutdown Action",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "False",
            "description": "When True, the audit fails if 'storm-control action shutdown' is not configured.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.full_int = self.interface

    def test_storm_control_broadcast_cfg(self):
        """Verifies the broadcast suppression threshold is within the allowed limit."""
        exp = float(getattr(self, "broadcast_threshold", 10.0))
        # Parse from running-config for cross-platform compatibility (vIOS doesn't support show storm-control <intf> <type>)
        out = self.genie_dev.execute(f"show running-config interface {self.full_int}")
        m = re.search(r"storm-control broadcast level\s+([\d.]+)", out, re.I)
        if not m:
            raise ValueError(
                f"Storm-Control NOT configured on {self.full_int}. Add 'storm-control broadcast level {exp}'."
            )
        actual = float(m.group(1))
        if actual > exp:
            raise ValueError(
                f"Threshold too high: {actual}% exceeds the maximum of {exp}%."
            )
        return f"Broadcast threshold {actual}% is within the {exp}% limit."

    def test_violation_action_standard(self):
        """Checks the configured storm-control violation action."""
        req_sd = str(getattr(self, "action_shutdown", "False")).lower() == "true"
        out = self.genie_dev.execute(f"show running-config interface {self.full_int}")
        has_sd = "storm-control action shutdown" in out
        has_trap = "storm-control action trap" in out
        if req_sd and not has_sd:
            raise ValueError(
                f"Shutdown action required on {self.full_int} but not configured."
            )
        action = "shutdown" if has_sd else ("trap" if has_trap else "filter/default")
        return f"Violation action: '{action}'."
