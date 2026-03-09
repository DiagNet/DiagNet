import re
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class SVI_Management_Hardening_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-hdd-stack fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">SVI &amp; Management Plane Hardening Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Management Security</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits the management plane hardening of the switch. It verifies that the
                        management SVI is operationally up and reachable, then confirms that the VTY lines
                        are hardened to SSH-only access. Optionally, it validates that an inbound ACL is
                        applied to the management SVI to restrict which hosts may initiate management sessions.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Telnet transmits credentials in plaintext and must never be permitted on
                            production management infrastructure. An exposed management SVI without an
                            inbound ACL allows any host on the management VLAN to initiate SSH sessions,
                            significantly widening the attack surface for brute-force attempts.
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
                                <td class="text-body-secondary">The switch to audit for management plane security</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">management_vlan <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The VLAN ID of the management SVI (e.g. 99)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_mtu</td>
                                <td class="text-body-secondary">Expected MTU on the management SVI in bytes (default: 1500)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">require_inbound_acl</td>
                                <td class="text-body-secondary">Fail if no inbound ACL is applied to the management SVI (default: True)</td>
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
            "description": "The switch to audit for SVI and management plane hardening.",
            "requirement": "required",
        },
        {
            "name": "management_vlan",
            "display_name": "Management VLAN",
            "type": "positive-number",
            "description": "The VLAN ID of the management SVI that must be operational (e.g. 99).",
            "requirement": "required",
        },
        {
            "name": "expected_mtu",
            "display_name": "Expected MTU",
            "type": "positive-number",
            "default": 1500,
            "description": "The expected MTU value on the management SVI interface.",
            "requirement": "optional",
        },
        {
            "name": "require_inbound_acl",
            "display_name": "Require Inbound ACL",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "True",
            "description": "When True, fails if no inbound access-list is applied to the management SVI.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        v = self.management_vlan
        self._svi_out = self.genie_dev.execute(f"show interfaces vlan {v}")
        self._vty_out = self.genie_dev.execute("show running-config | section line vty")

    def test_svi_operational_readiness(self):
        """Verifies the management SVI is fully up and passing traffic."""
        v = self.management_vlan
        if f"Vlan{v} is up, line protocol is up" in self._svi_out:
            exp_mtu = int(getattr(self, "expected_mtu", 1500))
            m = re.search(r"MTU\s+(\d+)", self._svi_out)
            if m and int(m.group(1)) != exp_mtu:
                return f"Warning: SVI Vlan{v} is Up/Up but MTU is {m.group(1)}, expected {exp_mtu}."
            return f"Management SVI Vlan{v} is Up/Up."
        raise ValueError(
            f"Management SVI Vlan{v} is NOT Up/Up. "
            f"Verify 'interface vlan {v}' exists and is not shutdown."
        )

    @depends_on("test_svi_operational_readiness")
    def test_vty_ssh_only_enforcement(self):
        """Confirms VTY lines are restricted to SSH; Telnet must not be permitted."""
        if "transport input telnet" in self._vty_out.lower():
            raise ValueError(
                "Telnet is permitted on VTY lines — plaintext credential exposure risk. "
                "Replace with 'transport input ssh'."
            )
        return "VTY lines are hardened to SSH-only access."

    @depends_on("test_svi_operational_readiness")
    def test_management_svi_acl(self):
        """Validates that an inbound ACL is applied to the management SVI."""
        if str(getattr(self, "require_inbound_acl", "True")).lower() != "true":
            return "Inbound ACL check skipped (require_inbound_acl=False)."
        v = self.management_vlan
        if re.search(r"ip access-group\s+\S+\s+in", self._svi_out, re.I):
            m = re.search(r"ip access-group\s+(\S+)\s+in", self._svi_out, re.I)
            return f"Inbound ACL '{m.group(1)}' applied to management SVI Vlan{v}."
        # Also check running-config for the SVI
        rc = self.genie_dev.execute(f"show running-config interface vlan {v}")
        m = re.search(r"ip access-group\s+(\S+)\s+in", rc, re.I)
        if m:
            return f"Inbound ACL '{m.group(1)}' applied to management SVI Vlan{v}."
        raise ValueError(
            f"No inbound ACL on management SVI Vlan{v}. "
            f"Apply with 'ip access-group <ACL-NAME> in' under 'interface vlan {v}'."
        )
