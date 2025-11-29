from networktests.testcases.base import DiagNetTest


class CheckRoutes(DiagNetTest):
    _mutually_exclusive_parameters = [("target", "target_ip")]

    _params = [
        {
            "name": "optional_ip",
            "display_name": "Optional IP",
            "type": "IPv4",
            "description": "An optional IPv4 address",
            "requirement": "optional",
        },
        {
            "name": "type",
            "display_name": "Address-Family",
            "type": "choice",
            "choices": ["IPv4", "IPv6"],
            "empty_choice": "true",
            "description": "Selects if IPv4 or IPv6 Routes are checked",
        },
        {"name": "target", "display_name": "Target Device", "type": "device"},
        {"name": "target_ip", "display_name": "Target IP", "type": "IPv4"},
        {
            "name": "routes",
            "display_name": "Routes",
            "type": "list",
            "description": "The routes to check",
            "parameters": [
                {
                    "name": "destination_prefix",
                    "display_name": "Destination Prefix",
                    "type": "IPv4",
                    "forbidden_if": {"type": "IPv4"},
                    "description": "The destination network in CIDR notation",
                },
                {
                    "name": "route_source",
                    "display_name": "Route Source",
                    "type": "choice",
                    "choices": ["ANY", "CONNECTED (C)"],
                    "default_choice": "ANY",
                    "description": "The origin or protocol through which a route was learned",
                },
                {
                    "name": "routes2",
                    "display_name": "Nested Routes",
                    "type": "list",
                    "description": "The routes to check",
                    "parameters": [
                        {
                            "name": "destination_prefix2",
                            "display_name": "Destination Prefix",
                            "type": "IPv4",
                            "forbidden_if": {"type": "IPv4"},
                            "description": "The destination network in CIDR notation",
                        },
                        {
                            "name": "route_source2",
                            "display_name": "Route Source",
                            "type": "choice",
                            "choices": ["ANY", "CONNECTED (C)"],
                            "default_choice": "ANY",
                            "description": "The origin or protocol through which a route was learned",
                        },
                        {
                            "name": "routes3",
                            "display_name": "Deep Nested Routes",
                            "type": "list",
                            "description": "The routes to check",
                            "parameters": [
                                {
                                    "name": "destination_prefix3",
                                    "display_name": "Destination Prefix",
                                    "type": "IPv4",
                                    "required_if": {"type": "IPv4"},
                                    "description": "The destination network in CIDR notation",
                                },
                                {
                                    "name": "route_source3",
                                    "display_name": "Route Source",
                                    "type": "choice",
                                    "choices": ["ANY", "CONNECTED (C)"],
                                    "empty_choice": "true",
                                    "default_choice": "ANY",
                                    "description": "The origin or protocol through which a route was learned",
                                },
                                {
                                    "name": "test_param",
                                    "display_name": "Test Parameter",
                                    "type": "IPv4",
                                    "requirement": "optional",
                                },
                            ],
                            "mutually_exclusive": [],
                            "constraints": ["min_length=3", "unique=true"],
                        },
                    ],
                    "mutually_exclusive": [],
                    "constraints": ["max_length=1", "unique=true"],
                },
            ],
            "mutually_exclusive": [],
            "constraints": ["min_length=1", "unique=true"],
        },
    ]

    def test_reachability(self) -> bool:
        return True
