from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class LLDP_CDP_Infrastructure_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #c2410c;">
                    <i class="bi bi-diagram-3 fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">LLDP / CDP Infrastructure Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white" style="background-color: #c2410c;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Topology Discovery</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test audits the Layer 2 discovery protocol state on the device. It first confirms
                        that at least one discovery protocol (LLDP or CDP) is globally active, then validates
                        that an expected neighbor hostname is visible in the neighbor table. LLDP is queried
                        first as the preferred IEEE standard; CDP is used as a fallback.
                    </p>

                    <div class="p-3 rounded" style="border: 1px solid rgba(194,65,12,0.3); background-color: rgba(194,65,12,0.08);">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Discovery protocols provide the ground truth for physical topology verification.
                            A missing neighbor indicates a cabling fault, misconfigured VLAN, or an unexpected
                            device in the path. Confirming both protocol availability and neighbour presence
                            ensures the infrastructure map matches the intended design.
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
                                <td class="text-body-secondary">The switch to audit for discovery protocol neighbors</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">required_neighbor <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Hostname (or partial) of the expected neighbor device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">local_interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The local interface facing the expected neighbor (informational)</td>
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
            "description": "The switch to audit for discovery protocol neighbor state.",
            "requirement": "required",
        },
        {
            "name": "required_neighbor",
            "display_name": "Expected Neighbor",
            "type": "str",
            "description": "Hostname (or partial match) of the neighbor device that must appear in the discovery table.",
            "requirement": "required",
        },
        {
            "name": "local_interface",
            "display_name": "Local Interface",
            "type": "cisco-interface",
            "description": "The local uplink interface facing the expected neighbor (used for context).",
            "requirement": "required",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.full_int = self.local_interface

    def test_global_discovery_operational(self):
        """Confirms at least one discovery protocol is globally active on the switch."""
        out_lldp = self.genie_dev.execute("show lldp")
        out_cdp = self.genie_dev.execute("show cdp")
        lldp_up = "not enabled" not in out_lldp.lower()
        cdp_up = "not enabled" not in out_cdp.lower()
        if not lldp_up and not cdp_up:
            raise ValueError(
                "Neither LLDP nor CDP is globally active. Add 'lldp run' or 'cdp run'."
            )
        active = []
        if lldp_up:
            active.append("LLDP")
        if cdp_up:
            active.append("CDP")
        return f"Discovery protocol(s) active: {', '.join(active)}."

    @depends_on("test_global_discovery_operational")
    def test_neighbor_reachability(self):
        """Validates the expected neighbor appears in the LLDP or CDP neighbor table."""
        target = self.required_neighbor.lower()

        lldp_out = self.genie_dev.execute("show lldp neighbors")
        if target in lldp_out.lower():
            return f"Neighbor '{self.required_neighbor}' verified via LLDP on {self.full_int}."

        try:
            data = self.genie_dev.parse("show cdp neighbors")
            for entry in data.get("cdp", {}).get("index", {}).values():
                if target in entry.get("device_id", "").lower():
                    return f"Neighbor '{self.required_neighbor}' verified via CDP on {self.full_int}."
        except Exception:
            pass

        try:
            cdp_out = self.genie_dev.execute("show cdp neighbors")
            if target in cdp_out.lower():
                return f"Neighbor '{self.required_neighbor}' verified via CDP CLI on {self.full_int}."
        except Exception:
            pass

        raise ValueError(
            f"Neighbor '{self.required_neighbor}' NOT found in LLDP or CDP neighbor table. "
            f"Check cabling and VLAN assignment on {self.full_int}."
        )
