import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Danijel Stamenkovic"


class Management_Plane_Security(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-dark text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-shield-lock-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Management Plane Security Audit</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-dark text-white bg-opacity-75 border border-dark border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Device Hardening</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test enforces strict device hardening policies for the management plane. It verifies
                        that unencrypted management protocols (Telnet, HTTP) are disabled, validates the operational
                        SSH version, audits the RSA cryptographic key length, and ensures secure transport layers
                        are mandated on all virtual terminal (VTY) lines.
                    </p>

                    <div class="p-3 rounded border border-dark border-opacity-25 bg-dark bg-opacity-10">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            Cleartext protocols expose administrative credentials to packet sniffers. Weak RSA keys
                            are susceptible to brute-force attacks. This audit ensures compliance with zero-trust baselines.
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
                                <td class="fw-bold font-monospace">require_ssh_v2 <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Fails if SSH version 1 is permitted</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">min_rsa_modulus</td>
                                <td class="text-body-secondary">The minimum required RSA key length (e.g. 2048)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">require_http_disabled <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Fails if 'ip http server' is active</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vty_transport_strict</td>
                                <td class="text-body-secondary">Require 'transport input ssh' on all VTYs</td>
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
                <span class="badge bg-dark bg-opacity-10 text-body-emphasis border border-dark border-opacity-10 rounded-pill px-3 py-1">Danijel Stamenkovic</span>
            </div>
        </div>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "Target Switch",
            "type": "device",
            "description": "The switch undergoing the hardening audit.",
            "requirement": "required",
        },
        {
            "name": "require_ssh_v2",
            "display_name": "Enforce SSHv2",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Mandates strict SSH Version 2 operation to avoid legacy vulnerabilities.",
            "requirement": "required",
        },
        {
            "name": "min_rsa_modulus",
            "display_name": "Minimum RSA Key Size",
            "type": "positive-number",
            "default": 2048,
            "description": "The lowest acceptable RSA cryptographic key length in bits.",
            "requirement": "optional",
        },
        {
            "name": "require_http_disabled",
            "display_name": "Enforce HTTP Disabled",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Ensures the insecure cleartext web server is non-operational.",
            "requirement": "required",
        },
        {
            "name": "vty_transport_strict",
            "display_name": "Strict VTY Transport",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "Verifies that Telnet is stripped from all virtual terminal lines.",
            "requirement": "optional",
        },
    ]

    def _setup(self):
        self.genie_dev = self.device.get_genie_device_object(log_stdout=False)
        self.mgmt_data = {
            "ssh_version": "",
            "rsa_key_size": 0,
            "http_server": False,
            "https_server": False,
            "vty_transports": [],
            "raw_ssh": "",
            "raw_http": "",
            "raw_vty": "",
        }

    def _to_int(self, value):
        try:
            return int(str(value).strip()) if value is not None else None
        except (ValueError, TypeError):
            return None

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(
                f"Hardening audit failed: {self.device.name} is unresponsive."
            )
        return True

    @depends_on("test_device_connection")
    def test_fetch_ssh_status(self) -> bool:
        self.mgmt_data["raw_ssh"] = self.genie_dev.execute("show ip ssh")
        if (
            "SSH Disabled" in self.mgmt_data["raw_ssh"]
            or "not enabled" in self.mgmt_data["raw_ssh"]
        ):
            raise ValueError(
                "SSH is globally disabled. The device can only be managed via insecure protocols."
            )
        return True

    @depends_on("test_fetch_ssh_status")
    def test_parse_ssh_telemetry(self) -> bool:
        version_match = re.search(
            r"SSH.*version\s*(.*?)$",
            self.mgmt_data["raw_ssh"],
            re.MULTILINE | re.IGNORECASE,
        )
        if version_match:
            self.mgmt_data["ssh_version"] = version_match.group(1).strip()

        rsa_match = re.search(
            r"RSA key size.*?(\d+)", self.mgmt_data["raw_ssh"], re.IGNORECASE
        )
        if rsa_match:
            self.mgmt_data["rsa_key_size"] = self._to_int(rsa_match.group(1))
        else:
            crypto_output = self.genie_dev.execute("show crypto key mypubkey rsa")
            modulus_match = re.search(r"Size\s*=\s*(\d+)", crypto_output)
            if modulus_match:
                self.mgmt_data["rsa_key_size"] = self._to_int(modulus_match.group(1))

        return True

    @depends_on("test_parse_ssh_telemetry")
    def test_validate_ssh_version(self) -> bool:
        if self.require_ssh_v2 == "Yes":
            if "1.99" in self.mgmt_data["ssh_version"]:
                raise ValueError(
                    "SSH Downgrade Attack Vulnerability: SSHv1 is supported alongside v2 (Version 1.99)."
                )
            if "2.0" not in self.mgmt_data["ssh_version"]:
                raise ValueError(
                    f"SSH Version violation. Expected 2.0, running {self.mgmt_data['ssh_version']}."
                )
        return True

    @depends_on("test_parse_ssh_telemetry")
    def test_validate_rsa_modulus(self) -> bool:
        min_rsa = self._to_int(getattr(self, "min_rsa_modulus", None))
        if min_rsa:
            if not self.mgmt_data["rsa_key_size"]:
                raise ValueError(
                    "RSA key mapping failed. Certificates may be absent or improperly generated."
                )
            if self.mgmt_data["rsa_key_size"] < min_rsa:
                raise ValueError(
                    f"Weak cryptography detected. RSA key is {self.mgmt_data['rsa_key_size']} bits. Minimum mandated is {min_rsa} bits."
                )
        return True

    @depends_on("test_device_connection")
    def test_fetch_http_status(self) -> bool:
        self.mgmt_data["raw_http"] = self.genie_dev.execute(
            "show running-config | include http"
        )

        for line in self.mgmt_data["raw_http"].splitlines():
            line = line.strip()
            if line == "ip http server":
                self.mgmt_data["http_server"] = True
            elif line == "no ip http server":
                self.mgmt_data["http_server"] = False
            elif line == "ip http secure-server":
                self.mgmt_data["https_server"] = True
            elif line == "no ip http secure-server":
                self.mgmt_data["https_server"] = False

        return True

    @depends_on("test_fetch_http_status")
    def test_validate_http_disable(self) -> bool:
        if self.require_http_disabled == "Yes":
            if self.mgmt_data["http_server"]:
                raise ValueError(
                    "Insecure Service Alert: The cleartext HTTP server is active and responding."
                )
        return True

    @depends_on("test_device_connection")
    def test_fetch_vty_lines(self) -> bool:
        self.mgmt_data["raw_vty"] = self.genie_dev.execute(
            "show running-config | section line vty"
        )
        if not self.mgmt_data["raw_vty"].strip():
            raise ValueError("VTY configuration block could not be extracted.")
        return True

    @depends_on("test_fetch_vty_lines")
    def test_parse_and_validate_vty_transport(self) -> bool:
        strict_transport = getattr(self, "vty_transport_strict", "Yes")
        if strict_transport == "Yes":
            lines = self.mgmt_data["raw_vty"].splitlines()
            current_vty = ""
            vty_transports = {}

            for line in lines:
                line = line.strip()
                if line.startswith("line vty"):
                    current_vty = line
                    vty_transports[current_vty] = "all"
                elif line.startswith("transport input") and current_vty:
                    vty_transports[current_vty] = line.replace(
                        "transport input", ""
                    ).strip()

            for vty, trans in vty_transports.items():
                if "all" in trans or "telnet" in trans:
                    raise ValueError(
                        f"Cleartext Management Allowed: {vty} is configured with 'transport input {trans}'."
                    )
                if "ssh" not in trans:
                    raise ValueError(
                        f"SSH Enforcement Failed: {vty} does not explicitly permit SSH. Found: '{trans}'."
                    )

        return True
