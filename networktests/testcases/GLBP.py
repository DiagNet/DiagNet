import re
from typing import Any, Dict, List, Optional, Tuple

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class GLBP(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #075985;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">GLBP State Validation</h2>
            <p style="color: #bae6fd; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">AVG Status & Load Balancing Audit</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>GLBP_State</strong> test class validates the Gateway Load Balancing Protocol status.
                Unlike HSRP, it distinguishes between the <strong>AVG</strong> (Active Virtual Gateway) and <strong>AVF</strong> (Active Virtual Forwarder) roles.
                This test focuses on ensuring the AVG is correctly elected and parameters match the design.
            </p>
        </section>

        <h4 style="color: #0369a1; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #0284c7; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Pillars
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #0284c7; margin-right: 10px;">✔</span>
                <span><strong>AVG Election:</strong> Verifies the router's role (<code>Active</code>, <code>Standby</code>, or <code>Listen</code>) for the control plane.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #0284c7; margin-right: 10px;">✔</span>
                <span><strong>Integrity Check:</strong> Validates <code>Virtual IP</code>, <code>Priority</code>, and <code>Preemption</code> settings against the intent.</span>
            </li>
        </ul>
    </div>
    """

    _params = [
        {
            "name": "device",
            "display_name": "Target Device",
            "type": "device",
            "description": "The device to validate GLBP on.",
            "requirement": "required",
        },
        {
            "name": "glbp_groups",
            "display_name": "GLBP Groups",
            "type": "list",
            "description": "A list of GLBP groups and their expected operational state.",
            "requirement": "required",
            "parameters": [
                {
                    "name": "interface",
                    "display_name": "Interface",
                    "type": "cisco-interface",
                    "description": "The interface where GLBP is configured (e.g., GigabitEthernet0/0).",
                    "requirement": "required",
                },
                {
                    "name": "group_id",
                    "display_name": "Group ID",
                    "type": "positive-number",
                    "description": "The GLBP Group ID to inspect.",
                    "requirement": "required",
                },
                {
                    "name": "expected_avg_state",
                    "display_name": "Expected AVG State",
                    "type": "choice",
                    "choices": ["Active", "Standby", "Listen", "Speak", "Init"],
                    "default_choice": "Active",
                    "description": "The expected state of the AVG (Gateway role).",
                    "requirement": "required",
                },
                {
                    "name": "expected_virtual_ip",
                    "display_name": "Virtual IP",
                    "type": "IPv4",
                    "description": "Optional: The expected Virtual IP address.",
                    "requirement": "optional",
                },
                {
                    "name": "expected_priority",
                    "display_name": "Priority",
                    "type": "positive-number",
                    "description": "Optional: The expected GLBP priority value.",
                    "requirement": "optional",
                },
                {
                    "name": "check_preempt",
                    "display_name": "Preempt Enabled",
                    "type": "choice",
                    "choices": ["Ignore", "Yes", "No"],
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

    def _parse_glbp_output(self, output: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
        data = {}
        current_key = None
        parsing_avg_section = False

        # Regex Patterns
        re_header = re.compile(r"^(?P<intf>[\w/]+)\s+-\s+Group\s+(?P<grp>\d+)")
        re_state = re.compile(r"^\s+State is\s+(?P<state>\w+)")
        re_vip = re.compile(r"^\s+Virtual IP address is\s+(?P<vip>[\d\.]+)")
        re_prio = re.compile(r"^\s+Priority\s+(?P<prio>\d+)")
        re_preempt = re.compile(r"^\s+Preemption\s+(?P<status>\w+)")
        re_forwarder_block = re.compile(r"^\s+Forwarder\s+\d+")

        for line in output.splitlines():
            line = line.rstrip()

            # 1. Header Detection
            m_header = re_header.match(line)
            if m_header:
                current_key = (m_header.group("intf"), m_header.group("grp"))
                data[current_key] = {}
                parsing_avg_section = True
                continue

            if not current_key:
                continue

            # 2. Block Forwarder Section
            if re_forwarder_block.match(line):
                parsing_avg_section = False
                continue

            # 3. Parse AVG Attributes
            if parsing_avg_section:
                m_state = re_state.match(line)
                if m_state:
                    data[current_key]["state"] = m_state.group("state")
                    continue

                m_vip = re_vip.match(line)
                if m_vip:
                    data[current_key]["vip"] = m_vip.group("vip")
                    continue

                m_prio = re_prio.match(line)
                if m_prio:
                    data[current_key]["priority"] = int(m_prio.group("prio"))
                    continue

                m_preempt = re_preempt.match(line)
                if m_preempt:
                    data[current_key]["preemption"] = m_preempt.group("status")
                    continue

        return data

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(
                f"CRITICAL: Could not connect to device {self.device.name}."
            )
        return True

    @depends_on("test_device_connection")
    def test_fetch_glbp_data(self) -> bool:
        cmd = "show glbp"
        try:
            # Execute Raw Command
            raw_output = self.device.get_genie_device_object().execute(cmd)
            self.parsed_data = self._parse_glbp_output(raw_output)
        except Exception as e:
            raise ValueError(
                f"Execution Failed: Could not run '{cmd}' on {self.device.name}. Error: {str(e)}"
            )
        return True

    @depends_on("test_fetch_glbp_data")
    def test_validate_glbp_states(self) -> bool:
        if not self.glbp_groups:
            return True

        errors: List[str] = []

        for entry in self.glbp_groups:
            iface_name = entry.get("interface")
            group_id = str(self._normalize_int(entry.get("group_id")))

            exp_state = entry.get("expected_avg_state")
            exp_vip = entry.get("expected_virtual_ip")
            exp_prio = self._normalize_int(entry.get("expected_priority"))
            check_preempt = entry.get("check_preempt", "Ignore")

            key = (iface_name, group_id)

            # 1. Validation: Group Existence
            if key not in self.parsed_data:
                errors.append(
                    f"{self.device.name} [{iface_name} Group {group_id}] CONFIG MISSING: "
                    f"The GLBP group is not present in 'show glbp' output."
                )
                continue

            group_data = self.parsed_data[key]

            # 2. Validation: AVG State
            act_state = group_data.get("state", "Unknown")
            if exp_state and act_state.lower() != exp_state.lower():
                errors.append(
                    f"{self.device.name} [{iface_name} Group {group_id}] STATE CRITICAL: "
                    f"Expected '{exp_state}', but device is currently '{act_state}'. "
                    f"Check physical link or neighbor availability."
                )

            # 3. Validation: Virtual IP
            act_vip = group_data.get("vip")
            if exp_vip and act_vip != exp_vip:
                errors.append(
                    f"{self.device.name} [{iface_name} Group {group_id}] VIP INVALID: "
                    f"Expected Virtual IP '{exp_vip}', but found '{act_vip}'."
                )

            # 4. Validation: Priority
            act_prio = group_data.get("priority")
            if exp_prio is not None:
                if act_prio != exp_prio:
                    errors.append(
                        f"{self.device.name} [{iface_name} Group {group_id}] PRIORITY MISMATCH: "
                        f"Configured priority is {act_prio}, but expected {exp_prio}."
                    )

            # 5. Validation: Preemption
            act_preempt_str = group_data.get("preemption", "disabled")
            act_preempt_enabled = act_preempt_str.lower() == "enabled"

            if check_preempt == "Yes" and not act_preempt_enabled:
                errors.append(
                    f"{self.device.name} [{iface_name} Group {group_id}] POLICY VIOLATION: "
                    f"Preemption is REQUIRED but currently DISABLED."
                )
            elif check_preempt == "No" and act_preempt_enabled:
                errors.append(
                    f"{self.device.name} [{iface_name} Group {group_id}] POLICY VIOLATION: "
                    f"Preemption is FORBIDDEN but currently ENABLED."
                )

        if errors:
            raise ValueError("\n".join(errors))

        return True
