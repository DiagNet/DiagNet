import ipaddress
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class BGP_RoutingTable(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #3b82f6;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">BGP Routing Table</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Loc-RIB Integrity & Policy Compliance</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>BGP_RoutingTable</strong> test class performs a deep-dive inspection of the BGP Local RIB.
                It validates that specific prefixes are not only present but are optimally selected and originated from the correct Autonomous Systems.
            </p>
        </section>

        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #3b82f6; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Core Match Strategies
        </h4>
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #cbd5e1;">
                <strong style="color: #334155;">Exact Match</strong><br>
                <span style="font-size: 0.85rem; color: #64748b;">The prefix must match the specific entry in the BGP table exactly, including the mask length.</span>
            </div>
            <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <strong style="color: #334155;">Included Match</strong><br>
                <span style="font-size: 0.85rem; color: #64748b;">Validates if the target subnet is a subset covered by a larger aggregate or summary route.</span>
            </div>
        </div>

        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #3b82f6; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Pillars
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #3b82f6; margin-right: 10px;">✔</span>
                <span><strong>Best Path Status:</strong> Verifies if the route is selected (<code>></code>) or held as a Backup path.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #3b82f6; margin-right: 10px;">✔</span>
                <span><strong>Origin AS:</strong> Traces the AS-Path to confirm the route originated from the expected ASN.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #3b82f6; margin-right: 10px;">✔</span>
                <span><strong>Strict Enforcement:</strong> Optionally fails if any undefined routes are found, preventing unauthorized route leaks.</span>
            </li>
        </ul>

        <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 25px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 15px;">
            Authored by: Luka Pacar
        </p>
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
