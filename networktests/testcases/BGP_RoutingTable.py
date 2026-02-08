import ipaddress
import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class BGP_RoutingTable(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-globe fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">BGP Routing Table</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-info text-dark bg-opacity-75 border border-info border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">BGP / Loc-RIB</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks the BGP routing table on your device.
                        It confirms that specific networks are present and selected as the best path.
                        It can also block any unexpected routes to ensure the table only contains what is allowed.
                    </p>

                    <div class="p-3 rounded border border-info border-opacity-25 bg-info bg-opacity-10">
                        <h6 class="fw-bold text-primary-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It prevents connection issues by ensuring the router prefers the correct paths to outside networks.
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
                                <td class="fw-bold font-monospace">bgp_device <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The device to check</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF instance. Default is global</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">address_family <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">IPv4 or IPv6</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">allow_other_routes <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">If False it fails if extra routes are found</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">entries <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">List of prefixes to validate</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ network <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Destination Network</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ match_strategy <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Exact match or included subnet</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ is_local_origin</td>
                                <td class="text-body-secondary fst-italic">True if route is created locally</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ next_hop</td>
                                <td class="text-body-secondary fst-italic">Expected Next-Hop IP</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ best_option <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Enforce Best-Option or Back-Up-Path</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ expected_origin_as</td>
                                <td class="text-body-secondary fst-italic">Expected Origin Autonomous System</td>
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
            "name": "bgp_device",
            "display_name": "BGP Device",
            "description": "The device from which to check the BGP-Table",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "VRF",
            "type": "str",
            "description": "The name of the VRF, if this route is part of one",
            "requirement": "optional",
        },
        {
            "name": "address_family",
            "display_name": "Address Family",
            "description": "The used Address Family (IPv4|IPv6)",
            "type": "choice",
            "choices": ["IPv4", "IPv6"],
            "default_choice": "IPv4",
            "requirement": "required",
        },
        {
            "name": "entries",
            "display_name": "Entries",
            "type": "list",
            "parameters": [
                {
                    "name": "network",
                    "display_name": "Network",
                    "type": [
                        {"name": "IPv4-CIDR", "condition": {"address_family": "IPv4"}},
                        {"name": "IPv6-CIDR", "condition": {"address_family": "IPv6"}},
                    ],
                    "description": "The destination network of the route",
                    "requirement": "required",
                },
                {
                    "name": "match_strategy",
                    "display_name": "Match Strategy",
                    "type": "choice",
                    "choices": ["Exact", "Included"],
                    "default_choice": "Exact",
                    "description": "The type of match needed for this route to be accepted. Exact: This route needs to be its own entry. Included: This route may be matched if it is a more specific subnet covered by a broader route in the table (the configured network is a sub-prefix of an existing route).",
                    "requirement": "required",
                },
                {
                    "name": "is_local_origin",
                    "display_name": "Local Origin",
                    "type": "choice",
                    "choices": ["True", "False"],
                    "default_choice": "False",
                    "description": "Marks if this route is of local origin",
                },
                {
                    "name": "next_hop",
                    "display_name": "Next-Hop",
                    "type": ["IPv4", "IPv6"],
                    "description": "The next hop of the route",
                    "requirement": "optional",
                    "required_if": {"is_local_origin": "False"},
                },
                {
                    "name": "best_option",
                    "display_name": "Best Path Option",
                    "type": "choice",
                    "choices": ["Ignored", "Best-Option", "Back-Up-Path"],
                    "default_choice": "Ignored",
                    "description": 'Checks if this path is considered the best. (preferred route ">")',
                    "requirement": "required",
                },
                {
                    "name": "expected_origin_as",
                    "display_name": "Expected Origin AS",
                    "type": "positive-number",
                    "description": "Check if the route originated from a specific Autonomous System.",
                    "requirement": "optional",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
        },
        {
            "name": "allow_other_routes",
            "display_name": "Allow Other Routes",
            "type": "choice",
            "choices": ["True", "False"],
            "default_choice": "True",
            "description": "Marks if only the given routes are allowed in the table",
            "requirement": "required",
        },
    ]

    LOCAL_ORIGIN_NEXT_HOPS = ["0.0.0.0", "::", "self"]

    def _search_recursive(self, data: dict, target_key: str):
        if target_key in data:
            return data[target_key]
        for value in (v for v in data.values() if isinstance(v, dict)):
            found = self._search_recursive(value, target_key)
            if found is not None:
                return found
        return None

    def _to_int_str(self, val):
        try:
            return str(int(str(val).strip())) if val is not None else None
        except (ValueError, TypeError):
            return None

    def test_device_connection(self) -> bool:
        if not self.bgp_device.can_connect():
            raise ValueError(f"Connection failed: {self.bgp_device.name}")
        return True

    @depends_on("test_device_connection")
    def test_fetch_bgp_data(self) -> bool:
        family = self.address_family.lower()
        vrf_name = getattr(self, "vrf", "default") or "default"
        context = f"{family} unicast"
        if vrf_name != "default":
            context = f"{context} vrf {vrf_name}"

        genie_dev = self.bgp_device.get_genie_device_object()

        # Cache parsed BGP table and summary data for use in subsequent test methods
        self.raw_table = genie_dev.parse(f"show bgp {context}")
        self.raw_summary = genie_dev.parse(f"show bgp {context} summary")

        self.table_prefixes = self._search_recursive(
            self.raw_table, "prefixes"
        ) or self._search_recursive(self.raw_table, "prefix")

        if not self.table_prefixes:
            raise ValueError(
                f"BGP Table is empty for {context} on {self.bgp_device.name}"
            )

        return True

    @depends_on("test_fetch_bgp_data")
    def test_validate_prefixes(self) -> bool:
        local_as = self._to_int_str(
            self._search_recursive(self.raw_summary, "local_as")
        )
        self.validated_keys = []

        for entry in self.entries:
            target_net = entry["network"]
            strategy = entry["match_strategy"]
            target_obj = ipaddress.ip_network(target_net)

            # Finding a match based on strategy
            matched_key = None
            for p_str in self.table_prefixes:
                if strategy == "Exact":
                    if p_str == target_net:
                        matched_key = p_str
                        break
                else:
                    if "/" in p_str:
                        p_obj = ipaddress.ip_network(p_str)
                    else:
                        # Apply appropriate default prefix length based on IP version
                        default_prefix = 128 if target_obj.version == 6 else 32
                        p_obj = ipaddress.ip_network(f"{p_str}/{default_prefix}")
                    if target_obj.subnet_of(p_obj):
                        matched_key = p_str
                        break

            if not matched_key:
                raise ValueError(
                    f"Prefix {target_net} ({strategy}) not found in Loc-RIB."
                )

            # Path verification
            path_errors = []
            has_valid_path = False
            indices = self.table_prefixes[matched_key].get("index", {}).items()

            for idx, attr in indices:
                current_errors = []

                # Best Path
                is_best = any(
                    [
                        attr.get("bestpath"),
                        attr.get("best"),
                        ">" in str(attr.get("status_codes", "")),
                    ]
                )
                if entry["best_option"] == "Best-Option" and not is_best:
                    current_errors.append("not best-path")
                elif entry["best_option"] == "Back-Up-Path" and is_best:
                    current_errors.append("is best-path (expected backup)")

                # Next-Hop Check
                actual_nh = str(attr.get("next_hop", attr.get("gateway", ""))).strip()
                if entry["is_local_origin"] == "True":
                    if actual_nh not in self.LOCAL_ORIGIN_NEXT_HOPS:
                        current_errors.append(f"not local origin (NH: {actual_nh})")
                elif entry.get("next_hop"):
                    if actual_nh != str(entry["next_hop"]):
                        current_errors.append(
                            f"NH mismatch: Exp {entry['next_hop']}, Got {actual_nh}"
                        )

                # Origin AS Check
                if entry.get("expected_origin_as"):
                    raw_as_path = str(attr.get("route_info", attr.get("as_path", "")))
                    as_list = re.findall(r"\d+", raw_as_path)
                    actual_as = as_list[-1] if as_list else local_as
                    expected_as = self._to_int_str(entry["expected_origin_as"])
                    if actual_as is None:
                        current_errors.append(
                            f"AS mismatch: Exp {entry['expected_origin_as']}, Got <unknown>"
                        )
                    elif actual_as != expected_as:
                        current_errors.append(
                            f"AS mismatch: Exp {entry['expected_origin_as']}, Got {actual_as}"
                        )

                if not current_errors:
                    has_valid_path = True
                    self.validated_keys.append(matched_key)
                    break
                path_errors.append(f"Path #{idx}: {', '.join(current_errors)}")

            if not has_valid_path:
                if path_errors:
                    max_details = 3
                    if len(path_errors) > max_details:
                        detailed = " | ".join(path_errors[:max_details])
                        summary = f"{detailed} | ... and {len(path_errors) - max_details} more path(s) with errors"
                    else:
                        summary = " | ".join(path_errors)
                else:
                    summary = "Unknown path error"

                raise ValueError(f"Route {target_net} failed: {summary}")
        return True

    @depends_on("test_validate_prefixes")
    def test_strict_table_enforcement(self) -> bool:
        if str(self.allow_other_routes) == "True":
            return True

        all_table_keys = set(self.table_prefixes.keys())
        unexpected = all_table_keys - set(self.validated_keys)

        if unexpected:
            unexpected_routes = ", ".join(sorted(str(route) for route in unexpected))
            raise ValueError(
                f"Strict Check Failed. Unexpected routes: {unexpected_routes}"
            )

        return True
