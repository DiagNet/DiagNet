import re
from typing import Any, Dict, List, Optional, Tuple

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class GLBP(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-info text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-layers-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">GLBP</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-info text-dark bg-opacity-75 border border-info border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">FHRP / Routing</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks the status of your Gateway Load Balancing Protocol (GLBP).
                        It verifies that the Active Virtual Gateway is functioning correctly and checks important settings like the Virtual IP, Priority, and Preemption.
                    </p>

                    <div class="p-3 rounded border border-info border-opacity-25 bg-info bg-opacity-10">
                        <h6 class="fw-bold text-info-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures that traffic is balanced across gateways and that a backup is ready if a connection fails.
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
                                <td class="text-body-secondary">The target device to validate GLBP on</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">glbp_groups <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">List of GLBP groups to validate</td>
                            </tr>

                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Interface name where GLBP is configured</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ group_id <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">The GLBP Group ID to inspect</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ expected_avg_state <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Expected AVG Operational State</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ expected_virtual_ip</td>
                                <td class="text-body-secondary fst-italic">Expected Virtual IP Address</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ expected_priority</td>
                                <td class="text-body-secondary fst-italic">Expected GLBP priority value</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ check_preempt</td>
                                <td class="text-body-secondary fst-italic">Validate if preemption is enabled</td>
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
        re_header = re.compile(r"^(?P<intf>\S+)\s+-\s+Group\s+(?P<grp>\d+)")
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
