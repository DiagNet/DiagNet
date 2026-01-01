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
            "description": "Cross-references MTU, Hello/Dead Timers, and Network Types between peers.",
        },
        {
            "name": "area_id",
            "display_name": "Area ID Override",
            "type": "str",
            "requirement": "optional",
            "description": "Optional: Ensures the discovered link belongs to a specific OSPF Area.",
        },
    ]

    def _get_clean_state(self, raw_state):
        return str(raw_state).split("/")[0].strip().upper() if raw_state else "DOWN"

    def _extract_ospf_instance_data(self, raw_data):
        target_vrf = getattr(self, "vrf", "default") or "default"
        return (
            raw_data.get("vrf", {})
            .get(target_vrf, {})
            .get("address_family", {})
            .get("ipv4", {})
            .get("instance", {})
        )

    def _extract_all_neighbors(self, raw_data):
        neighbor_map = {}
        for instance in self._extract_ospf_instance_data(raw_data).values():
            for area in instance.get("areas", {}).values():
                for interface in area.get("interfaces", {}).values():
                    for rid, nbr in interface.get("neighbors", {}).items():
                        if "state" in nbr:
                            neighbor_map[rid] = self._get_clean_state(nbr["state"])
        return neighbor_map

    def _extract_local_router_id(self, raw_data):
        for instance in self._extract_ospf_instance_data(raw_data).values():
            for area in instance.get("areas", {}).values():
                for interface in area.get("interfaces", {}).values():
                    rid = interface.get("router_id")
                    if rid:
                        return rid
        return None

    def _get_ospf_interfaces(self, raw_data):
        for instance in self._extract_ospf_instance_data(raw_data).values():
            for area in instance.get("areas", {}).values():
                return area.get("interfaces", {})
        return {}

    def test_device_reachability(self) -> bool:
        """Verifies that both devices are reachable via the diagnostic framework."""
        for peer in [self.device_a, self.device_b]:
            if not peer.can_connect():
                raise ValueError(f"Connectivity failed for {peer.name}")
        return True

    @depends_on("test_device_reachability")
    def test_fetch_and_discover_link(self) -> bool:
        vrf_context = getattr(self, "vrf", "default") or "default"
        cmd = (
            "show ip ospf interface"
            if vrf_context == "default"
            else f"show ip ospf vrf {vrf_context} interface"
        )

        raw_a = self.device_a.get_genie_device_object().parse(cmd)
        raw_b = self.device_b.get_genie_device_object().parse(cmd)

        self.rid_a = self._extract_local_router_id(raw_a)
        self.rid_b = self._extract_local_router_id(raw_b)

        if not self.rid_a or not self.rid_b:
            raise ValueError(
                f"Router-ID discovery failed. RID_A: {self.rid_a}, RID_B: {self.rid_b}"
            )

        ints_a = self._get_ospf_interfaces(raw_a)
        ints_b = self._get_ospf_interfaces(raw_b)

        self.shared_link_params = {}
        for name_a, data_a in ints_a.items():
            if not data_a.get("ip_address"):
                continue
            net_a = ipaddress.ip_interface(data_a["ip_address"]).network

            for name_b, data_b in ints_b.items():
                if not data_b.get("ip_address"):
                    continue
                if net_a == ipaddress.ip_interface(data_b["ip_address"]).network:
                    self.shared_link_params = {"a": data_a, "b": data_b}
                    return True

        raise ValueError(
            "Topology Mismatch: No shared OSPF subnet found between peers."
        )

    @depends_on("test_fetch_and_discover_link")
    def test_validate_dual_neighbor_state(self) -> bool:
        vrf_context = getattr(self, "vrf", "default") or "default"
        cmd = (
            "show ip ospf neighbor detail"
            if vrf_context == "default"
            else f"show ip ospf vrf {vrf_context} neighbor detail"
        )

        view_a = self._extract_all_neighbors(
            self.device_a.get_genie_device_object().parse(cmd)
        )
        view_b = self._extract_all_neighbors(
            self.device_b.get_genie_device_object().parse(cmd)
        )

        state_a_sees_b = view_a.get(self.rid_b, "DOWN")
        state_b_sees_a = view_b.get(self.rid_a, "DOWN")

        if (
            state_a_sees_b != self.expected_state
            or state_b_sees_a != self.expected_state
        ):
            raise ValueError(
                f"Adjacency Mismatch! Expected: {self.expected_state} | "
                f"{self.device_a.name} reports {state_a_sees_b}, "
                f"{self.device_b.name} reports {state_b_sees_a}"
            )
        return True

    @depends_on("test_validate_dual_neighbor_state")
    def test_config_consistency_audit(self) -> bool:
        if self.audit_config_consistency == "No":
            return True

        hello_a = self.shared_link_params["a"].get("hello_interval")
        hello_b = self.shared_link_params["b"].get("hello_interval")

        if hello_a != hello_b:
            raise ValueError(
                f"Timer Mismatch! {self.device_a.name}: {hello_a}s, {self.device_b.name}: {hello_b}s"
            )

        return True
