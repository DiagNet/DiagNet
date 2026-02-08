from networktests.testcases.base import DiagNetTest, depends_on
from typing import Union

__author__ = "Luka Pacar"


class OSPF_Interfaces(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-teal text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #0d9488;">
                    <i class="bi bi-hdd-network fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">OSPF Interface</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white bg-opacity-75 border border-opacity-25" style="background-color: #0f766e; border-color: #0f766e;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">OSPF / Security</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks your OSPF interfaces to ensure they are configured securely.
                        It verifies that interfaces without neighbors are set to passive so they do not send unnecessary data.
                        It also checks that active links connecting to other routers are using the required password or encryption settings.
                    </p>

                    <div class="p-3 rounded border border-opacity-25 bg-teal bg-opacity-10" style="border-color: #0d9488;">
                        <h6 class="fw-bold mb-1" style="color: #0d9488;">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It stops unauthorized devices from connecting to your network and improves overall security.
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
                                <td class="fw-bold font-monospace">target_device <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The Device to Audit</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF Context. Default is default</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">required_auth_type</td>
                                <td class="text-body-secondary">The security level required. Options are Ignore, Simple Password, or Encrypted</td>
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
            "name": "target_device",
            "display_name": "Device to Audit",
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
            "name": "required_auth_type",
            "display_name": "Required Auth Policy",
            "type": "choice",
            "choices": ["Ignore", "Simple", "Crypto"],
            "default_choice": "Crypto",
            "description": "Choose which level of authentication to enforce on transit links.",
        },
    ]

    def _get_ospf_interfaces(self, raw_data):
        if not raw_data:
            return {}
        vrf_key = getattr(self, "vrf", "default") or "default"
        try:
            vrf_data = raw_data.get("vrf", {}).get(vrf_key, {})
            af_data = vrf_data.get("address_family", {}).get("ipv4", {})
            all_interfaces = {}
            for instance in af_data.get("instance", {}).values():
                for area in instance.get("areas", {}).values():
                    all_interfaces.update(area.get("interfaces", {}))
            return all_interfaces
        except AttributeError:
            return {}

    def test_connectivity(self) -> bool:
        if not self.target_device.can_connect():
            raise ValueError(f"Connectivity failed for {self.target_device.name}")
        return True

    @depends_on("test_connectivity")
    def test_fetch_interface_telemetry(self) -> bool:
        vrf_name = getattr(self, "vrf", "default") or "default"
        cmd = (
            "show ip ospf interface"
            if vrf_name == "default"
            else f"show ip ospf vrf {vrf_name} interface"
        )

        def safe_parse(device, command):
            try:
                return device.get_genie_device_object().parse(command)
            except Exception:
                return {}

        self.interfaces = self._get_ospf_interfaces(safe_parse(self.target_device, cmd))
        if not self.interfaces:
            raise ValueError("No OSPF-enabled interfaces discovered.")
        return True

    @depends_on("test_fetch_interface_telemetry")
    def test_audit_passive_safety(self) -> bool:
        violations = []
        for name, details in self.interfaces.items():
            is_secured = details.get("passive", False) or details.get(
                "stub_host", False
            )
            nbr_count = details.get("statistics", {}).get("nbr_count", 0)

            if not is_secured and nbr_count == 0:
                violations.append(name)

        if violations:
            raise ValueError(
                f"PASSIVE POLICY ERROR: Interfaces with 0 neighbors must be passive/stub: {violations}"
            )

        return True

    @depends_on("test_audit_passive_safety")
    def test_audit_security_policy(self) -> bool:
        if self.required_auth_type == "Ignore":
            return True

        violations = []
        for name, details in self.interfaces.items():
            if details.get("passive", False) or details.get("stub_host", False):
                continue

            auth_data = details.get("authentication", {})
            if self.required_auth_type == "Simple":
                if "simple_password" not in auth_data:
                    violations.append(f"{name} (Simple Auth missing)")
            elif self.required_auth_type == "Crypto":
                crypto = auth_data.get("auth_trailer_key", {}).get("crypto_algorithm")
                if not crypto:
                    violations.append(f"{name} (Crypto Auth missing)")

        if violations:
            raise ValueError(
                f"SECURITY POLICY ERROR [{self.required_auth_type}]: {violations}"
            )
        return True

    @depends_on("test_audit_security_policy")
    def test_audit_network_optimization(self) -> Union[str, bool]:
        candidates = []
        for name, details in self.interfaces.items():
            int_type = details.get("interface_type", "").lower()
            nbr_count = details.get("statistics", {}).get("nbr_count", 0)

            if int_type == "broadcast" and nbr_count == 1:
                candidates.append(name)

        if candidates:
            return f"OPTIMIZATION: Consider switching {candidates} to 'point-to-point' for faster convergence."

        return True
