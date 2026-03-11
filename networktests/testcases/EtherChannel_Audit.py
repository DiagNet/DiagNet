import re
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class EtherChannel_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-stack fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">EtherChannel Consistency &amp; Health Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Link Aggregation</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits the operational health of an EtherChannel (Port-Channel) bundle.
                        It validates that the channel is active and in L2 mode, verifies that the correct
                        aggregation protocol (LACP, PAgP, or Manual) is in use, confirms that a minimum
                        number of member links are in the bundled state, and checks the global hashing algorithm.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            A single misconfigured or inactive bundle member causes asymmetric traffic loss.
                            Verifying LACP negotiation prevents silent blackholing on links that appear physically up
                            but are excluded from the logical channel.
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
                                <td class="text-body-secondary">The switch hosting the Port-Channel bundle</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">channel_group <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The numeric Port-Channel ID to audit (e.g. 1, 2)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_protocol</td>
                                <td class="text-body-secondary">Expected aggregation protocol: LACP, PAgP, or Manual</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">min_active_links</td>
                                <td class="text-body-secondary">Minimum number of bundled member ports required (default: 1)</td>
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
            "description": "The switch that owns the Port-Channel interface.",
            "requirement": "required",
        },
        {
            "name": "channel_group",
            "display_name": "Channel Group ID",
            "type": "positive-number",
            "description": "The numeric identifier of the Port-Channel bundle (e.g. 1).",
            "requirement": "required",
        },
        {
            "name": "expected_protocol",
            "display_name": "Expected Protocol",
            "type": "choice",
            "choices": ["LACP", "PAgP", "Manual"],
            "default_choice": "LACP",
            "description": "The link aggregation protocol that must be negotiating this bundle.",
            "requirement": "optional",
        },
        {
            "name": "min_active_links",
            "display_name": "Min Active Links",
            "type": "positive-number",
            "default": 1,
            "description": "The minimum number of member ports required to be in bundled (P) state.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self._ec_summary = self.genie_dev.execute("show etherchannel summary")

    def test_etherchannel_summary_health(self):
        """Validates the summary status of the Port-Channel bundle."""
        group = self.channel_group
        expected_proto = getattr(self, "expected_protocol", "LACP").lower()
        output = self._ec_summary
        pattern = rf"^{group}\s+Po{group}\((.*?)\)\s+([\w\-]+)\s+(.*)$"
        match = re.search(pattern, output, re.MULTILINE)

        if not match:
            raise ValueError(
                f"Channel-group {group} not found in 'show etherchannel summary'."
            )

        flags, actual_proto = match.group(1), match.group(2).lower()
        if "S" not in flags:
            raise ValueError(f"Po{group} is NOT in L2 mode (Flags: {flags}).")
        if "U" not in flags:
            raise ValueError(f"Po{group} is operationally DOWN (Flags: {flags}).")

        if expected_proto == "manual":
            if (
                "-" not in actual_proto
                and "on" not in actual_proto
                and "none" not in actual_proto
            ):
                raise ValueError(
                    f"Protocol mismatch: expected Manual, found '{actual_proto}'."
                )
        elif expected_proto not in actual_proto:
            raise ValueError(
                f"Protocol mismatch: expected '{expected_proto}', found '{actual_proto}'."
            )

        return f"Port-Channel {group} is UP ({actual_proto}) and In-Use."

    @depends_on("test_etherchannel_summary_health")
    def test_member_port_bundling(self):
        """Verifies member port bundling state and minimum link count."""
        group = self.channel_group
        min_links = int(getattr(self, "min_active_links", 1))
        output = self._ec_summary
        pattern = rf"^{group}\s+Po{group}\(.*?\)\s+[\w\-]+\s+(.*)$"
        match = re.search(pattern, output, re.MULTILINE)
        if not match:
            raise ValueError("Could not extract member ports from summary output.")

        members_raw = match.group(1)
        bundled = re.findall(r"(\S+)\(P\)", members_raw)
        suspended = re.findall(r"(\S+)\([sIHD]\)", members_raw)

        if len(bundled) < min_links:
            raise ValueError(
                f"Insufficient active links: {len(bundled)} bundled, minimum required is {min_links}."
            )

        msg = f"{len(bundled)} port(s) bundled: {', '.join(bundled)}."
        if suspended:
            msg += f" Warning: {len(suspended)} port(s) not bundled: {', '.join(suspended)}."
        return msg

    def test_load_balance_algorithm(self):
        """Checks global load-balancing hashing method."""
        output = self.genie_dev.execute("show etherchannel load-balance")
        output_lower = output.lower()
        if any(
            m in output_lower for m in ["src-dst-ip", "src-dst-port", "src-dst-mac"]
        ):
            return "Optimized hashing active."
        return "Warning: Basic hashing detected. Consider src-dst-ip or src-dst-mac hashing."
