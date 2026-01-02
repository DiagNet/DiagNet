import ipaddress
import re

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

    def _search_recursive(self, data: dict, target_key: str):
        if target_key in data:
            return data[target_key]
        for value in (v for v in data.values() if isinstance(v, dict)):
            found = self._search_recursive(value, target_key)
            if found:
                return found
        return {}

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

        # Cache
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
            strategy = entry["match-strategy"]
            target_obj = ipaddress.ip_network(target_net)

            # Finding a match based on strategy
            matched_key = None
            for p_str in self.table_prefixes:
                if strategy == "Exact":
                    if p_str == target_net:
                        matched_key = p_str
                        break
                else:
                    p_obj = ipaddress.ip_network(
                        p_str if "/" in p_str else f"{p_str}/32"
                    )
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
                    if actual_nh not in ["0.0.0.0", "::", "self"]:
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
                    if actual_as != self._to_int_str(entry["expected_origin_as"]):
                        current_errors.append(
                            f"AS mismatch: Exp {entry['expected_origin_as']}, Got {actual_as}"
                        )

                if not current_errors:
                    has_valid_path = True
                    self.validated_keys.append(matched_key)
                    break
                path_errors.append(f"Path #{idx}: {', '.join(current_errors)}")

            if not has_valid_path:
                raise ValueError(
                    f"Route {target_net} failed: {' | '.join(path_errors)}"
                )

        return True

    @depends_on("test_validate_prefixes")
    def test_strict_table_enforcement(self) -> bool:
        if str(self.allow_other_routes) == "True":
            return True

        all_table_keys = set(self.table_prefixes.keys())
        unexpected = all_table_keys - set(self.validated_keys)

        if unexpected:
            raise ValueError(
                f"Strict Check Failed. Unexpected routes: {sorted(list(unexpected))}"
            )

        return True
