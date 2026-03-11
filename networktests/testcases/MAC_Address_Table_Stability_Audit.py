import re
from networktests.testcases.base import DiagNetTest

__author__ = "Danijel Stamenkovic"


class MAC_Address_Table_Stability_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-table fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">MAC Address Table Stability Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">CAM Health</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits the health of the MAC address table on the switch. It verifies that
                        the CAM aging timer matches the expected value and scans the system log for MAC
                        flapping events, which are a reliable indicator of switching loops or duplicate
                        MAC addresses on the network.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            MAC flapping — where the same MAC address is learned on multiple ports in rapid
                            succession — is a strong signal of a switching loop or a MAC spoofing attack.
                            An incorrect aging timer can cause premature eviction of valid entries, flooding
                            traffic to all ports and degrading performance across the entire VLAN.
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
                                <td class="text-body-secondary">The switch to audit for MAC table stability</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_aging_time</td>
                                <td class="text-body-secondary">Expected MAC aging timer in seconds (default: 300)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">max_mac_count</td>
                                <td class="text-body-secondary">Informational upper bound for total MAC entries (default: 1000)</td>
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
            "description": "The switch to audit for MAC address table health.",
            "requirement": "required",
        },
        {
            "name": "expected_aging_time",
            "display_name": "Expected Aging Time (s)",
            "type": "positive-number",
            "default": 300,
            "description": "The MAC address aging timer in seconds that must be configured on the switch.",
            "requirement": "optional",
        },
        {
            "name": "max_mac_count",
            "display_name": "Max MAC Count",
            "type": "positive-number",
            "default": 1000,
            "description": "Informational ceiling for total dynamic MAC entries; a warning is issued if exceeded.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)

    def test_mac_aging_timer_standard(self):
        """Verifies the CAM aging timer matches the expected value."""
        exp = int(getattr(self, "expected_aging_time", 300))
        out = self.genie_dev.execute("show mac address-table aging-time")
        m = re.search(r"Aging Time:\s+(\d+)", out)
        if not m:
            return "Warning: Could not parse aging timer from output."
        actual = int(m.group(1))
        if actual != exp:
            return f"Warning: Aging timer is {actual}s, expected {exp}s. Set with 'mac address-table aging-time {exp}'."
        return f"MAC aging timer verified at {actual}s."

    def test_mac_count_threshold(self):
        """Warns if total dynamic MAC entries exceed the configured ceiling."""
        max_count = int(getattr(self, "max_mac_count", 1000))
        out = self.genie_dev.execute("show mac address-table count")
        m = re.search(r"Total Mac Addresses for this criterion:\s+(\d+)", out)
        if not m:
            m = re.search(r"Dynamic Address Count\s*:\s*(\d+)", out)
        if not m:
            return "Warning: Could not parse MAC address count from output."
        actual = int(m.group(1))
        if actual > max_count:
            return (
                f"Warning: {actual} dynamic MAC entries exceed threshold of {max_count}. "
                f"Potential CAM table exhaustion or MAC flooding attack."
            )
        return f"MAC table count within limits: {actual}/{max_count} entries."

    def test_mac_flapping_detection(self):
        """Scans the system log for MAC flapping events indicating a loop or spoofing."""
        try:
            out = self.genie_dev.execute("show logging | include MACFLAP|flapping")
        except Exception:
            return "Warning: Could not query logging for MAC flapping events (command not supported on this platform)."
        if "MACFLAP" in out or "flapping" in out.lower():
            raise ValueError(
                "MAC flapping detected in system log. Possible switching loop or MAC spoofing — investigate immediately."
            )
        return "No MAC flapping events detected in system log."
