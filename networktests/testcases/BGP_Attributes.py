import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class BGP_Attributes(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #3b82f6;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">BGP Attributes</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Loc-RIB Path Attribute & Community Verification</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>BGP_Attributes</strong> test class performs a deep-level inspection of specific BGP path attributes.
                It ensures that routing policies—such as Local Preference, MED, and Community tagging—are correctly applied to inbound and outbound advertisements.
            </p>
        </section>

        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #3b82f6; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Operational Modes
        </h4>
        <div style="display: flex; gap: 20px; margin-bottom: 20px;">
            <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #cbd5e1;">
                <strong style="color: #334155;">Traffic Engineering</strong><br>
                <span style="font-size: 0.85rem; color: #64748b;">Validate Local Preference, Weight, and MED to ensure correct inbound/outbound path selection.</span>
            </div>
            <div style="flex: 1; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <strong style="color: #334155;">Path Control</strong><br>
                <span style="font-size: 0.85rem; color: #64748b;">Verify AS-Path regex patterns and BGP Communities to enforce administrative routing boundaries.</span>
            </div>
        </div>

        <h4 style="color: #0f172a; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #3b82f6; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Pillars
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #3b82f6; margin-right: 10px;">✔</span>
                <span><strong>Targeted Path Selection:</strong> Can be configured to validate the <code>Best-Path</code>, a specific <code>Next-Hop</code>, or <code>Locally Originated</code> routes.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #3b82f6; margin-right: 10px;">✔</span>
                <span><strong>Regex Path Matching:</strong> Supports Cisco-style AS-Path regex (e.g. <code>_65001$</code>) to confirm upstream transit paths.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #3b82f6; margin-right: 10px;">✔</span>
                <span><strong>Community Compliance:</strong> Strict validation of Standard and Extended Communities with support for presence (YES) and absence (NO) checks.</span>
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
            "type": "device",
            "description": "The network device whose BGP table will be inspected for specific path attributes.",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "VRF",
            "type": "str",
            "description": "Optional: The Virtual Routing and Forwarding instance to check. If omitted, the global routing table is used.",
            "requirement": "optional",
        },
        {
            "name": "address_family",
            "display_name": "Address Family",
            "type": "choice",
            "choices": ["IPv4", "IPv6"],
            "default_choice": "IPv4",
            "description": "The protocol version to inspect (IPv4 or IPv6 unicast).",
            "requirement": "required",
        },
        {
            "name": "entries",
            "display_name": "Attribute Entries",
            "type": "list",
            "description": "A list of prefixes and the specific BGP attributes that must be validated for each.",
            "parameters": [
                {
                    "name": "network",
                    "display_name": "Network",
                    "type": [
                        {"name": "IPv4-CIDR", "condition": {"address_family": "IPv4"}},
                        {"name": "IPv6-CIDR", "condition": {"address_family": "IPv6"}},
                    ],
                    "description": "The destination prefix (CIDR notation) to look up in the BGP table.",
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
                    "name": "local_pref",
                    "display_name": "Local Preference",
                    "type": "positive-number",
                    "description": "The expected Local Preference value. Higher values are preferred within an AS.",
                    "requirement": "optional",
                },
                {
                    "name": "weight",
                    "display_name": "Weight",
                    "type": "positive-number",
                    "description": "Cisco-specific attribute. Higher weights are preferred; locally originated routes usually have 32768.",
                    "requirement": "optional",
                },
                {
                    "name": "med",
                    "display_name": "MED / Metric",
                    "type": "positive-number",
                    "description": "Multi-Exit Discriminator. Used to suggest a preferred path to external neighbors; lower is preferred.",
                    "requirement": "optional",
                },
                {
                    "name": "origin_code",
                    "display_name": "Origin Code",
                    "type": "choice",
                    "choices": ["Ignore", "IGP", "EGP", "Incomplete"],
                    "default_choice": "Ignore",
                    "description": "The BGP origin attribute. Select 'Ignore' to skip this check.",
                    "requirement": "optional",
                },
                {
                    "name": "as_path",
                    "display_name": "AS Path",
                    "type": "cisco-as-path",
                    "description": "Optional: Expected AS-Path sequence or regex.",
                    "requirement": "optional",
                },
                {
                    "name": "communities",
                    "display_name": "Associated Communities",
                    "type": "list",
                    "description": "The Communities associated with this entry",
                    "parameters": [
                        {
                            "name": "well_known_community",
                            "display_name": "Well Known Communities",
                            "description": "A selection of well known communities",
                            "type": "choice",
                            "choices": [
                                "",
                                "NO_EXPORT",
                                "NO_ADVERTISE",
                                "NO_EXPORT_SUBCONFED",
                                "NOPEER",
                                "BLACKHOLE",
                                "GRACEFUL_SHUTDOWN",
                                "ACCEPT_OWN",
                                "LLGR_STALE",
                            ],
                            "default_choice": "",
                            "requirement": "required",
                        },
                        {
                            "name": "numbered_community",
                            "display_name": "Community",
                            "description": "The numbered form of a community.",
                            "type": "cisco-community",
                            "requirement": "required",
                        },
                        {
                            "name": "community_behavior",
                            "display_name": "Should the Community be present?",
                            "description": "Marks if this Community is supposed to be present in the configuration",
                            "type": "choice",
                            "choices": ["YES", "NO"],
                            "default_choice": "YES",
                            "requirement": "required",
                        },
                    ],
                    "mutually_exclusive": [
                        ("well_known_community", "numbered_community")
                    ],
                    "constraints": [],
                    "requirement": "optional",
                },
            ],
            "mutually_exclusive": [],
            "constraints": [],
            "requirement": "required",
        },
    ]

    def _to_int(self, value):
        try:
            return int(str(value).strip()) if value is not None else None
        except (ValueError, TypeError):
            return None

    def _normalize_community(self, community):
        if not community:
            return ""

        normalized = str(community).strip().upper().replace("-", "_")
        if normalized.isdigit():
            val = int(normalized)
            return f"{(val >> 16) & 0xFFFF}:{val & 0xFFFF}"

        return normalized

    def test_device_connection(self) -> bool:
        if not self.bgp_device.can_connect():
            raise ValueError(f"Connection failed: {self.bgp_device.name}")
        return True

    @depends_on("test_device_connection")
    def test_fetch_bgp_data(self) -> bool:
        # Data Fetching
        address_family = self.address_family.lower()
        vrf_name = getattr(self, "vrf", "default") or "default"
        af_context = f"{address_family} unicast"

        command = f"show bgp {af_context}"
        if vrf_name != "default":
            command = f"{command} vrf {vrf_name}"

        raw_output = self.bgp_device.get_genie_device_object().parse(command)

        try:
            self.bgp_prefixes = raw_output["instance"]["default"]["vrf"][vrf_name][
                "address_family"
            ][af_context]["prefixes"]
        except KeyError:
            raise ValueError(
                f"BGP data for VRF {vrf_name} / AF {af_context} not found."
            )
        return True

    @depends_on("test_fetch_bgp_data")
    def test_identify_target_paths(self) -> bool:
        # Path Selection & Selection Logic
        self.cached_path_attributes = {}

        for entry in self.entries:
            network_prefix = entry["network"]
            if network_prefix not in self.bgp_prefixes:
                raise ValueError(f"Prefix {network_prefix} not found in the BGP table.")

            prefix_data = self.bgp_prefixes[network_prefix]
            best_path_index = str(prefix_data.get("best_path", ""))

            target_next_hop = entry.get("next_hop")
            is_locally_originated = entry.get("is_local_origin") == "True"

            selected_path = None
            available_paths = prefix_data.get("index", {})

            for index, attributes in available_paths.items():
                current_next_hop = str(attributes.get("next_hop", ""))

                if target_next_hop and current_next_hop == str(target_next_hop):
                    selected_path = attributes
                    break

                if is_locally_originated and current_next_hop in ["0.0.0.0", "::"]:
                    selected_path = attributes
                    break

                if (
                    not target_next_hop
                    and not is_locally_originated
                    and str(index) == best_path_index
                ):
                    selected_path = attributes
                    break

            if not selected_path:
                raise ValueError(
                    f"[{network_prefix}] Could not find a path matching the specified criteria."
                )

            self.cached_path_attributes[network_prefix] = selected_path

        return True

    @depends_on("test_identify_target_paths")
    def test_validate_metrics(self) -> bool:
        # Local Preference, Weight, MED
        for entry in self.entries:
            prefix = entry["network"]
            path_attrs = self.cached_path_attributes[prefix]

            metric_checks = [
                ("local_pref", "localpref", "Local Preference"),
                ("weight", "weight", "Weight"),
                ("med", "metric", "MED/Metric"),
            ]

            for entry_key, genie_key, display_name in metric_checks:
                expected_value = self._to_int(entry.get(entry_key))
                actual_value = self._to_int(path_attrs.get(genie_key))

                if expected_value is not None and actual_value != expected_value:
                    raise ValueError(
                        f"[{prefix}] {display_name} mismatch: Expected {expected_value}, got {actual_value}"
                    )

        return True

    @depends_on("test_identify_target_paths")
    def test_validate_origin(self) -> bool:
        # Origin Code Verification
        origin_mapping = {"IGP": "i", "EGP": "e", "Incomplete": "?"}

        for entry in self.entries:
            expected_origin = entry.get("origin_code", "Ignore")
            if expected_origin == "Ignore":
                continue

            prefix = entry["network"]
            path_attrs = self.cached_path_attributes[prefix]
            actual_origin = path_attrs.get("origin_codes")

            if origin_mapping[expected_origin] != actual_origin:
                raise ValueError(
                    f"[{prefix}] Origin mismatch: Expected {expected_origin} ({origin_mapping[expected_origin]}), got {actual_origin}"
                )

        return True

    @depends_on("test_identify_target_paths")
    def test_validate_as_path(self) -> bool:
        # AS-Path Regex Matching
        for entry in self.entries:
            as_path_pattern = entry.get("as_path")
            if not as_path_pattern:
                continue

            prefix = entry["network"]
            path_attrs = self.cached_path_attributes[prefix]

            actual_as_path = str(
                path_attrs.get("as_path") or path_attrs.get("route_info") or ""
            ).strip()

            # Convert Cisco underscore to Python word boundaries
            python_compatible_regex = as_path_pattern.replace(
                "_", r"(?:^|[,{} \t]|$|$)"
            )

            if not re.search(python_compatible_regex, actual_as_path):
                raise ValueError(
                    f"[{prefix}] AS-Path mismatch: Found '{actual_as_path}'"
                )

        return True

    @depends_on("test_identify_target_paths")
    def test_validate_communities(self) -> bool:
        # BGP Community Verification
        for entry in self.entries:
            prefix = entry["network"]
            path_attrs = self.cached_path_attributes[prefix]
            expected_communities = entry.get("communities", [])

            if not expected_communities:
                continue

            # communities found on the device
            search_string = f"{path_attrs.get('route_info', '')} {path_attrs.get('community', '')} {path_attrs.get('extended_community', '')}"
            active_communities = {
                self._normalize_community(tag) for tag in search_string.split() if tag
            }

            comm_data_block = path_attrs.get("community")
            if isinstance(comm_data_block, dict):
                active_communities.update(
                    self._normalize_community(key) for key in comm_data_block.keys()
                )

            for comm_entry in expected_communities:
                target_tag = self._normalize_community(
                    comm_entry.get("well_known_community")
                    or comm_entry.get("numbered_community")
                )

                if not target_tag:
                    continue

                is_present = target_tag in active_communities
                should_be_present = comm_entry.get("community_behavior", "YES") == "YES"

                if should_be_present and not is_present:
                    raise ValueError(
                        f"[{prefix}] Missing required community: {target_tag}"
                    )

                if not should_be_present and is_present:
                    raise ValueError(
                        f"[{prefix}] Forbidden community detected: {target_tag}"
                    )

        return True
