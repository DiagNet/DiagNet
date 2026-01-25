from typing import Any, Dict, List, Optional

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class HSRP(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #9a3412;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">HSRP State Validation</h2>
            <p style="color: #fed7aa; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Availability & Redundancy Check</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>HSRP_State</strong> test class validates the First Hop Redundancy Protocol status.
                It ensures that routers are correctly assuming their <strong>Active</strong> or <strong>Standby</strong> roles and that attributes like Priority and Virtual IP are consistent with the design.
            </p>
        </section>

        <h4 style="color: #9a3412; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #ea580c; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Pillars
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #ea580c; margin-right: 10px;">✔</span>
                <span><strong>Role Enforcement:</strong> Strict validation of <code>Active</code>, <code>Standby</code>, or <code>Listen</code> states per group.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #ea580c; margin-right: 10px;">✔</span>
                <span><strong>Configuration Consistency:</strong> Checks <code>Priority</code>, <code>Preemption</code>, and <code>Virtual IP</code> against expectations.</span>
            </li>
        </ul>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "Target Device",
            "type": "device",
            "description": "The device to validate HSRP on.",
            "requirement": "required",
        },
        {
            "name": "hsrp_groups",
            "display_name": "HSRP Groups",
            "type": "list",
            "description": "A list of HSRP groups and their expected operational state.",
            "requirement": "required",
            "parameters": [
                {
                    "name": "interface",
                    "display_name": "Interface",
                    "type": "cisco-interface",
                    "description": "The interface where HSRP is configured (e.g., GigabitEthernet0/0).",
                    "requirement": "required",
                },
                {
                    "name": "group_id",
                    "display_name": "Group ID",
                    "type": "positive-number",
                    "description": "The HSRP Group ID to inspect.",
                    "requirement": "required",
                },
                {
                    "name": "expected_state",
                    "display_name": "Expected State",
                    "type": "choice",
                    "choices": ["Active", "Standby", "Listen", "Init"],
                    "default_choice": "Active",
                    "description": "The operational state this device should be in.",
                    "requirement": "required",
                },
                {
                    "name": "virtual_ip",
                    "display_name": "Virtual IP",
                    "type": "IPv4",
                    "description": "Optional: The expected Virtual IP address.",
                    "requirement": "optional",
                },
                {
                    "name": "priority",
                    "display_name": "Priority",
                    "type": "positive-number",
                    "description": "Optional: The expected HSRP priority value.",
                    "requirement": "optional",
                },
                {
                    "name": "preempt",
                    "display_name": "Preempt Enabled",
                    "type": "choice",
                    "choices": ["Ignore", "True", "False"],
                    "default_choice": "Ignore",
                    "description": "Optional: Validate if preemption is enabled.",
                    "requirement": "optional",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
    ]

    def _normalize_int(self, value: Any) -> Optional[int]:
        try:
            return int(str(value).strip())
        except (ValueError, TypeError):
            return None

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(f"Connection failed: {self.device.name}")
        return True

    @depends_on("test_device_connection")
    def test_fetch_hsrp_data(self) -> bool:
        # Fetch operational data
        cmd = "show standby all"
        try:
            self.op_data = self.device.get_genie_device_object().parse(cmd)
        except Exception as e:
            raise ValueError(f"Failed to parse '{cmd}': {str(e)}")
        return True

    @depends_on("test_fetch_hsrp_data")
    def test_validate_hsrp_status(self) -> bool:
        if not self.hsrp_groups:
            return True

        errors: List[str] = []

        for entry in self.hsrp_groups:
            iface_name = entry.get("interface")
            group_id = self._normalize_int(entry.get("group_id"))

            # Parameter Parsing & Defaults
            exp_state = entry.get("expected_state", "").lower()
            exp_vip = entry.get("virtual_ip")
            exp_prio = self._normalize_int(entry.get("priority"))
            exp_preempt = entry.get("preempt", "Ignore")

            # 1. Locate Interface
            if iface_name not in self.op_data:
                errors.append(f"[{iface_name}] Interface not found in HSRP output.")
                continue

            # 2. Locate Group
            group_data = self._find_hsrp_group_data(self.op_data[iface_name], group_id)

            if not group_data:
                errors.append(
                    f"[{iface_name}] HSRP Group {group_id} not configured/found."
                )
                continue

            # 3. Validate State
            actual_state = str(group_data.get("hsrp_router_state", "unknown")).lower()
            if actual_state != exp_state:
                errors.append(
                    f"[{iface_name} Grp {group_id}] State Mismatch: "
                    f"Expected '{exp_state.upper()}', Got '{actual_state.upper()}'"
                )

            # 4. Validate Virtual IP
            if exp_vip:
                # Structure: 'primary_ipv4_address': {'address': '192.168.0.254'}
                actual_vip = group_data.get("primary_ipv4_address", {}).get(
                    "address", ""
                )
                if actual_vip != exp_vip:
                    errors.append(
                        f"[{iface_name} Grp {group_id}] VIP Mismatch: "
                        f"Expected {exp_vip}, Got {actual_vip}"
                    )

            # 5. Validate Priority
            if exp_prio is not None:
                actual_prio = self._normalize_int(group_data.get("priority"))
                if actual_prio != exp_prio:
                    errors.append(
                        f"[{iface_name} Grp {group_id}] Priority Mismatch: "
                        f"Expected {exp_prio}, Got {actual_prio}"
                    )

            # 6. Validate Preemption
            if exp_preempt in ["True", "False"]:
                should_preempt = exp_preempt == "True"
                actual_preempt = group_data.get("preempt", False)

                # Some parsers return 'enabled' string or boolean
                if isinstance(actual_preempt, str):
                    actual_preempt = actual_preempt.lower() in [
                        "true",
                        "enabled",
                        "yes",
                    ]

                if actual_preempt != should_preempt:
                    errors.append(
                        f"[{iface_name} Grp {group_id}] Preempt Mismatch: "
                        f"Expected {should_preempt}, Got {actual_preempt}"
                    )

        if errors:
            raise ValueError("\n".join(errors))

        return True

    def _find_hsrp_group_data(
        self, iface_data: Dict[str, Any], target_group: int
    ) -> Optional[Dict[str, Any]]:
        af_data = iface_data.get("address_family", {}).get("ipv4", {})
        versions = af_data.get("version", {})

        for ver_id, ver_data in versions.items():
            groups = ver_data.get("groups", {})
            if target_group in groups:
                return groups[target_group]

        return None
