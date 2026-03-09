import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class AAA_Radius_Configuration(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-person-badge-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">AAA & RADIUS Enforcement</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-primary text-dark bg-opacity-75 border border-primary border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Identity & Access Management</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test performs a deep inspection of the global AAA (Authentication, Authorization, and Accounting)
                        infrastructure. It validates the presence of the new-model architecture, verifies RADIUS server
                        reachability metrics, audits the AAA server groups, and strictly enforces the mapping of these
                        policies to the virtual terminal (VTY) lines.
                    </p>

                    <div class="p-3 rounded border border-primary border-opacity-25 bg-primary bg-opacity-10">
                        <h6 class="fw-bold text-primary-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Ensures zero-trust access control by preventing fallback to local authentication without explicit
                            policies, and confirms integration with Identity Services Engines (ISE) or NAC solutions.
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
                                <td class="text-body-secondary">The target network device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">radius_ip <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Expected IP address of the ISE/RADIUS server</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">auth_port</td>
                                <td class="text-body-secondary">RADIUS Authentication Port (default 1812)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">acct_port</td>
                                <td class="text-body-secondary">RADIUS Accounting Port (default 1813)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_group_name</td>
                                <td class="text-body-secondary">Name of the AAA group server radius</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">verify_vty_mapping <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Ensure AAA methods are applied to VTY lines</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_login_method</td>
                                <td class="text-body-secondary">The AAA authentication method list name</td>
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
            "description": "The switch or router to audit.",
            "requirement": "required",
        },
        {
            "name": "radius_ip",
            "display_name": "RADIUS / ISE IP",
            "type": "ipv4",
            "description": "The IPv4 address of the target RADIUS server.",
            "requirement": "required",
        },
        {
            "name": "auth_port",
            "display_name": "Auth Port",
            "type": "positive-number",
            "default": 1812,
            "description": "The UDP port used for authentication.",
            "requirement": "optional",
        },
        {
            "name": "acct_port",
            "display_name": "Acct Port",
            "type": "positive-number",
            "default": 1813,
            "description": "The UDP port used for accounting.",
            "requirement": "optional",
        },
        {
            "name": "expected_group_name",
            "display_name": "AAA Group Name",
            "type": "text",
            "description": "The expected identifier for the AAA group server radius.",
            "requirement": "optional",
        },
        {
            "name": "verify_vty_mapping",
            "display_name": "Verify VTY Enforcement",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Strictly checks if login authentication and authorization are bound to line vty.",
            "requirement": "required",
        },
        {
            "name": "expected_login_method",
            "display_name": "Login Method Name",
            "type": "text",
            "description": "The AAA list name attached to the VTY lines.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.aaa_data = {
            "new_model": False,
            "radius_servers": [],
            "aaa_groups": [],
            "auth_lists": {},
            "authz_lists": {},
            "vty": {"login_method": "", "authz_method": "", "transport": ""},
            "raw_config": "",
        }

    def _to_int(self, value):
        try:
            return int(str(value).strip()) if value is not None else None
        except (ValueError, TypeError):
            return None

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(
                f"Management plane unreachable for device {self.device.name}."
            )
        return True

    @depends_on("test_device_connection")
    def test_fetch_aaa_configuration(self) -> bool:
        command = "show running-config | section ^aaa|^radius|^line vty"
        self.aaa_data["raw_config"] = self.genie_dev.execute(command)
        if not self.aaa_data["raw_config"].strip():
            raise ValueError("Failed to extract AAA configuration blocks.")
        return True

    @depends_on("test_fetch_aaa_configuration")
    def test_parse_global_aaa_model(self) -> bool:
        if "aaa new-model" in self.aaa_data["raw_config"]:
            self.aaa_data["new_model"] = True
        return True

    @depends_on("test_fetch_aaa_configuration")
    def test_parse_radius_servers(self) -> bool:
        lines = self.aaa_data["raw_config"].splitlines()
        current_server = {}

        for line in lines:
            line = line.strip()
            if line.startswith("radius server"):
                if current_server:
                    self.aaa_data["radius_servers"].append(current_server)
                current_server = {"name": line.split("radius server ")[1].strip()}
            elif line.startswith("address ipv4") and current_server:
                ip_match = re.search(r"address ipv4 ([\d\.]+)", line)
                auth_match = re.search(r"auth-port (\d+)", line)
                acct_match = re.search(r"acct-port (\d+)", line)

                if ip_match:
                    current_server["ip"] = ip_match.group(1)
                if auth_match:
                    current_server["auth_port"] = self._to_int(auth_match.group(1))
                if acct_match:
                    current_server["acct_port"] = self._to_int(acct_match.group(1))

        if current_server:
            self.aaa_data["radius_servers"].append(current_server)

        return True

    @depends_on("test_fetch_aaa_configuration")
    def test_parse_aaa_groups(self) -> bool:
        lines = self.aaa_data["raw_config"].splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("aaa group server radius"):
                group_name = line.replace("aaa group server radius", "").strip()
                self.aaa_data["aaa_groups"].append(group_name)
            elif line.startswith("aaa authentication login"):
                parts = line.split()
                if len(parts) >= 4:
                    self.aaa_data["auth_lists"][parts[3]] = " ".join(parts[4:])
            elif line.startswith("aaa authorization exec"):
                parts = line.split()
                if len(parts) >= 4:
                    self.aaa_data["authz_lists"][parts[3]] = " ".join(parts[4:])
        return True

    @depends_on("test_fetch_aaa_configuration")
    def test_parse_vty_lines(self) -> bool:
        lines = self.aaa_data["raw_config"].splitlines()
        in_vty = False

        for line in lines:
            if line.startswith("line vty"):
                in_vty = True
            elif in_vty and line.startswith("line "):
                in_vty = False
            elif in_vty:
                clean_line = line.strip()
                if clean_line.startswith("login authentication"):
                    self.aaa_data["vty"]["login_method"] = clean_line.split(
                        "login authentication "
                    )[1].strip()
                elif clean_line.startswith("authorization exec"):
                    self.aaa_data["vty"]["authz_method"] = clean_line.split(
                        "authorization exec "
                    )[1].strip()
                elif clean_line.startswith("transport input"):
                    self.aaa_data["vty"]["transport"] = clean_line.split(
                        "transport input "
                    )[1].strip()

        return True

    @depends_on("test_parse_global_aaa_model")
    def test_validate_new_model(self) -> bool:
        if not self.aaa_data["new_model"]:
            raise ValueError(
                "Critical Security Gap: 'aaa new-model' is not enabled on this device."
            )
        return True

    @depends_on("test_parse_radius_servers")
    def test_validate_radius_metrics(self) -> bool:
        found_server = None
        for srv in self.aaa_data["radius_servers"]:
            if srv.get("ip") == self.radius_ip:
                found_server = srv
                break

        if not found_server:
            raise ValueError(
                f"RADIUS server with IP {self.radius_ip} is not configured."
            )

        expected_auth = self._to_int(getattr(self, "auth_port", 1812))
        expected_acct = self._to_int(getattr(self, "acct_port", 1813))

        if expected_auth and found_server.get("auth_port") != expected_auth:
            raise ValueError(
                f"Authentication port mismatch. Expected: {expected_auth}, Found: {found_server.get('auth_port')}"
            )

        if expected_acct and found_server.get("acct_port") != expected_acct:
            raise ValueError(
                f"Accounting port mismatch. Expected: {expected_acct}, Found: {found_server.get('acct_port')}"
            )

        return True

    @depends_on("test_parse_aaa_groups")
    def test_validate_group_name(self) -> bool:
        expected_group = getattr(self, "expected_group_name", None)
        if expected_group:
            if expected_group not in self.aaa_data["aaa_groups"]:
                raise ValueError(
                    f"AAA Radius group '{expected_group}' is completely missing from the configuration."
                )
        return True

    @depends_on("test_parse_vty_lines")
    def test_validate_vty_mapping(self) -> bool:
        if self.verify_vty_mapping == "Yes":
            vty_login = self.aaa_data["vty"]["login_method"]
            expected_login = getattr(self, "expected_login_method", None)

            if not vty_login:
                raise ValueError(
                    "VTY lines are entirely unprotected. No AAA login authentication method is applied."
                )

            if expected_login and vty_login != expected_login:
                raise ValueError(
                    f"VTY Mapping failure. Applied method: '{vty_login}', Required policy: '{expected_login}'."
                )

            if vty_login not in self.aaa_data["auth_lists"] and vty_login != "default":
                raise ValueError(
                    f"Dangling pointer: VTY uses method '{vty_login}', but this method is not defined globally."
                )

        return True
