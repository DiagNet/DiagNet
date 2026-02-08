from typing import Any, Dict, List, Optional

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class HSRP(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-info text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-shield-plus fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">HSRP Validation</h3>
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
                        This test checks the status of your HSRP configuration.
                        It confirms that your router is acting as the Active or Standby gateway as expected.
                        It also verifies important settings like the Virtual IP address, Priority, and Preemption.
                    </p>

                    <div class="p-3 rounded border border-info border-opacity-25 bg-info bg-opacity-10">
                        <h6 class="fw-bold text-info-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures that if one router fails, the other takes over immediately to keep the network running.
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
                                <td class="text-body-secondary">The target device to validate HSRP on</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">hsrp_groups <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">List of HSRP groups to validate</td>
                            </tr>

                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ interface <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">The interface where HSRP is configured</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ group_id <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">The HSRP Group ID to inspect</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ expected_state <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">The operational state this device should be in</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ virtual_ip</td>
                                <td class="text-body-secondary fst-italic">The expected Virtual IP address</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ priority</td>
                                <td class="text-body-secondary fst-italic">The expected HSRP priority value</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ preempt</td>
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
