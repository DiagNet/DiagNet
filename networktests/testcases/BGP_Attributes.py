from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class BGP_Attributes(DiagNetTest):
    """
    TODO
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
                    "choices": ["IGP", "EGP", "Incomplete"],
                    "description": "The BGP origin attribute: IGP (i), EGP (e), or Incomplete (?).",
                    "requirement": "optional",
                },
            ],
            "requirement": "optional",
        },
    ]

    def _get_parsed(self, command: str):
        return self.bgp_device.get_genie_device_object().parse(command)

    def _find_key(self, data: dict, key: str):
        if key in data:
            return data[key]
        for v in (v for v in data.values() if isinstance(v, dict)):
            found = self._find_key(v, key)
            if found:
                return found
        return {}

    def test_device_connection(self) -> bool:
        if not self.bgp_device.can_connect():
            raise ValueError(f"Connection failed: {self.bgp_device.name}")
        return True

    @depends_on("test_device_connection")
    def test_bgp_attributes(self) -> bool:
        family = self.address_family.lower()
        vrf_name = getattr(self, "vrf", "default") or "default"
        context = f"{family} unicast" + (
            f" vrf {vrf_name}" if vrf_name != "default" else ""
        )

        raw_data = self._get_parsed(f"show bgp {context}")
        prefixes = self._find_key(raw_data, "prefixes") or self._find_key(
            raw_data, "prefix"
        )

        if not prefixes:
            raise ValueError(f"BGP Table empty on {self.bgp_device.name}")

        origin_map = {"IGP": "i", "EGP": "e", "Incomplete": "?"}

        for entry in self.entries:
            target_net = entry["network"]
            if target_net not in prefixes:
                raise ValueError(f"Prefix {target_net} not found in Loc-RIB.")

            path_results, success = [], False

            for idx, path_attr in prefixes[target_net].get("index", {}).items():
                errs = []

                # 1. Numeric Attributes validation
                for param, rib_key in [
                    ("local_pref", "localpref"),
                    ("weight", "weight"),
                    ("med", "metric"),
                ]:
                    expected = entry.get(param)
                    if expected is not None and str(expected).strip() != "":
                        actual = path_attr.get(rib_key)
                        if str(actual) != str(expected):
                            errs.append(
                                f"{param} mismatch: expected {expected}, got {actual}"
                            )

                # 2. Origin Check validation
                expected_origin = entry.get("origin_code")
                if expected_origin and str(expected_origin).strip() != "":
                    expected_code = origin_map[expected_origin]
                    actual_code = str(path_attr.get("origin_codes", ""))
                    if expected_code not in actual_code:
                        errs.append(
                            f"Origin mismatch: expected {expected_code}, got {actual_code}"
                        )

                if not errs:
                    success = True
                    break
                path_results.append(f"Path #{idx}: {', '.join(errs)}")

            if not success:
                raise ValueError(
                    f"Validation failed for {target_net}: {' | '.join(path_results)}"
                )

        return True
