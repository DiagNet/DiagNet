import re

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class BGP_Attributes(DiagNetTest):
    """
        <div class="p-4 bg-white rounded shadow-sm" style="font-family:Arial,sans-serif; line-height:1.5; max-width:800px; border: 1px solid #dee2e6;">
      <h2 class="mb-3" style="color: #2c3e50;">BGP_Attributes Test Class</h2>
      <p>
        The <strong>BGP_Attributes</strong> test class performs deep inspection of the BGP Loc-RIB (Local Routing Information Base).
        It validates specific path attributes for targeted prefixes to ensure routing policy compliance and path consistency.
      </p>

      <h4 class="mt-4 mb-2" style="color: #2980b9;">Purpose</h4>
      <p>
        This test verifies that BGP updates are processed and tagged correctly. It allows engineers to validate <strong>Traffic Engineering</strong> (Local Preference, MED) and <strong>Path Control</strong> (AS-Path, Communities) across global or VRF-specific routing tables.
      </p>

      <h4 class="mt-4 mb-2" style="color: #2980b9;">Parameters</h4>

      <h5 class="mt-3">Required Global Parameters</h5>
      <ul class="list-group mb-3">
        <li class="list-group-item">
          <strong>BGP Device</strong> (<em>Device</em>)<br>
          The network element to query for BGP table data.
        </li>
        <li class="list-group-item">
          <strong>Address Family</strong> (<em>choice</em>)<br>
          Determines whether to check <strong>IPv4</strong> or <strong>IPv6</strong> unicast prefixes.
        </li>
        <li class="list-group-item">
          <strong>VRF</strong> (<em>optional string</em>)<br>
          The specific Virtual Routing and Forwarding instance to inspect. If omitted, the global table is used.
        </li>
      </ul>

      <h5 class="mt-3">Attribute Entry Parameters (Per Prefix)</h5>
      <p>For each network prefix, you can define specific path selection criteria and expected values:</p>
      <ul class="list-group mb-3">
        <li class="list-group-item"><strong>Network</strong> (<em>CIDR</em>) – The destination prefix to look up.</li>
        <li class="list-group-item"><strong>Path Selection</strong> – Define if the test should check the <strong>Best Path</strong>, a specific <strong>Next-Hop</strong>, or a <strong>Locally Originated</strong> route.</li>
        <li class="list-group-item"><strong>Metrics</strong> (<em>optional</em>) – Validation for Local Preference, Weight, and MED (Metric).</li>
        <li class="list-group-item"><strong>Origin Code</strong> (<em>choice</em>) – Matches the BGP origin attribute (IGP, EGP, or Incomplete).</li>
        <li class="list-group-item"><strong>AS Path</strong> (<em>regex</em>) – Supports Cisco-style regex (e.g., <code>_65001_</code>) to match specific AS sequences.</li>
        <li class="list-group-item"><strong>Communities</strong> (<em>list</em>) – A list of tags to check. Use <strong>YES</strong> to ensure a tag exists or <strong>NO</strong> to ensure it is absent (forbidden).</li>
      </ul>

      <h4 class="mt-4 mb-2" style="color: #2980b9;">How it Works</h4>
      <p>
        The test follows a high-performance modular execution flow:
      </p>
      <ol>
        <li><strong>Data Retrieval</strong>: Polls the device once using the Genie parser to fetch the BGP table.</li>
        <li><strong>Path Targeting</strong>: Identifies the correct path index based on Next-Hop or Best-Path requirements.</li>
        <li><strong>Modular Validation</strong>: Executes independent checks for metrics, origin, AS-Path, and communities.</li>
      </ol>
      <p>
        Failures are reported with granular detail, specifying the exact attribute and prefix causing the mismatch.
      </p>

      <h4 class="mt-4 mb-2" style="color: #2980b9;">Why Use This Test</h4>
      <ul>
        <li><strong>Verify Policy Compliance</strong>: Ensure tags like <code>NO_EXPORT</code> are correctly applied to routes.</li>
        <li><strong>Validate ISP Redundancy</strong>: Confirm AS-Path prepending is active on specific neighbor paths.</li>
        <li><strong>Targeted Audits</strong>: Filter out "system" or "noisy" communities and only validate the ones you specifically configured.</li>
      </ul>
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

    def _to_int(self, val):
        try:
            return int(str(val).strip()) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _normalize_comm(self, comm):
        if not comm:
            return ""
        c = str(comm).strip().upper().replace("-", "_")
        if c.isdigit():
            v = int(c)
            return f"{(v >> 16) & 0xFFFF}:{v & 0xFFFF}"
        return c

    def test_device_connection(self) -> bool:
        if not self.bgp_device.can_connect():
            raise ValueError(f"Connection failed: {self.bgp_device.name}")
        return True

    @depends_on("test_device_connection")
    def test_fetch_bgp_data(self) -> bool:
        family, vrf = (
            self.address_family.lower(),
            getattr(self, "vrf", "default") or "default",
        )
        context = f"{family} unicast"
        cmd = f"show bgp {context}{f' vrf {vrf}' if vrf != 'default' else ''}"

        raw_data = self.bgp_device.get_genie_device_object().parse(cmd)
        try:
            self.prefixes = raw_data["instance"]["default"]["vrf"][vrf][
                "address_family"
            ][context]["prefixes"]
        except KeyError:
            raise ValueError(f"BGP data for {vrf}/{context} not found.")
        return True

    def _get_path_attr(self, entry):
        net = entry["network"]
        if net not in self.prefixes:
            raise ValueError(f"Prefix {net} not in BGP table.")

        pref_data = self.prefixes[net]
        best_idx = str(pref_data.get("best_path", ""))
        target_nh, is_local = (
            entry.get("next_hop"),
            entry.get("is_local_origin") == "True",
        )

        for idx, attr in pref_data.get("index", {}).items():
            cur_nh = str(attr.get("next_hop", ""))
            if target_nh and cur_nh == str(target_nh):
                return attr
            if is_local and cur_nh in ["0.0.0.0", "::"]:
                return attr
            if not target_nh and not is_local and str(idx) == best_idx:
                return attr
        return None

    @depends_on("test_fetch_bgp_data")
    def test_numeric_attributes(self) -> bool:
        for entry in self.entries:
            attr = self._get_path_attr(entry)
            if not attr:
                raise ValueError(f"[{entry['network']}] Path selection failed.")

            checks = [
                ("local_pref", "localpref"),
                ("weight", "weight"),
                ("med", "metric"),
            ]
            for param, key in checks:
                exp, act = self._to_int(entry.get(param)), self._to_int(attr.get(key))
                if exp is not None and act != exp:
                    raise ValueError(
                        f"[{entry['network']}] {param} mismatch: Exp {exp}, Got {act}"
                    )
        return True

    @depends_on("test_fetch_bgp_data")
    def test_origin_code(self) -> bool:
        origin_map = {"IGP": "i", "EGP": "e", "Incomplete": "?"}
        for entry in self.entries:
            exp_label = entry.get("origin_code", "Ignore")
            if exp_label == "Ignore":
                continue

            attr = self._get_path_attr(entry)
            if attr and origin_map[exp_label] != attr.get("origin_codes"):
                raise ValueError(
                    f"[{entry['network']}] Origin mismatch: Expected {exp_label}"
                )
        return True

    @depends_on("test_fetch_bgp_data")
    def test_as_path(self) -> bool:
        for entry in self.entries:
            pattern = entry.get("as_path")
            if pattern is None:
                continue

            attr = self._get_path_attr(entry)
            if not attr:
                continue

            actual = str(attr.get("as_path") or attr.get("route_info") or "").strip()
            # Map Cisco '_' to BGP-compatible regex
            py_regex = pattern.replace("_", r"(?:^|[,{} \t]|$|$)")
            if not re.search(py_regex, actual):
                raise ValueError(
                    f"[{entry['network']}] AS-Path mismatch: Found '{actual}'"
                )
        return True

    @depends_on("test_fetch_bgp_data")
    def test_communities(self) -> bool:
        for entry in self.entries:
            attr = self._get_path_attr(entry)
            if not attr:
                continue

            raw_user_comms = entry.get("communities", [])
            user_comms = raw_user_comms
            if not user_comms:
                continue

            raw_src = f"{attr.get('route_info', '')} {attr.get('community', '')} {attr.get('extended_community', '')}"
            actual_set = {self._normalize_comm(t) for t in raw_src.split() if t}

            comm_dict = attr.get("community")
            if isinstance(comm_dict, dict):
                actual_set.update(self._normalize_comm(k) for k in comm_dict.keys())

            for c_obj in user_comms:
                target = self._normalize_comm(
                    c_obj["well_known_community"] or c_obj["numbered_community"]
                )
                if not target:
                    continue

                is_present = target in actual_set
                behavior = c_obj.get("community_behavior", "YES")

                if behavior == "YES" and not is_present:
                    raise ValueError(
                        f"[{entry['network']}] Missing required community: {target}"
                    )
                if behavior == "NO" and is_present:
                    raise ValueError(
                        f"[{entry['network']}] Forbidden community found: {target}"
                    )
        return True
