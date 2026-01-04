from networktests.testcases.base import DiagNetTest, depends_on
from typing import Union

__author__ = "Luka Pacar"


class OSPF_Interfaces(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #f59e0b;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">OSPF Interfaces</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Passive-First Policy & Security Auditor</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>OSPF_Interfaces</strong> test class performs a rigorous audit of OSPF interface states.
                It enforces a "Passive-First" logic, ensuring that edge segments are secured before transit security policies are evaluated.
            </p>
        </section>

        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #f59e0b; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Audit Hierarchy
        </h4>
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #cbd5e1;">
                <strong style="color: #334155;">Passive Enforcement</strong><br>
                <span style="font-size: 0.85rem; color: #64748b;">Any interface with zero active neighbors must be passive to prevent rogue adjacencies and CPU waste.</span>
            </div>
            <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                <strong style="color: #334155;">Transit Security</strong><br>
                <span style="font-size: 0.85rem; color: #64748b;">Enforce Cryptographic or Simple authentication specifically on active, non-passive transit links.</span>
            </div>
        </div>

        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #f59e0b; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Pillars
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">✔</span>
                <span><strong>Security Compliance:</strong> Supports granular enforcement of authentication levels, allowing for per-network policy adjustments.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">✔</span>
                <span><strong>Topology Optimization:</strong> Automatically identifies 'Broadcast' segments that should logically be 'Point-to-Point' for faster convergence.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">✔</span>
                <span><strong>Silent Interface Detection:</strong> Hard-fails on active interfaces that lack neighbors, identifying potential configuration oversights.</span>
            </li>
        </ul>

        <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 25px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 15px;">
            Authored by: Luka Pacar
        </p>
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
