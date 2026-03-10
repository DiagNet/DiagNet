from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Local_Account_Security(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-people-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Local Account Encryption Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-primary text-white bg-opacity-75 border border-primary border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">IAM Security</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test evaluates the cryptographic strength of fallback administrative accounts stored
                        locally on the device. It iterates through the running configuration to map usernames,
                        validates privilege allocations, and strictly rejects weak Type 7 or Type 5 hashes in favor
                        of strong hashing algorithms (e.g., scrypt).
                    </p>

                    <div class="p-3 rounded border border-primary border-opacity-25 bg-primary bg-opacity-10">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Local accounts are essential during RADIUS/ISE outages. However, legacy hashes (Type 7)
                            can be cracked instantly, leading to full network compromise.
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
                                <td class="fw-bold font-monospace">expected_username <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The mandatory administrative username</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">require_privilege_15 <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Ensure the account maps to root/privilege 15</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">required_algorithm</td>
                                <td class="text-body-secondary">The expected hashing method (e.g., scrypt)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">fail_on_weak_hashes <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Rejects the audit if any user has a Type 7 or plaintext password</td>
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
                <span class="badge bg-primary bg-opacity-10 text-body-emphasis border border-primary border-opacity-10 rounded-pill px-3 py-1">Danijel Stamenkovic</span>
            </div>
        </div>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "Target Switch",
            "type": "device",
            "description": "The switch hosting the local accounts.",
            "requirement": "required",
        },
        {
            "name": "expected_username",
            "display_name": "Expected Username",
            "type": "text",
            "description": "The specific admin user that must exist in the configuration.",
            "requirement": "required",
        },
        {
            "name": "require_privilege_15",
            "display_name": "Require Privilege 15",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Validates if the user possesses maximum system privileges.",
            "requirement": "required",
        },
        {
            "name": "required_algorithm",
            "display_name": "Required Encryption Type",
            "type": "choice",
            "choices": ["scrypt", "sha256", "None"],
            "default_choice": "scrypt",
            "description": "Enforces a specific modern algorithm for password storage.",
            "requirement": "optional",
        },
        {
            "name": "fail_on_weak_hashes",
            "display_name": "Reject Legacy Encryption",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Scans the entire user database and fails if Type 7 or Type 5 hashes are discovered.",
            "requirement": "required",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.auth_data = {"users": {}, "weak_hash_users": [], "raw_config": ""}

    def _to_int(self, value):
        try:
            return int(str(value).strip()) if value is not None else None
        except (ValueError, TypeError):
            return None

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(f"IAM Audit connection failed for {self.device.name}.")
        return True

    @depends_on("test_device_connection")
    def test_fetch_user_database(self) -> bool:
        self.auth_data["raw_config"] = self.genie_dev.execute(
            "show running-config | include username"
        )
        if not self.auth_data["raw_config"].strip():
            raise ValueError(
                "No local accounts found. Device may become permanently unmanageable during a RADIUS outage."
            )
        return True

    @depends_on("test_fetch_user_database")
    def test_parse_user_database(self) -> bool:
        lines = self.auth_data["raw_config"].splitlines()

        for line in lines:
            line = line.strip()
            if not line.startswith("username"):
                continue

            parts = line.split()
            if len(parts) < 3:
                continue

            username = parts[1]
            priv_level = 1
            algo = "unknown"
            hash_type = "unknown"

            if "privilege" in parts or "priv" in parts:
                try:
                    idx = (
                        parts.index("privilege")
                        if "privilege" in parts
                        else parts.index("priv")
                    )
                    priv_level = self._to_int(parts[idx + 1])
                except (ValueError, IndexError):
                    pass

            if "algorithm-type" in parts or "algo" in parts:
                try:
                    idx = (
                        parts.index("algorithm-type")
                        if "algorithm-type" in parts
                        else parts.index("algo")
                    )
                    algo = parts[idx + 1].lower()
                except (ValueError, IndexError):
                    pass

            if "secret" in parts:
                idx = parts.index("secret")
                if len(parts) > idx + 1:
                    next_val = parts[idx + 1]
                    if next_val.isdigit() and len(next_val) == 1:
                        hash_type = next_val
                        # IOS XE stores algorithm-type in the secret type number:
                        # type 9 = scrypt, type 8 = pbkdf2-sha256
                        if algo == "unknown":
                            if next_val == "9":
                                algo = "scrypt"
                            elif next_val == "8":
                                algo = "sha256"
                    else:
                        hash_type = "implicit_strong"
            elif "password" in parts:
                idx = parts.index("password")
                if len(parts) > idx + 1:
                    next_val = parts[idx + 1]
                    if next_val == "7" or next_val == "0":
                        hash_type = next_val

            if hash_type in ["0", "5", "7"]:
                self.auth_data["weak_hash_users"].append(username)

            self.auth_data["users"][username] = {
                "privilege": priv_level,
                "algorithm": algo,
                "hash_type": hash_type,
            }

        return True

    @depends_on("test_parse_user_database")
    def test_validate_mandatory_account(self) -> bool:
        if self.expected_username not in self.auth_data["users"]:
            raise ValueError(
                f"IAM Violation: The mandatory fallback user '{self.expected_username}' is not provisioned."
            )
        return True

    @depends_on("test_parse_user_database")
    def test_validate_privilege_allocation(self) -> bool:
        if (
            self.require_privilege_15 == "Yes"
            and self.expected_username in self.auth_data["users"]
        ):
            priv = self.auth_data["users"][self.expected_username]["privilege"]
            if priv != 15:
                raise ValueError(
                    f"Access Control Error: User '{self.expected_username}' is assigned privilege level {priv}. Expected is 15."
                )
        return True

    @depends_on("test_parse_user_database")
    def test_validate_encryption_algorithm(self) -> bool:
        req_algo = getattr(self, "required_algorithm", "None")
        if req_algo != "None" and self.expected_username in self.auth_data["users"]:
            configured_algo = self.auth_data["users"][self.expected_username][
                "algorithm"
            ]
            if configured_algo != req_algo.lower():
                raise ValueError(
                    f"Cryptographic Mismatch for '{self.expected_username}'. Expected algorithm: '{req_algo}', Discovered: '{configured_algo}'."
                )
        return True

    @depends_on("test_parse_user_database")
    def test_validate_global_hash_strength(self) -> bool:
        if self.fail_on_weak_hashes == "Yes":
            if self.auth_data["weak_hash_users"]:
                raise ValueError(
                    f"Severe Vulnerability: The following users are utilizing legacy, easily crackable (Type 7/5/0) password hashes: {', '.join(self.auth_data['weak_hash_users'])}."
                )
        return True
