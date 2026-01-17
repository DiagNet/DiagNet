from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class NAT(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #34d399;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">NAT Operations Audit</h2>
            <p style="color: #ecfdf5; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Interface Roles, Translation Logic & Pool Integrity</p>
        </div>

        <section style="margin-top: 20px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>NAT</strong> test class performs a comprehensive audit of the Network Address Translation (NAT) subsystem.
                It verifies that traffic flows are correctly translated according to the configured policy (Static, Dynamic, or Overload) and ensures that underlying resources (Pools, Interfaces) are correctly allocated.
            </p>
        </section>

        <h4 style="color: #064e3b; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #34d399; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Validation Capabilities
        </h4>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;">
                <strong style="color: #064e3b; display: block; margin-bottom: 5px;">1. Static Mapping</strong>
                <span style="font-size: 0.9rem; color: #047857;">
                    Strictly validates 1:1 translations. Ensures specific <em>Inside Local</em> IPs correspond to the correct <em>Inside Global</em> IPs in the active table.
                </span>
            </div>

            <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;">
                <strong style="color: #064e3b; display: block; margin-bottom: 5px;">2. Dynamic Pools</strong>
                <span style="font-size: 0.9rem; color: #047857;">
                    Audits IP Pools for configuration compliance (Start/End/Netmask) and health. Fails if the pool has recorded allocation <strong>misses</strong> (exhaustion).
                </span>
            </div>

            <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;">
                <strong style="color: #064e3b; display: block; margin-bottom: 5px;">3. PAT / Overload</strong>
                <span style="font-size: 0.9rem; color: #047857;">
                    Verifies that Port Address Translation is active and strictly bound to the expected <strong>Overload Interface</strong>.
                </span>
            </div>

            <div style="background: #ecfdf5; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981;">
                <strong style="color: #064e3b; display: block; margin-bottom: 5px;">4. Interface Roles</strong>
                <span style="font-size: 0.9rem; color: #047857;">
                    Pre-check audit to confirm that interfaces are correctly flagged as <code>ip nat inside</code> or <code>ip nat outside</code> before testing logic.
                </span>
            </div>
        </div>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "NAT Device",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "VRF Context",
            "type": "str",
            "default": "default",
            "requirement": "optional",
        },
        {
            "name": "nat_interfaces",
            "display_name": "NAT Interfaces",
            "type": "list",
            "description": "The Interfaces having NAT activated",
            "requirement": "optional",
            "parameters": [
                {
                    "name": "interface",
                    "display_name": "Interface",
                    "type": "cisco-interface",
                    "description": "The given interface",
                    "requirement": "required",
                },
                {
                    "name": "direction",
                    "display_name": "Direction",
                    "type": "choice",
                    "choices": ["Ingoing", "Outgoing"],
                    "default_choice": "Ingoing",
                    "requirement": "required",
                    "description": "Marks if the port is ingoing or outgoing",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
        {
            "name": "min_active_translations",
            "display_name": "Min. Active Translations",
            "type": "positive-number",
            "description": "General/Overload: Fail if active translations are below this count.",
            "requirement": "optional",
        },
        {
            "name": "validation_mode",
            "display_name": "Validation Mode",
            "type": "choice",
            "choices": [
                "Static",
                "Dynamic",
                "NAT/PAT - Overload",
            ],
            "default_choice": "Static",
            "description": "Select the NAT type to validate.",
            "requirement": "required",
        },
        {
            "name": "static_rules",
            "display_name": "Expected Static Entries",
            "type": "list",
            "requirement": "optional",
            "required_if": {"validation_mode": "Static"},
            "parameters": [
                {
                    "name": "inside_local",
                    "display_name": "Inside Local IP",
                    "type": "IPv4",
                    "requirement": "required",
                },
                {
                    "name": "inside_global",
                    "display_name": "Inside Global IP",
                    "type": "IPv4",
                    "requirement": "required",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
        {
            "name": "pool_name",
            "display_name": "Dynamic Pool Name",
            "type": "str",
            "requirement": "optional",
            "required_if": {"validation_mode": "Dynamic"},
        },
        {
            "name": "expected_pool_start",
            "display_name": "Expected Pool Start IP",
            "type": "IPv4",
            "requirement": "optional",
            "required_if": {"validation_mode": "Dynamic"},
            "description": "Start IP of the NAT Pool range.",
        },
        {
            "name": "expected_pool_end",
            "display_name": "Expected Pool End IP",
            "type": "IPv4",
            "requirement": "optional",
            "required_if": {"validation_mode": "Dynamic"},
            "description": "End IP of the NAT Pool range.",
        },
        {
            "name": "expected_pool_netmask",
            "display_name": "Expected Pool Netmask",
            "type": "IPv4",
            "requirement": "optional",
            "required_if": {"validation_mode": "Dynamic"},
            "description": "Subnet mask of the NAT Pool.",
        },
        {
            "name": "overload_interface",
            "display_name": "NAT/PAT - Overload Interface",
            "description": 'The Interface maked as "overload" and used in the NAT/PAT process',
            "type": "cisco-interface",
            "requirement": "optional",
            "required_if": {"validation_mode": "NAT/PAT - Overload"},
        },
    ]

    def _get_clean_ip(self, ip_port_str: str) -> str:
        if not ip_port_str or ip_port_str == "---":
            return ip_port_str
        return ip_port_str.split(":")[0]

    def test_connectivity(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(f"Target {self.device.name} is unreachable.")
        return True

    @depends_on("test_connectivity")
    def test_fetch_telemetry(self) -> bool:
        genie_dev = self.device.get_genie_device_object()
        vrf = getattr(self, "vrf", "default") or "default"

        cmd_stats = "show ip nat statistics"
        cmd_trans = "show ip nat translations"
        if vrf != "default":
            cmd_trans += f" vrf {vrf}"

        self.stats = genie_dev.parse(cmd_stats)

        try:
            raw_trans = genie_dev.parse(cmd_trans)
            idx = raw_trans.get("vrf", {}).get(vrf, {}).get("index", {})

            if isinstance(idx, dict):
                self.translations = list(idx.values())
            else:
                self.translations = idx
        except Exception:
            self.translations = []

        return True

    @depends_on("test_fetch_telemetry")
    def test_audit_interfaces(self) -> bool:
        if not getattr(self, "nat_interfaces", None):
            return True

        op_ints = self.stats.get("interfaces", {})
        errors = []

        for req in self.nat_interfaces:
            target = req["interface"]
            role = "inside" if req["direction"] == "Ingoing" else "outside"

            configured_interfaces = op_ints.get(role, [])

            if target not in configured_interfaces:
                errors.append(f"{target} is not configured as NAT {role}")

        if errors:
            raise ValueError(f"Interface Audit Failed: {', '.join(errors)}")
        return True

    @depends_on("test_audit_interfaces")
    def test_validate_nat_operation(self) -> bool:
        mode = self.validation_mode

        if getattr(self, "min_active_translations", None):
            total = self.stats.get("active_translations", {}).get("total", 0)
            if total < self.min_active_translations:
                raise ValueError(f"Low Activity: {total} translations found.")

        # Static NAT
        if mode == "Static":
            if not self.translations:
                raise ValueError(
                    "Static validation failed: NAT translation table is empty."
                )

            for rule in self.static_rules:
                target_local = rule["inside_local"]
                target_global = rule["inside_global"]
                found_match = False

                for entry in self.translations:
                    current_local = self._get_clean_ip(entry.get("inside_local"))
                    current_global = self._get_clean_ip(entry.get("inside_global"))

                    if (
                        current_local == target_local
                        and current_global == target_global
                    ):
                        found_match = True
                        break

                if not found_match:
                    raise ValueError(
                        f"Static Map missing: {target_local} -> {target_global}"
                    )

        # Dynamic NAT
        elif mode == "Dynamic":
            mappings = (
                self.stats.get("dynamic_mappings", {})
                .get("inside_source", {})
                .get("id", {})
            )
            pool_data = None

            for mapping_entry in mappings.values():
                pool_config = mapping_entry.get("pool", {})
                if self.pool_name in pool_config:
                    pool_data = pool_config[self.pool_name]
                    break

            if not pool_data:
                raise ValueError(f"Pool {self.pool_name} not found.")

            if pool_data.get("misses", 0) > 0:
                raise ValueError(f"Pool {self.pool_name} has allocation misses!")

            conf_errors = []

            if getattr(self, "expected_pool_start", None):
                actual_start = pool_data.get("start")
                if actual_start != self.expected_pool_start:
                    conf_errors.append(
                        f"Start IP Mismatch (Exp: {self.expected_pool_start}, Got: {actual_start})"
                    )

            if getattr(self, "expected_pool_end", None):
                actual_end = pool_data.get("end")
                if actual_end != self.expected_pool_end:
                    conf_errors.append(
                        f"End IP Mismatch (Exp: {self.expected_pool_end}, Got: {actual_end})"
                    )

            if getattr(self, "expected_pool_netmask", None):
                actual_mask = pool_data.get("netmask")
                if actual_mask != self.expected_pool_netmask:
                    conf_errors.append(
                        f"Netmask Mismatch (Exp: {self.expected_pool_netmask}, Got: {actual_mask})"
                    )

            if conf_errors:
                raise ValueError(f"Pool Config Mismatch: {', '.join(conf_errors)}")

        # Overload / PAT Validation
        elif mode == "NAT/PAT - Overload":
            mappings = (
                self.stats.get("dynamic_mappings", {})
                .get("inside_source", {})
                .get("id", {})
            )
            found_overload = False

            for mapping_entry in mappings.values():
                interface_name = str(mapping_entry.get("interface", ""))
                if self.overload_interface in interface_name:
                    found_overload = True
                    break

            if not found_overload:
                raise ValueError(f"PAT not bound to {self.overload_interface}")

        return True
