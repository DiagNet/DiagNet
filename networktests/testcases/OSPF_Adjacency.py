import ipaddress

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class OSPF_Adjacency(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-teal text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #0d9488;">
                    <i class="bi bi-bezier2 fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">OSPF Adjacency</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white bg-opacity-75 border border-opacity-25" style="background-color: #0f766e; border-color: #0f766e;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">OSPF / Routing</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks the connection between two OSPF routers.
                        It automatically finds the link connecting them and confirms they are communicating correctly.
                        It also checks that settings like timers match on both sides.
                    </p>

                    <div class="p-3 rounded border border-opacity-25 bg-teal bg-opacity-10" style="border-color: #0d9488;">
                        <h6 class="fw-bold mb-1" style="color: #0d9488;">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures that routers are neighbors and can share network paths without errors.
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
                                <td class="fw-bold font-monospace">device_a <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The first OSPF peer</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">device_b <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The second OSPF peer</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_state <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Target Adjacency State. Example: FULL</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">Default VRF context. Default is default</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">audit_config_consistency</td>
                                <td class="text-body-secondary">Deep audit for Hello/Dead Timers and Network Types</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">area_id</td>
                                <td class="text-body-secondary">Optional: Validate the link belongs to this Area ID</td>
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
                <span class="badge bg-primary bg-opacity-10 text-primary-emphasis border border-primary border-opacity-10 rounded-pill px-3 py-1">Luka Pacar</span>
            </div>
        </div>
    </div>
    """

    _params = [
        {
            "name": "device_a",
            "display_name": "OSPF Peer A",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "device_b",
            "display_name": "OSPF Peer B",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "Default VRF",
            "type": "str",
            "default": "default",
            "requirement": "optional",
        },
        {
            "name": "expected_state",
            "display_name": "Target Adjacency State",
            "type": "choice",
            "choices": [
                "FULL",
                "2-WAY",
                "EXSTART",
                "EXCHANGE",
                "LOADING",
                "INIT",
                "ATTEMPT",
                "DOWN",
            ],
            "default_choice": "FULL",
            "description": "The state both devices should report. Use transitionary states to catch specific hangs.",
            "requirement": "required",
        },
        {
            "name": "audit_config_consistency",
            "display_name": "Deep Config Audit",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Hello/Dead Timers, and Network Types between peers.",
        },
        {
            "name": "area_id",
            "display_name": "Area ID Override",
            "type": "str",
            "requirement": "optional",
            "description": "Optional: Ensures the discovered link belongs to a specific OSPF Area.",
        },
    ]

    def _to_clean_state(self, raw_state):
        return str(raw_state).split("/")[0].strip().upper() if raw_state else "DOWN"

    def _get_vrf_instance(self, raw_data):
        target_vrf = getattr(self, "vrf", "default") or "default"
        return (
            raw_data.get("vrf", {})
            .get(target_vrf, {})
            .get("address_family", {})
            .get("ipv4", {})
            .get("instance", {})
        )

    def _extract_neighbor_map(self, raw_data):
        if not raw_data:
            return {}
        neighbor_map = {}
        for instance in self._get_vrf_instance(raw_data).values():
            for area in instance.get("areas", {}).values():
                for interface in area.get("interfaces", {}).values():
                    for rid, nbr in interface.get("neighbors", {}).items():
                        state = nbr.get("state")
                        if state:
                            neighbor_map[rid] = self._to_clean_state(state)
        return neighbor_map

    def _get_router_id_and_interfaces(self, raw_data):
        router_id = None
        interfaces = {}
        for instance in self._get_vrf_instance(raw_data).values():
            for area_id, area_data in instance.get("areas", {}).items():
                area_ints = area_data.get("interfaces", {})
                for name, details in area_ints.items():
                    details["area_id_found"] = area_id
                    interfaces[name] = details
                    if not router_id:
                        router_id = details.get("router_id")
        return router_id, interfaces

    def test_connectivity(self) -> bool:
        for device in [self.device_a, self.device_b]:
            if not device.can_connect():
                raise ValueError(f"Target {device.name} is unreachable.")
        return True

    @depends_on("test_connectivity")
    def test_discover_shared_link(self) -> bool:
        vrf = getattr(self, "vrf", "default") or "default"
        cmd = (
            "show ip ospf interface"
            if vrf == "default"
            else f"show ip ospf vrf {vrf} interface"
        )

        raw_a = self.device_a.get_genie_device_object().parse(cmd)
        raw_b = self.device_b.get_genie_device_object().parse(cmd)

        self.rid_a, ints_a = self._get_router_id_and_interfaces(raw_a)
        self.rid_b, ints_b = self._get_router_id_and_interfaces(raw_b)

        if not self.rid_a or not self.rid_b:
            raise ValueError(
                f"Could not resolve Router-IDs (A: {self.rid_a}, B: {self.rid_b})"
            )

        found_overlap = False
        for name_a, details_a in ints_a.items():
            if not details_a.get("ip_address"):
                continue
            net_a = ipaddress.ip_interface(details_a["ip_address"]).network

            for name_b, details_b in ints_b.items():
                if not details_b.get("ip_address"):
                    continue
                if net_a == ipaddress.ip_interface(details_b["ip_address"]).network:
                    self.local_int_name_a, self.local_int_name_b = name_a, name_b
                    self.link_data_a, self.link_data_b = details_a, details_b
                    found_overlap = True
                    break
            if found_overlap:
                break

        if not found_overlap:
            raise ValueError(
                "Topology Mismatch: No shared OSPF subnet found between peers."
            )
        return True

    @depends_on("test_discover_shared_link")
    def test_config_audit(self) -> bool:
        if self.audit_config_consistency == "No":
            return True

        errors = []

        # Timers
        h_a, d_a = (
            self.link_data_a.get("hello_interval"),
            self.link_data_a.get("dead_interval"),
        )
        h_b, d_b = (
            self.link_data_b.get("hello_interval"),
            self.link_data_b.get("dead_interval"),
        )
        if h_a != h_b or d_a != d_b:
            errors.append(
                f"Timer Mismatch! {self.device_a.name}: {h_a}/{d_a}, {self.device_b.name}: {h_b}/{d_b}"
            )

        # Area ID
        ar_a, ar_b = (
            self.link_data_a.get("area_id_found"),
            self.link_data_b.get("area_id_found"),
        )
        if ar_a != ar_b:
            errors.append(f"Area Mismatch! Peer A: {ar_a}, Peer B: {ar_b}")
        if getattr(self, "area_id", None) and str(ar_a) != str(self.area_id):
            errors.append(
                f"Area ID Override Failure! Found {ar_a}, Expected {self.area_id}"
            )

        # Network Type
        nt_a, nt_b = (
            self.link_data_a.get("interface_type"),
            self.link_data_b.get("interface_type"),
        )
        if nt_a != nt_b:
            errors.append(f"Network Type Mismatch! Peer A: {nt_a}, Peer B: {nt_b}")

        if errors:
            raise ValueError(" | ".join(errors))

        return True

    @depends_on("test_config_audit")
    def test_validate_state_targeted(self) -> bool:
        """Step 4: Operational State Validation via Targeted Neighbor Detail."""
        vrf = getattr(self, "vrf", "default") or "default"

        cmd_a = f"show ip ospf neighbor {self.local_int_name_a} detail"
        cmd_b = f"show ip ospf neighbor {self.local_int_name_b} detail"
        if vrf != "default":
            cmd_a = f"show ip ospf vrf {vrf} neighbor {self.local_int_name_a} detail"
            cmd_b = f"show ip ospf vrf {vrf} neighbor {self.local_int_name_b} detail"

        def safe_parse(device, command):
            try:
                return device.get_genie_device_object().parse(command)
            except Exception:
                return {}

        view_a = self._extract_neighbor_map(safe_parse(self.device_a, cmd_a))
        view_b = self._extract_neighbor_map(safe_parse(self.device_b, cmd_b))

        state_a_sees_b = view_a.get(self.rid_b, "DOWN")
        state_b_sees_a = view_b.get(self.rid_a, "DOWN")

        if (
            state_a_sees_b != self.expected_state
            or state_b_sees_a != self.expected_state
        ):
            raise ValueError(
                f"Adjacency Failure! Target: {self.expected_state} | "
                f"{self.device_a.name} reports {state_a_sees_b}, "
                f"{self.device_b.name} reports {state_b_sees_a}"
            )
        return True
