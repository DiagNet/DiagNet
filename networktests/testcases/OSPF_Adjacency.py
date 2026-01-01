import ipaddress

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class OSPF_Adjacency(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #f59e0b;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">OSPF Adjacency</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Dual-Peer Link Discovery & State Validation</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>OSPF_Adjacency</strong> test class performs a comprehensive "Three-Way" validation of an OSPF relationship.
                It automatically identifies shared Link-Layer segments, verifies mutual state synchronization, and audits configuration consistency.
            </p>
        </section>

        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #f59e0b; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Test Logic & Capabilities
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">✔</span>
                <span><strong>Topology Discovery:</strong> Automatically matches peers by identifying overlapping subnets across all OSPF-enabled interfaces.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">✔</span>
                <span><strong>Dual-State Verification:</strong> Confirms that <em>both</em> routers see each other in the desired state (e.g., FULL), catching asymmetric communication issues.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">✔</span>
                <span><strong>Timer Audit:</strong> Cross-references OSPF <code>Hello</code> and <code>Dead</code> intervals to ensure perfect synchronization on the shared segment.</span>
            </li>
        </ul>

        <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 25px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 15px;">
            Authored by: Luka Pacar
        </p>
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
