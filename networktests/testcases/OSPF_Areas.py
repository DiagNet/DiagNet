import ipaddress
from typing import Dict, Union

from devices.models import Device
from networktests.testcases.base import DiagNetTest, depends_on
from pyats.async_ import pcall

__author__ = "Luka Pacar"


class OSPF_Areas(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-teal text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #0d9488;">
                    <i class="bi bi-diagram-3-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">OSPF Areas</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white bg-opacity-75 border border-opacity-25" style="background-color: #0f766e; border-color: #0f766e;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">OSPF / Design</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks your OSPF area configuration. It confirms that areas are set up correctly (like Stub or NSSA) and that all routers are assigned to the right areas.
                        It also ensures that the network follows the rules for connecting to the backbone area.
                    </p>

                    <div class="p-3 rounded border border-opacity-25 bg-teal bg-opacity-10" style="border-color: #0d9488;">
                        <h6 class="fw-bold mb-1" style="color: #0d9488;">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It prevents routing issues and ensures traffic flows correctly through the network.
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
                                <td class="fw-bold font-monospace">ospf_instance <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The OSPF Process ID to check</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">area_definitions <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">List defining the Area ID, Type, and Members</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ area_id <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Area ID</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ area_type</td>
                                <td class="text-body-secondary fst-italic">Standard, Stub, Totally Stubby, or NSSA</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ members <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">List of Router objects in this area</td>
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
            "name": "ospf_instance",
            "display_name": "OSPF Instance",
            "type": "positive-number",
            "requirement": "required",
            "description": "The OSPF Instance to check",
        },
        {
            "name": "area_definitions",
            "display_name": "OSPF Area Hierarchy",
            "type": "list",
            "requirement": "required",
            "description": "Define Area IDs, their members, and their intended OSPF types.",
            "parameters": [
                {
                    "name": "area_id",
                    "display_name": "Area ID",
                    "type": "positive-number",
                    "description": "The area in which the given routers are located",
                    "requirement": "required",
                },
                {
                    "name": "area_type",
                    "display_name": "Area Type",
                    "type": "choice",
                    "choices": [
                        "Standard",
                        "Stub Area",
                        "Totally Stubby Area",
                        "Not-So-Stubby Area (NSSA)",
                    ],
                    "default-choice": "Standard",
                    "description": "The type of this area",
                },
                {
                    "name": "members",
                    "display_name": "Area Members",
                    "type": "list",
                    "description": "The routers that are part of this area",
                    "requirement": "required",
                    "parameters": [
                        {
                            "name": "member",
                            "display_name": "Member",
                            "type": "device",
                            "description": "A router which is part of the given area",
                            "requirement": "required",
                        }
                    ],
                    "mutually_exclusive": [],
                    "constraints": [],
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
    ]

    def _normalize_area_id(self, area_id: Union[str, int]) -> int:
        try:
            area_str = str(area_id).upper().strip()
            if any(x in area_str for x in ["BACKBONE", "0.0.0.0"]) or area_str == "0":
                return 0
            return (
                int(ipaddress.IPv4Address(area_str))
                if "." in area_str
                else int(area_str)
            )
        except Exception:
            return -1

    def _get_operational_state(self, dev_data: Dict, target_instance: str) -> Dict:
        state = {
            "found": False,
            "all_configured_areas": set(),
            "physically_active_areas": set(),
            "has_virtual_bb": False,
            "area_details": {},
        }

        target_inst_str = str(target_instance)
        vrfs = dev_data.get("vrf", {})

        for vrf_data in vrfs.values():
            af_v4 = vrf_data.get("address_family", {}).get("ipv4", {})
            instances = af_v4.get("instance", {})

            if target_inst_str in instances:
                inst_data = instances[target_inst_str]
                state["found"] = True
                if inst_data.get("virtual_links"):
                    state["has_virtual_bb"] = True

                for aid_key, area_data in inst_data.get("areas", {}).items():
                    norm_id = self._normalize_area_id(aid_key)
                    state["all_configured_areas"].add(norm_id)

                    stats = area_data.get("statistics", {})
                    # Check for physical (non-loopback) interfaces
                    phys_count = stats.get("interfaces_count", 0) - stats.get(
                        "loopback_count", 0
                    )

                    if phys_count > 0:
                        state["physically_active_areas"].add(norm_id)

                    state["area_details"][norm_id] = {
                        "active": phys_count > 0,
                        "type": area_data.get("area_type", "normal").lower(),
                        "no_summary": stats.get("stub_no_summary")
                        or stats.get("nssa_no_summary"),
                    }
        return state

    def test_analyze_intent(self):
        self.intended_topology = {}
        self.area_intent_details = {}
        type_map = {
            "Standard": "normal",
            "Stub Area": "stub",
            "Totally Stubby Area": "stub",
            "Not-So-Stubby Area (NSSA)": "nssa",
        }

        for area_def in self.area_definitions:
            aid = self._normalize_area_id(area_def["area_id"])
            a_type = type_map.get(area_def["area_type"])
            no_summ = "Totally" in area_def["area_type"]

            for member_entry in area_def["members"]:
                dev_name = member_entry["member"].name
                self.intended_topology.setdefault(dev_name, set()).add(aid)
                self.area_intent_details.setdefault(dev_name, {})[aid] = {
                    "type": a_type,
                    "no_summary": no_summ,
                }

    @depends_on("test_analyze_intent")
    def test_collect_telemetry(self):
        unique_devices = {
            m["member"].name: m["member"]
            for a in self.area_definitions
            for m in a["members"]
        }
        device_list = list(unique_devices.values())

        def _fetch(device: Device):
            try:
                return device.get_genie_device_object().parse("show ip ospf")
            except Exception as e:
                return {"_collection_error": str(e)}

        results = pcall(_fetch, device=device_list)
        self.telemetry = {dev.name: res for dev, res in zip(device_list, results)}

    @depends_on("test_collect_telemetry")
    def test_verify_architectural_compliance(self):
        audit_errors = []
        target_inst = str(self.ospf_instance)

        for dev_name, intended_areas in self.intended_topology.items():
            raw_data = self.telemetry.get(dev_name, {})

            if "_collection_error" in raw_data:
                audit_errors.append(
                    f"{dev_name}: Telemetry failure ({raw_data['_collection_error']})"
                )
                continue

            op_state = self._get_operational_state(raw_data, target_inst)

            # Instance Existence Check
            if not op_state["found"]:
                audit_errors.append(
                    f"{dev_name}: OSPF Process {target_inst} missing from operational state."
                )
                continue

            # Intent -> Reality
            for aid in intended_areas:
                if aid not in op_state["area_details"]:
                    audit_errors.append(
                        f"{dev_name}: Intended Area {aid} missing from config."
                    )
                    continue

                actual = op_state["area_details"][aid]
                if not actual["active"]:
                    audit_errors.append(
                        f"{dev_name}: Area {aid} Inactive (No transit adjacencies possible)."
                    )

                intent = self.area_intent_details[dev_name][aid]
                if actual["type"] != intent["type"]:
                    audit_errors.append(
                        f"{dev_name} Area {aid}: Type Mismatch (Design={intent['type']}, Live={actual['type']})"
                    )
                if intent["no_summary"] and not actual["no_summary"]:
                    audit_errors.append(f"{dev_name} Area {aid}: Missing 'no-summary'.")

            # Reality -> Intent
            for op_aid in op_state["all_configured_areas"]:
                if op_aid not in intended_areas:
                    audit_errors.append(
                        f"{dev_name}: Configuration Drift - Unintended Area {op_aid} found."
                    )

            # When more than 1 area is connected -> Needs connection to Backbone Area
            if len(op_state["all_configured_areas"]) > 1:
                has_bb = (0 in op_state["physically_active_areas"]) or op_state[
                    "has_virtual_bb"
                ]
                if not has_bb:
                    audit_errors.append(
                        f"{dev_name}: ARCHITECTURAL VIOLATION. Bridging areas {op_state['all_configured_areas']} "
                        f"without active Area 0 transit."
                    )

        if audit_errors:
            error_report = "\n- " + "\n- ".join(audit_errors)
            raise ValueError(f"OSPF AUDIT FAILED: {error_report}")
