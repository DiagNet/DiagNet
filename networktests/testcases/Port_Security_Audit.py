import re
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Port_Security_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-lock fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Port-Security Enforcement Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Port Security</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits port-security on a given access port. It confirms that the feature is
                        enabled, validates that the MAC address limit matches the expected value, and ensures the
                        violation response mode (shutdown, restrict, or protect) aligns with the security policy.
                        All three checks are performed from a single cached command output.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Port-security prevents MAC flooding and unauthorized device connections on access ports.
                            A permissive MAC limit or a 'protect' violation mode allows an attacker to silently inject
                            traffic without triggering any alerts.
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
                                <td class="text-body-secondary">The access port to audit for port-security configuration</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">max_mac_addresses</td>
                                <td class="text-body-secondary">Expected maximum number of allowed MAC addresses (default: 1)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">violation_mode</td>
                                <td class="text-body-secondary">Required violation response: shutdown, restrict, or protect (default: shutdown)</td>
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
            "description": "The switch that owns the access port to audit.",
            "requirement": "required",
        },
        {
            "name": "interface",
            "display_name": "Access Port Interface",
            "type": "cisco-interface",
            "description": "The access-mode interface to audit for port-security.",
            "requirement": "required",
        },
        {
            "name": "max_mac_addresses",
            "display_name": "Max MAC Addresses",
            "type": "positive-number",
            "default": 1,
            "description": "The exact maximum MAC address count that must be configured.",
            "requirement": "optional",
        },
        {
            "name": "violation_mode",
            "display_name": "Violation Mode",
            "type": "choice",
            "choices": ["shutdown", "restrict", "protect"],
            "default_choice": "shutdown",
            "description": "The required response when a violation is detected.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.full_int = self.interface
        self._ps_out = self.genie_dev.execute(
            f"show port-security interface {self.full_int}"
        )

    def test_port_security_operational(self):
        """Verifies port-security is enabled on the interface."""
        if not re.search(r"Port Security\s*:\s*Enabled", self._ps_out, re.I):
            raise ValueError(
                f"Port-Security NOT enabled on {self.full_int}. Add 'switchport port-security'."
            )
        return f"Port-Security is active on {self.full_int}."

    @depends_on("test_port_security_operational")
    def test_max_mac_consistency(self):
        """Validates the configured MAC address limit."""
        exp = int(getattr(self, "max_mac_addresses", 1))
        m = re.search(r"Maximum MAC Addresses\s+:\s+(\d+)", self._ps_out)
        if not m:
            raise ValueError("Could not parse 'Maximum MAC Addresses' from output.")
        actual = int(m.group(1))
        if actual != exp:
            raise ValueError(
                f"MAC limit mismatch: configured {actual}, expected {exp}."
            )
        return f"MAC address limit of {actual} verified."

    @depends_on("test_port_security_operational")
    def test_violation_policy(self):
        """Validates the configured violation response mode."""
        exp = getattr(self, "violation_mode", "shutdown").lower()
        m = re.search(r"Violation Mode\s+:\s+(\w+)", self._ps_out)
        if not m:
            raise ValueError("Could not parse 'Violation Mode' from output.")
        actual = m.group(1).lower()
        if actual != exp:
            raise ValueError(
                f"Violation mode mismatch: configured '{actual}', expected '{exp}'."
            )
        return f"Violation mode '{actual}' correctly configured."
