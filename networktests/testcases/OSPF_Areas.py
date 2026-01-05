import ipaddress
import logging
from typing import Dict, Union

from devices.models import Device
from networktests.testcases.base import DiagNetTest, depends_on
from pyats.async_ import pcall

logging.getLogger("unicon").setLevel(logging.ERROR)
logging.getLogger("genie").setLevel(logging.ERROR)


class OSPF_Areas(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #f59e0b;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">OSPF Areas</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Multi-Area Hierarchy & Validation</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>OSPF_Areas</strong> test class performs a rigorous bidirectional audit of OSPF area configurations.
                It validates that the operational state matches the intended design and enforces fundamental OSPF architectural rules, such as the <strong>Backbone Transit Rule</strong>.
            </p>
        </section>



        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #f59e0b; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Audit Phases
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">1.</span>
                <span><strong>Intent-to-Reality:</strong> Verifies that all areas defined in the design are active on the devices with the correct <strong>Area Type</strong> (Stub, NSSA, etc.) and <strong>Summary</strong> settings.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">2.</span>
                <span><strong>Configuration Drift:</strong> Identifies "Shadow Areas" configured on routers that were not part of the intended design.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #f59e0b; margin-right: 10px;">3.</span>
                <span><strong>Transit Integrity:</strong> Enforces that any router acting as an <strong>ABR</strong> (Area Border Router) has a valid, active physical or virtual path to <strong>Area 0 (Backbone)</strong>.</span>
            </li>
        </ul>

        <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 25px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 15px;">
            Authored by: Luka Pacar
        </p>
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
        """Standardizes Area IDs to integers (e.g., '0.0.0.0' -> 0)."""
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
        """
        Parses OSPF telemetry into a map of configured vs. physically active areas.
        """
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
                    # Transit Logic: Check for physical (non-loopback) interfaces
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
        """Maps user-defined design intent."""
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
        """Parallelized telemetry collection with exception capture."""
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
        """
        Bidirectional Audit: No print statements used. All findings reported via exception.
        """
        audit_errors = []
        target_inst = str(self.ospf_instance)

        for dev_name, intended_areas in self.intended_topology.items():
            raw_data = self.telemetry.get(dev_name, {})

            # 1. Telemetry Health Check
            if "_collection_error" in raw_data:
                audit_errors.append(
                    f"{dev_name}: Telemetry failure ({raw_data['_collection_error']})"
                )
                continue

            op_state = self._get_operational_state(raw_data, target_inst)

            # 2. Instance Existence Check
            if not op_state["found"]:
                audit_errors.append(
                    f"{dev_name}: OSPF Process {target_inst} missing from operational state."
                )
                continue

            # 3. Phase 1: Intent -> Reality (Compliance)
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

            # 4. Phase 2: Reality -> Intent (Drift/Shadow Areas)
            for op_aid in op_state["all_configured_areas"]:
                if op_aid not in intended_areas:
                    audit_errors.append(
                        f"{dev_name}: Configuration Drift - Unintended Area {op_aid} found."
                    )

            # 5. Phase 3: Architectural Integrity (Backbone Rule)
            # If ANY area (intended or unintended) creates an ABR role, backbone is mandatory.
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
            # Raise a single error containing all findings for the framework
            error_report = "\n- " + "\n- ".join(audit_errors)
            raise ValueError(f"OSPF AUDIT FAILED: {error_report}")
