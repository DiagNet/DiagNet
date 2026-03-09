import re
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Errdisable_Recovery_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-arrow-counterclockwise fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Errdisable Recovery Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Port Recovery</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits the errdisable recovery configuration on the switch. It first scans
                        for any ports currently in the err-disabled state to surface active violations, then
                        validates that automatic recovery is enabled for the required causes (e.g. bpduguard,
                        psecure-violation) and that the recovery interval does not exceed the policy maximum.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Without errdisable recovery, a port disabled by BPDU Guard or port-security stays
                            down permanently until manually re-enabled. In a campus environment this causes
                            invisible outages. Automatic recovery with a bounded interval ensures ports
                            self-heal after transient violations without requiring manual intervention.
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
                                <td class="text-body-secondary">The switch to audit for errdisable recovery configuration</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">check_active_violations</td>
                                <td class="text-body-secondary">When True, fails if any ports are currently in err-disabled state (default: True)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">required_recovery_causes</td>
                                <td class="text-body-secondary">Comma-separated causes that must have recovery enabled (e.g. bpduguard,psecure-violation)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">max_recovery_interval</td>
                                <td class="text-body-secondary">Maximum allowed recovery timer in seconds (default: 300)</td>
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
            "description": "The switch to audit for errdisable recovery state.",
            "requirement": "required",
        },
        {
            "name": "check_active_violations",
            "display_name": "Check Active Violations",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "True",
            "description": "When True, the test fails if any interface is currently in err-disabled state.",
            "requirement": "optional",
        },
        {
            "name": "required_recovery_causes",
            "display_name": "Required Recovery Causes",
            "type": "str",
            "description": "Comma-separated errdisable causes that must have automatic recovery enabled (e.g. bpduguard,psecure-violation).",
            "requirement": "optional",
        },
        {
            "name": "max_recovery_interval",
            "display_name": "Max Recovery Interval (s)",
            "type": "positive-number",
            "default": 300,
            "description": "The recovery timer must not exceed this value in seconds.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self._recovery_out = self.genie_dev.execute("show errdisable recovery")

    def test_active_errdisabled_ports(self):
        """Scans for interfaces currently in err-disabled state."""
        fail_on_found = (
            str(getattr(self, "check_active_violations", "True")).lower() == "true"
        )
        out = self.genie_dev.execute("show interfaces status err-disabled")
        disabled = [
            line.split()[0]
            for line in out.splitlines()
            if "err-disabled" in line.lower()
        ]
        if disabled:
            msg = f"Ports currently err-disabled: {', '.join(disabled)}."
            if fail_on_found:
                raise ValueError(msg)
            return f"Warning: {msg}"
        return "No ports currently in err-disabled state."

    def test_recovery_cause_configuration(self):
        """Validates that automatic recovery is enabled for all required causes."""
        raw = getattr(self, "required_recovery_causes", None)
        if not raw:
            return "No required recovery causes specified — skipping cause check."
        required = [c.strip() for c in raw.split(",")]
        missing = [
            c
            for c in required
            if not re.search(rf"{c}\s+Enabled", self._recovery_out, re.I)
        ]
        if missing:
            cmds = " ".join(f"'errdisable recovery cause {c}'" for c in missing)
            raise ValueError(
                f"Errdisable recovery NOT configured for: {', '.join(missing)}. Add {cmds}."
            )
        return f"Errdisable recovery enabled for: {raw}."

    @depends_on("test_recovery_cause_configuration")
    def test_recovery_interval(self):
        """Verifies the recovery timer does not exceed the policy maximum."""
        max_interval = int(getattr(self, "max_recovery_interval", 300))
        m = re.search(r"Timer interval:\s+(\d+)", self._recovery_out, re.I)
        if not m:
            return "Warning: Could not parse recovery timer interval from output."
        actual = int(m.group(1))
        if actual > max_interval:
            raise ValueError(
                f"Recovery interval {actual}s exceeds maximum {max_interval}s. "
                f"Set with 'errdisable recovery interval {max_interval}'."
            )
        return (
            f"Recovery interval {actual}s is within the {max_interval}s policy limit."
        )
