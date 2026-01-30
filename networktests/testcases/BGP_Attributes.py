import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class BGP_Attributes(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-diagram-3-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">BGP Attribute Validation</h3>
                    <div class="mt-1">
                        <span class="badge bg-info text-dark bg-opacity-75 border border-info border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">BGP / Routing</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test performs a deep inspection of the BGP routing table. It verifies that specific
                        prefixes exist and strictly match defined <strong>Path Attributes</strong>.
                        It ensures Traffic Engineering policies (Local-Pref, MED, Communities) are correctly applied
                        and detects potential unexpected routing behaviors.
                    </p>

                    <div class="p-3 rounded border border-info border-opacity-25 bg-info bg-opacity-10">
                        <h6 class="fw-bold text-primary-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures network stability by strictly validating Traffic Engineering, AS-Path policies, and community tagging.
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
                                <td class="text-body-secondary">The target network device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF instance (default: global)</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">address_family <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">IPv4 or IPv6</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">entries <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">List of routes to validate</td>
                            </tr>

                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ network <span class="text-danger">*</span></td>
                                <td class="text-body-secondary fst-italic">Target Prefix</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ local_pref</td>
                                <td class="text-body-secondary fst-italic">Expected Local Preference</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ med</td>
                                <td class="text-body-secondary fst-italic">Expected MED</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ as_path</td>
                                <td class="text-body-secondary fst-italic">Regex for AS-Path sequence</td>
                            </tr>
                            <tr>
                                <td class="ps-4 font-monospace text-body-tertiary">↳ communities</td>
                                <td class="text-body-secondary fst-italic">Required BGP Communities</td>
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
