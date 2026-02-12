from pyats.utils.exceptions import SchemaEmptyParserError

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class NAT(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-warning text-dark rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #f59e0b;">
                    <i class="bi bi-arrow-left-right fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">NAT</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-dark bg-opacity-75 border border-opacity-25" style="background-color: #fbbf24; border-color: #fbbf24;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">NAT / Addressing</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks your Network Address Translation (NAT) settings.
                        It confirms that interfaces are correctly marked as inside or outside.
                        It also validates specific rules for Static NAT, Dynamic pools, or Port Address Translation (PAT).
                    </p>

                    <div class="p-3 rounded border border-warning border-opacity-25 bg-warning bg-opacity-10">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures devices can access the internet and external users can reach public servers.
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
                                <td class="text-body-secondary">The NAT Device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF Context. Default is default</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">validation_mode <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Select the type of NAT to check</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">nat_interfaces</td>
                                <td class="text-body-secondary">List of interfaces using NAT</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Interface Name</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ direction <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Ingoing or Outgoing</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">static_rules</td>
                                <td class="text-body-secondary">Required for Static mode. List of specific IP mappings</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ inside_local <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Inside Local IP</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ inside_global <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Inside Global IP</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">min_active_translations</td>
                                <td class="text-body-secondary">Fail if active translations are below this count</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">pool_name <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Required when <span class="font-monospace">validation_mode</span> is Dynamic. The name of the address pool</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_pool_start <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Required when <span class="font-monospace">validation_mode</span> is Dynamic. Expected first IP address in the Dynamic pool</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_pool_end <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Required when <span class="font-monospace">validation_mode</span> is Dynamic. Expected last IP address in the Dynamic pool</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_pool_netmask <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Required when <span class="font-monospace">validation_mode</span> is Dynamic. Expected netmask for the Dynamic pool</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">overload_interface</td>
                                <td class="text-body-secondary">Required for Overload mode. The interface sharing the IP</td>
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
            "description": 'The Interface marked as "overload" and used in the NAT/PAT process',
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

        try:
            self.stats = genie_dev.parse(cmd_stats)
        except SchemaEmptyParserError:
            self.stats = {}
        except Exception as e:
            raise ValueError(
                f"Critical failure parsing NAT statistics on {self.device.name}: {str(e)}"
            )

        try:
            raw_trans = genie_dev.parse(cmd_trans)
            vrf_data = raw_trans.get("vrf", {}).get(vrf, {})
            idx_data = vrf_data.get("index", {})

            if isinstance(idx_data, dict):
                self.translations = list(idx_data.values())
            else:
                self.translations = []

        except SchemaEmptyParserError:
            self.translations = []

        except Exception as e:
            raise ValueError(
                f"Critical failure parsing NAT translations on {self.device.name}: {str(e)}"
            )

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
                raise ValueError(
                    f"Active translations (found: {total}) are below the minimum "
                    f"threshold ({self.min_active_translations})."
                )

        # Static NAT
        if mode == "Static":
            if not self.translations:
                raise ValueError(
                    "Static validation failed: NAT translation table is empty."
                )

            static_rules = getattr(self, "static_rules", None)
            if not static_rules:
                raise ValueError(
                    "Static validation failed: static_rules is not configured or is empty."
                )

            for rule in static_rules:
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

            if not self.pool_name:
                raise ValueError(
                    "Validation Mode 'Dynamic' requires a 'pool_name' parameter, but none was provided."
                )

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

            if not self.overload_interface:
                raise ValueError(
                    "Validation Mode 'NAT/PAT - Overload' requires a 'overload_interface' parameter, but none was provided."
                )

            for mapping_entry in mappings.values():
                interface_name = str(mapping_entry.get("interface", ""))
                overload_interface = str(self.overload_interface)
                if interface_name.strip().lower() == overload_interface.strip().lower():
                    found_overload = True
                    break

            if not found_overload:
                raise ValueError(f"PAT not bound to {self.overload_interface}")

        return True
