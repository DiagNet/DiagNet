import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Device_Identity_Crypto_Audit(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-success text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-fingerprint fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Device Identity & Crypto Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-success text-success-emphasis bg-opacity-10 border border-success border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary text-secondary-emphasis bg-opacity-10 border border-secondary border-opacity-25">Infrastructure Security</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test validates the foundational network identity and cryptographic posture of the device.
                        It verifies domain name assignments, analyzes the SSH daemon version, audits the RSA
                        cryptographic key length for key-exchange safety, and ensures insecure DNS lookup mechanics
                        are deactivated.
                    </p>

                    <div class="p-3 rounded border border-success border-opacity-25 bg-success bg-opacity-10">
                        <h6 class="fw-bold text-success-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Weak RSA keys enable decryption of administrative traffic. Active domain lookups can cause
                            massive CLI freezes during misconfigurations. A correct domain identity is mandatory for PKI.
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
                                <td class="fw-bold font-monospace">expected_domain <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The required corporate FQDN suffix</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">enforce_no_lookup <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Fails if 'ip domain-lookup' is active</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">enforce_ssh_v2 <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Fails if SSHv1 rollback is permitted</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">min_rsa_modulus</td>
                                <td class="text-body-secondary">The minimum required RSA bits (e.g. 2048)</td>
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
                <span class="badge bg-success bg-opacity-10 text-success-emphasis border border-success border-opacity-10 rounded-pill px-3 py-1">Danijel Stamenkovic</span>
            </div>
        </div>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "Target Switch",
            "type": "device",
            "description": "The switch to validate the global identity of.",
            "requirement": "required",
        },
        {
            "name": "expected_domain",
            "display_name": "Expected Domain Name",
            "type": "text",
            "description": "The expected 'ip domain-name' suffix.",
            "requirement": "required",
        },
        {
            "name": "enforce_no_lookup",
            "display_name": "Enforce No Domain Lookup",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Ensures the device does not hang when resolving typos in the CLI.",
            "requirement": "required",
        },
        {
            "name": "enforce_ssh_v2",
            "display_name": "Enforce SSHv2",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Ensures 'ip ssh version 2' is strictly enforced.",
            "requirement": "required",
        },
        {
            "name": "min_rsa_modulus",
            "display_name": "Minimum RSA Modulus",
            "type": "positive-number",
            "default": 2048,
            "description": "The minimum bit length of the generated cryptographic keys.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.crypto_data = {
            "domain_name": "",
            "domain_lookup": True,
            "ssh_version": "",
            "rsa_key_size": 0,
            "raw_config": "",
            "raw_ssh": "",
            "raw_crypto": "",
        }

    def _to_int(self, value):
        try:
            return int(str(value).strip()) if value is not None else None
        except (ValueError, TypeError):
            return None

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(
                f"Identity audit aborted: {self.device.name} is unresponsive."
            )
        return True

    @depends_on("test_device_connection")
    def test_fetch_global_identity(self) -> bool:
        self.crypto_data["raw_config"] = self.genie_dev.execute(
            "show running-config | include domain"
        )
        return True

    @depends_on("test_fetch_global_identity")
    def test_parse_global_identity(self) -> bool:
        if "no ip domain-lookup" in self.crypto_data["raw_config"]:
            self.crypto_data["domain_lookup"] = False

        domain_match = re.search(
            r"ip domain-name (\S+)", self.crypto_data["raw_config"]
        )
        if domain_match:
            self.crypto_data["domain_name"] = domain_match.group(1).strip()
        return True

    @depends_on("test_parse_global_identity")
    def test_validate_domain_lookup(self) -> bool:
        if self.enforce_no_lookup == "Yes" and self.crypto_data["domain_lookup"]:
            raise ValueError(
                "Operational Risk: DNS Domain Lookup is active. This can cause severe CLI freezes."
            )
        return True

    @depends_on("test_parse_global_identity")
    def test_validate_domain_name(self) -> bool:
        if self.crypto_data["domain_name"] != self.expected_domain:
            raise ValueError(
                f"Identity mismatch. Configured domain is '{self.crypto_data['domain_name']}', required is '{self.expected_domain}'. Crypto key generation may fail."
            )
        return True

    @depends_on("test_device_connection")
    def test_fetch_and_parse_ssh(self) -> bool:
        self.crypto_data["raw_ssh"] = self.genie_dev.execute("show ip ssh")

        version_match = re.search(
            r"SSH.*version\s*(.*?)$",
            self.crypto_data["raw_ssh"],
            re.MULTILINE | re.IGNORECASE,
        )
        if version_match:
            self.crypto_data["ssh_version"] = version_match.group(1).strip()

        return True

    @depends_on("test_fetch_and_parse_ssh")
    def test_validate_ssh_version(self) -> bool:
        if self.enforce_ssh_v2 == "Yes":
            if (
                "1.99" in self.crypto_data["ssh_version"]
                or "1.5" in self.crypto_data["ssh_version"]
            ):
                raise ValueError(
                    f"SSH Downgrade Vulnerability: Device supports insecure legacy versions. Found: {self.crypto_data['ssh_version']}."
                )
            if "2.0" not in self.crypto_data["ssh_version"]:
                raise ValueError(
                    "Cryptographic Policy Breach: SSHv2 is not strictly enforced."
                )
        return True

    @depends_on("test_device_connection")
    def test_fetch_and_parse_crypto_keys(self) -> bool:
        self.crypto_data["raw_crypto"] = self.genie_dev.execute(
            "show crypto key mypubkey rsa"
        )

        modulus_match = re.search(r"Size\s*=\s*(\d+)", self.crypto_data["raw_crypto"])
        if modulus_match:
            self.crypto_data["rsa_key_size"] = self._to_int(modulus_match.group(1))

        return True

    @depends_on("test_fetch_and_parse_crypto_keys")
    def test_validate_rsa_modulus(self) -> bool:
        min_rsa = self._to_int(getattr(self, "min_rsa_modulus", None))
        if min_rsa:
            if not self.crypto_data["rsa_key_size"]:
                raise ValueError(
                    "Cryptographic identity failure: No RSA public keys found on the device."
                )
            if self.crypto_data["rsa_key_size"] < min_rsa:
                raise ValueError(
                    f"Weak Encryption Standard: Configured RSA key is {self.crypto_data['rsa_key_size']} bits. A minimum of {min_rsa} bits is mandated."
                )
        return True
