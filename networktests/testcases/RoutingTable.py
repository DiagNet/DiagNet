import ipaddress
from typing import Any, Dict, Optional

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class RoutingTable(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #4c1d95 0%, #6d28d9 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #8b5cf6;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">Global Routing Table</h2>
            <p style="color: #e9d5ff; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">RIB State Consistency & Path Verification</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>RoutingTable</strong> test class serves as the ultimate source of truth for the device's forwarding logic.
                Unlike protocol-specific tests, this validates the <strong>Global RIB</strong> (Routing Information Base), ensuring that learned routes are actually installed and selectable for traffic forwarding.
            </p>
        </section>

        <h4 style="color: #2e1065; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #8b5cf6; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Validation Scope
        </h4>
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background: #f5f3ff; padding: 15px; border-radius: 8px; border-left: 4px solid #7c3aed;">
                <strong style="color: #4c1d95;">Protocol Agnostic</strong><br>
                <span style="font-size: 0.85rem; color: #5b21b6;">Validates routes from any source: Connected, Static, OSPF, BGP, EIGRP, or ISIS within IPv4 or IPv6 families.</span>
            </div>
            <div style="flex: 1; background: #f5f3ff; padding: 15px; border-radius: 8px; border-left: 4px solid #8b5cf6;">
                <strong style="color: #4c1d95;">Deep Attribute Check</strong><br>
                <span style="font-size: 0.85rem; color: #5b21b6;">Enforces strict compliance for Metric, Administrative Distance (Preference), and Route Tags.</span>
            </div>
        </div>

        <h4 style="color: #2e1065; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #8b5cf6; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Pillars
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #7c3aed; margin-right: 10px;">✔</span>
                <span><strong>Flexible Matching:</strong> Supports <code>Exact</code> CIDR matching or <code>Included</code> logic to verify subnet existence within aggregates.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #7c3aed; margin-right: 10px;">✔</span>
                <span><strong>Path Precision:</strong> Validates specific <strong>Next-Hop IPs</strong> and <strong>Outgoing Interfaces</strong> to prevent sub-optimal routing (ECMP validation supported).</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #7c3aed; margin-right: 10px;">✔</span>
                <span><strong>Policy Compliance:</strong> Confirms that Route Tags and Admin Distances are preserved correctly across redistribution points.</span>
            </li>
        </ul>

        <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 25px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 15px;">
            Authored by: Luka Pacar
        </p>
    </div>
    """
    _params = [
        {
            "name": "device",
            "display_name": "Device",
            "type": "device",
            "description": "The network device to query the routing table from.",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "VRF",
            "type": "str",
            "default": "default",
            "description": "The Virtual Routing and Forwarding instance to inspect.",
            "requirement": "optional",
        },
        {
            "name": "address_family",
            "display_name": "Address Family",
            "type": "choice",
            "choices": ["IPv4", "IPv6"],
            "default_choice": "IPv4",
            "description": "The IP protocol version to validate (IPv4 or IPv6).",
            "requirement": "required",
        },
        {
            "name": "routes",
            "display_name": "Routes to Validate",
            "type": "list",
            "description": "A list of specific route entries to verify in the table.",
            "requirement": "required",
            "parameters": [
                {
                    "name": "network",
                    "display_name": "Network",
                    "type": [
                        {"name": "IPv4-CIDR", "condition": {"address_family": "IPv4"}},
                        {"name": "IPv6-CIDR", "condition": {"address_family": "IPv6"}},
                    ],
                    "description": "The destination prefix (CIDR notation) to look for.",
                    "requirement": "required",
                },
                {
                    "name": "match_strategy",
                    "display_name": "Match Strategy",
                    "type": "choice",
                    "choices": ["Exact", "Included"],
                    "default_choice": "Exact",
                    "description": "Exact: Matches the prefix string exactly. Included: Checks if the defined network is a subnet of an existing route.",
                    "requirement": "required",
                },
                {
                    "name": "protocol",
                    "display_name": "Protocol",
                    "type": "choice",
                    "choices": [
                        "Ignore",
                        "connected",
                        "static",
                        "ospf",
                        "bgp",
                        "eigrp",
                        "isis",
                        "rip",
                        "local",
                    ],
                    "default_choice": "Ignore",
                    "description": "The expected source protocol of the route.",
                    "requirement": "optional",
                },
                {
                    "name": "next_hop",
                    "display_name": "Next Hop IP",
                    "type": ["IPv4", "IPv6"],
                    "description": "The specific IP address of the next-hop gateway.",
                    "requirement": "optional",
                },
                {
                    "name": "outgoing_interface",
                    "display_name": "Outgoing Interface",
                    "type": "cisco-interface",
                    "description": "The expected egress interface for this route.",
                    "requirement": "optional",
                },
                {
                    "name": "metric",
                    "display_name": "Metric",
                    "type": "positive-number",
                    "description": "The exact metric value associated with the route.",
                    "requirement": "optional",
                },
                {
                    "name": "preference",
                    "display_name": "Admin Distance",
                    "type": "positive-number",
                    "description": "The Administrative Distance (preference) of the route.",
                    "requirement": "optional",
                },
                {
                    "name": "tag",
                    "display_name": "Route Tag",
                    "type": "positive-number",
                    "description": "The numeric tag associated with the route.",
                    "requirement": "optional",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
    ]

    @staticmethod
    def _get_route_entry(
            all_routes: Dict[str, Any],
        target: str,
        strategy: str,
    ) -> Optional[Dict[str, Any]]:
        if strategy == "Exact":
            return all_routes.get(target)

        target_net = ipaddress.ip_network(target)
        for route_prefix, route_data in all_routes.items():
            try:
                current_net = ipaddress.ip_network(route_prefix)
                if target_net.subnet_of(current_net):
                    return route_data
            except ValueError:
                continue
        return None

    @staticmethod
    def _normalize_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def test_device_connection(self) -> bool:
        if not self.device.can_connect():
            raise ValueError(f"Connection failed: {self.device.name}")
        return True

    @depends_on("test_device_connection")
    def test_fetch_routing_data(self) -> bool:
        family_map = {"IPv4": "ip", "IPv6": "ipv6"}
        fam = family_map.get(self.address_family, "ip")
        vrf_name = getattr(self, "vrf", "default") or "default"

        cmd = f"show {fam} route"
        if vrf_name != "default":
            cmd += f" vrf {vrf_name}"

        genie_dev = self.device.get_genie_device_object()
        raw_output = genie_dev.parse(cmd)

        try:
            fam_key = "ipv6" if fam == "ipv6" else "ipv4"
            self.route_table = raw_output["vrf"][vrf_name]["address_family"][fam_key][
                "routes"
            ]
        except KeyError:
            raise ValueError(f"No routing table found for VRF {vrf_name} / {fam_key}")

        return True

    @depends_on("test_fetch_routing_data")
    def test_validate_routes(self) -> bool:
        # Safety check: if no routes are provided, pass the test
        if not getattr(self, "routes", None):
            return True

        failures = []

        for requirement in self.routes:
            target_net = str(requirement["network"])
            strategy = requirement["match_strategy"]

            entry = self._get_route_entry(self.route_table, target_net, strategy)

            if not entry:
                failures.append(f"Route {target_net} ({strategy}) not found")
                continue

            errors = []

            # Protocol Validation
            req_proto = requirement.get("protocol", "Ignore")
            if req_proto != "Ignore":
                actual_proto = str(entry.get("source_protocol", "")).lower()
                if req_proto.lower() != actual_proto:
                    errors.append(
                        f"Protocol mismatch: Exp {req_proto}, Got {actual_proto}"
                    )

            nh_data = entry.get("next_hop", {})

            # Next Hop IP Check
            req_nh = requirement.get("next_hop")
            if req_nh:
                req_nh = str(req_nh)
                found_nh = False
                nh_list = nh_data.get("next_hop_list", {})

                for nh_entry in nh_list.values():
                    if nh_entry.get("next_hop") == req_nh:
                        found_nh = True
                        break

                # Some parsers put next hop directly, not in a map
                if not found_nh and nh_data.get("next_hop") == req_nh:
                    found_nh = True

                if not found_nh:
                    errors.append(f"Next-Hop {req_nh} not found in path list")

            # Outgoing Interface Check
            req_int = requirement.get("outgoing_interface")
            if req_int:
                req_int = str(req_int)
                found_int = False
                out_interfaces = nh_data.get("outgoing_interface", {})
                if req_int in out_interfaces:
                    found_int = True

                if not found_int:
                    nh_list = nh_data.get("next_hop_list", {})
                    for nh_entry in nh_list.values():
                        if nh_entry.get("outgoing_interface") == req_int:
                            found_int = True
                            break

                if not found_int:
                    errors.append(f"Outgoing Interface {req_int} not found")

            # Metric
            req_metric = self._normalize_int(requirement.get("metric"))
            if req_metric is not None:
                actual_metric = self._normalize_int(entry.get("metric"))
                if actual_metric != req_metric:
                    errors.append(
                        f"Metric mismatch: Exp {req_metric}, Got {actual_metric}"
                    )

            # Administrative Distance
            req_pref = self._normalize_int(requirement.get("preference"))
            if req_pref is not None:
                # Some parsers have it as "distance", some as "route_preference"
                actual_pref = self._normalize_int(entry.get("route_preference"))
                if actual_pref is None:
                    actual_pref = self._normalize_int(entry.get("distance"))

                if actual_pref != req_pref:
                    errors.append(
                        f"Preference mismatch: Expected: {req_pref}, Got: {actual_pref}"
                    )

            # Tag
            req_tag = self._normalize_int(requirement.get("tag"))
            if req_tag is not None:
                actual_tag = self._normalize_int(entry.get("tag"))
                if actual_tag != req_tag:
                    errors.append(f"Tag mismatch: Exp {req_tag}, Got {actual_tag}")

            if errors:
                failures.append(f"Route {target_net}: " + ", ".join(errors))

        if failures:
            raise ValueError("\n".join(failures))

        return True