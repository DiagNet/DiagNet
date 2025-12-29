import ipaddress
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class BGP_RoutingTable(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family:Arial,sans-serif; line-height:1.5; max-width:800px;">
        <h2 class="mb-3">BGP_RoutingTable Test Class</h2>
        <p>
            The <strong>BGP_RoutingTable</strong> test class inspects the BGP Loc-RIB (BGP Table) of a network device.
            It validates the presence, attributes, and selection status of specific network prefixes.
        </p>

        <h4 class="mt-4 mb-2">Purpose</h4>
        <p>
            This test ensures that a device is receiving or originating the correct BGP routes. It goes beyond simple reachability
            by verifying protocol-specific details like Next-Hop, Origin AS, and Best-Path selection, making it essential for
            validating routing policy and redundancy.
        </p>

        <h4 class="mt-4 mb-2">Parameters</h4>

        <h5 class="mt-3">Global Parameters</h5>
        <ul class="list-group mb-3">
            <li class="list-group-item">
                <strong>BGP Device</strong> (<em>Device</em>)<br>
                The network device whose BGP table will be inspected.
            </li>
            <li class="list-group-item">
                <strong>Address Family</strong> (<em>choice</em>)<br>
                The protocol version to check. Choices: IPv4, IPv6.
            </li>
            <li class="list-group-item">
                <strong>VRF</strong> (<em>string</em>)<br>
                Optional. Specify the Virtual Routing and Forwarding instance. Default is the global routing table.
            </li>
            <li class="list-group-item">
                <strong>Allow Other Routes</strong> (<em>choice</em>)<br>
                If set to "False", the test will fail if any routes exist in the BGP table that are not defined in the Entries list.
            </li>
        </ul>

        <h5 class="mt-3">Entry-Specific Parameters</h5>
        <p>Multiple entries can be checked in a single test run. Each entry includes:</p>
        <ul class="list-group mb-3">
            <li class="list-group-item">
                <strong>Network</strong> (<em>CIDR</em>)<br>
                The prefix to search for (e.g., 10.0.0.0/24 or 2001:db8::/32).
            </li>
            <li class="list-group-item">
                <strong>Match Strategy</strong> (<em>choice</em>)<br>
                <strong>Exact:</strong> The prefix must match the table entry exactly.<br>
                <strong>Included:</strong> The prefix is valid if it is a subset of a larger aggregate in the table.
            </li>
            <li class="list-group-item">
                <strong>Best Path Option</strong> (<em>choice</em>)<br>
                Verifies if the route is the "Best" path (marked with &gt;), a "Back-Up" path, or if selection status should be ignored.
            </li>
            <li class="list-group-item">
                <strong>Next-Hop / Local Origin</strong><br>
                Validates if the route is locally originated (0.0.0.0) or learned via a specific neighbor IP.
            </li>
        </ul>

        <h4 class="mt-4 mb-2">How it Works</h4>
        <ol>
            <li>The test connects to the specified <strong>BGP Device</strong>.</li>
            <li>It retrieves the BGP table filtered by the chosen <strong>Address Family</strong> and <strong>VRF</strong>.</li>
            <li>For each network in the <strong>Entries</strong> list, it performs a lookup based on the <strong>Match Strategy</strong>.</li>
            <li>It compares the actual BGP attributes (Next-Hop, Best-Path flag, Origin AS) against the expected parameters.</li>
        </ol>

        <h4 class="mt-4 mb-2">Why Use This Test</h4>
        <ul>
            <li>Confirm that the device is learning prefixes from the correct upstream neighbors.</li>
            <li>Verify that local network advertisements are active in the BGP process.</li>
            <li>Validate path redundancy by ensuring back-up routes are present but not selected as best.</li>
            <li>Enforce "Strict Table" policies by alerting on unexpected external route leaks.</li>
        </ul>
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
                    "name": "match-strategy",
                    "display_name": "Match Strategy",
                    "type": "choice",
                    "choices": ["Exact", "Included"],
                    "default_choice": "Exact",
                    "description": "The type of match needed for this route to be accepted. Exact: This Route needs to be its own entry. Included: This Route is also allowed to be included in a different route. (sub-prefixes)",
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

    def _get_parsed_data(self, command: str):
        return self.bgp_device.get_genie_device_object().parse(command)

    def _search_recursive(self, data: dict, target_key: str):
        if target_key in data:
            return data[target_key]
        for value in (v for v in data.values() if isinstance(v, dict)):
            found = self._search_recursive(value, target_key)
            if found:
                return found
        return {}

    def test_device_connection(self) -> bool:
        if not self.bgp_device.can_connect():
            raise ValueError(f"Connection failed: {self.bgp_device.name}")
        return True

    @depends_on("test_device_connection")
    def test_bgp_table(self) -> bool:
        family = self.address_family.lower()
        vrf_name = getattr(self, "vrf", "default") or "default"
        context = f"{family} unicast" + (
            f" vrf {vrf_name}" if vrf_name != "default" else ""
        )

        table_output = self._get_parsed_data(f"show bgp {context}")
        prefixes_in_table = self._search_recursive(
            table_output, "prefixes"
        ) or self._search_recursive(table_output, "prefix")

        summary_output = self._get_parsed_data(f"show bgp {context} summary")
        device_local_as = str(self._search_recursive(summary_output, "local_as") or "")

        if not prefixes_in_table:
            raise ValueError(
                f"BGP Table is empty for {context} on {self.bgp_device.name}"
            )

        validated_prefixes = []

        for entry in self.entries:
            target_net = entry["network"]
            strategy = entry["match-strategy"]

            # Find matching prefix string in table
            matched_prefix_key = next(
                (
                    p
                    for p in prefixes_in_table
                    if (
                        target_net == p
                        if strategy == "Exact"
                        else ipaddress.ip_network(target_net).subnet_of(
                            ipaddress.ip_network(p if "/" in p else f"{p}/32")
                        )
                    )
                ),
                None,
            )

            if not matched_prefix_key:
                raise ValueError(
                    f"Prefix {target_net} ({strategy}) not found in Loc-RIB."
                )

            rejection_reasons = []
            has_valid_path = False

            for path_index, attributes in (
                prefixes_in_table[matched_prefix_key].get("index", {}).items()
            ):
                path_errors = []

                # Best Path Validation
                is_actually_best = any(
                    [
                        attributes.get("bestpath"),
                        attributes.get("best"),
                        ">" in str(attributes.get("status_codes", "")),
                    ]
                )
                if entry["best_option"] == "Best-Option" and not is_actually_best:
                    path_errors.append("not best-path")
                if entry["best_option"] == "Back-Up-Path" and is_actually_best:
                    path_errors.append("is best-path (expected backup)")

                # Next-Hop Validation
                actual_nh = str(
                    attributes.get("next_hop", attributes.get("gateway", ""))
                ).strip()
                if entry["is_local_origin"] == "True":
                    if actual_nh not in ["0.0.0.0", "::", "self"]:
                        path_errors.append(f"not local origin (NH: {actual_nh})")
                elif entry.get("next_hop") and actual_nh != str(entry["next_hop"]):
                    path_errors.append(
                        f"NH mismatch: expected {entry['next_hop']}, got {actual_nh}"
                    )

                # AS Path Validation
                if entry.get("expected_origin_as"):
                    raw_as_path = str(
                        attributes.get("route_info", attributes.get("as_path", ""))
                    )
                    as_numbers = [n for n in raw_as_path.split() if n.isdigit()]
                    actual_origin_as = as_numbers[-1] if as_numbers else device_local_as

                    if actual_origin_as != str(entry["expected_origin_as"]):
                        path_errors.append(
                            f"AS mismatch: expected {entry['expected_origin_as']}, got {actual_origin_as}"
                        )

                if not path_errors:
                    has_valid_path = True
                    validated_prefixes.append(matched_prefix_key)
                    break
                rejection_reasons.append(
                    f"Path #{path_index}: {', '.join(path_errors)}"
                )

            if not has_valid_path:
                raise ValueError(
                    f"Route {target_net} failed validation: {' | '.join(rejection_reasons)}"
                )

        if self.allow_other_routes == "False":
            unexpected_routes = set(prefixes_in_table.keys()) - set(validated_prefixes)
            if unexpected_routes:
                raise ValueError(
                    f"Strict Table Check Failed. Unexpected routes: {list(unexpected_routes)}"
                )

        return True
