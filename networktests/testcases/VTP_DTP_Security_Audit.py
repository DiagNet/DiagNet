from networktests.testcases.base import DiagNetTest

__author__ = "Danijel Stamenkovic"


class VTP_DTP_Security_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-shield-exclamation fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">VTP &amp; DTP Security Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">VLAN Security</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits the security posture of legacy VLAN management protocols. It validates that
                        VTP is operating in the expected mode (Transparent, Off, Client, or Server) to prevent
                        unauthorized VLAN database propagation, and checks that DTP negotiation is completely
                        disabled on all switchports to mitigate trunk spoofing attacks.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            A VTP server in an uncontrolled domain can wipe the VLAN database of all connected switches
                            instantly. Active DTP allows an attacker to negotiate a rogue trunk and gain access to all
                            VLANs. Both protocols should be suppressed in production environments.
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
                                <td class="text-body-secondary">The switch to audit for VTP and DTP security</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">required_vtp_mode</td>
                                <td class="text-body-secondary">The expected VTP operating mode: Transparent, Off, Client, or Server (default: Transparent)</td>
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
            "description": "The switch to audit for VTP/DTP security compliance.",
            "requirement": "required",
        },
        {
            "name": "required_vtp_mode",
            "display_name": "Required VTP Mode",
            "type": "choice",
            "choices": ["Transparent", "Off", "Client", "Server"],
            "default_choice": "Transparent",
            "description": "The operational VTP mode the device must be running.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)

    def test_vtp_mode_operational(self):
        """Verifies VTP is running in the required mode."""
        expected = getattr(self, "required_vtp_mode", "Transparent").lower()
        out = self.genie_dev.execute("show vtp status")
        if expected not in out.lower():
            raise ValueError(
                f"VTP risk: '{expected.capitalize()}' mode NOT confirmed. Check 'show vtp status'."
            )
        return f"VTP mode '{expected}' verified."

    def test_dtp_global_check(self):
        """Scans connected switchports for active DTP negotiation (skips shutdown/unused ports)."""
        status_out = self.genie_dev.execute("show interfaces status")
        connected = set()
        for line in status_out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and "connected" in line and "notconnect" not in line:
                connected.add(parts[0])

        out = self.genie_dev.execute(
            "show interfaces switchport | include Name:|Negotiation of Trunking"
        )
        negotiating = []
        curr = ""
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Name:"):
                curr = line.split(":", 1)[1].strip()
            elif "Negotiation of Trunking: On" in line and curr:
                if curr in connected:
                    negotiating.append(curr)
        if negotiating:
            raise ValueError(
                f"DTP is active on: {', '.join(negotiating)}. Add 'switchport nonegotiate'."
            )
        return "DTP disabled on all connected switchports."
