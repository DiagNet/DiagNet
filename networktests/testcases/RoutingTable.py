import ipaddress
from typing import Any, Dict, Optional

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class RoutingTable(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-purple text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px; background-color: #6f42c1;">
                    <i class="bi bi-signpost-split fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Global Routing Table</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge text-white bg-opacity-75 border border-opacity-25" style="background-color: #59359a; border-color: #59359a;">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Routing / Forwarding</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks the Global Routing Table to ensure the device has the correct paths to reach specific networks.
                        It validates that routes learned from protocols like OSPF or BGP are actually installed and active, checking details like the next hop IP and outgoing interface.
                    </p>

                    <div class="p-3 rounded border border-opacity-25 bg-purple bg-opacity-10" style="border-color: #6f42c1;">
                        <h6 class="fw-bold mb-1" style="color: #59359a;">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It confirms that the router knows exactly where to send traffic to reach its destination.
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
                                <td class="text-body-secondary">The network device to query</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">The Virtual Routing and Forwarding instance</td>
                            </tr>
                             <tr>
                                <td class="fw-bold font-monospace">address_family <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The IP version. IPv4 or IPv6</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">routes <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">A list of specific route entries to verify</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ network <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">The destination prefix</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ match_strategy <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Exact match or check if included in a subnet</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ protocol</td>
                                <td class="text-body-secondary fst-italic">The source protocol like OSPF or BGP</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ next_hop</td>
                                <td class="text-body-secondary fst-italic">The specific IP address of the next gateway</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ outgoing_interface</td>
                                <td class="text-body-secondary fst-italic">The interface traffic leaves through</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ metric</td>
                                <td class="text-body-secondary fst-italic">The cost value of the route</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ preference</td>
                                <td class="text-body-secondary fst-italic">The Administrative Distance</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ tag</td>
                                <td class="text-body-secondary fst-italic">The numeric tag associated with the route</td>
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
