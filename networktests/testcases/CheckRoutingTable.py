from networktests.testcases.base import DiagNetTest


class CheckRoutingTable(DiagNetTest):
    _optional_params =  [
        {
            "name": "test",
            "display_name": "Target Device",
            "type": "Device",
            "description": "The device from which to test the routes",
            "requirement": "optional",
        },
    ]

    _mutually_exclusive_parameters = [("target_device", "test")]

    _required_params = [
        {
            "name": "target_device",
            "display_name": "Target Device",
            "type": "Device",
            "description": "The device from which to test the routes"
        },
        {
            "name": "address_family",
            "display_name": "Address Family",
            "type": "choice",
            "choices": ["IPv4", "IPv6"],
            "default_choice": "IPv4",
            "description": "The address family associated with the routes"
        },
        {
            "name": "routes",
            "display_name": "Routes",
            "type": "list",
            "parameters": [
                {
                    "name": "route_origin",
                    "display_name": "Route Origin",
                    "type": "choice",
                    "choices": [
                        "CONNECTED (C)",
                        "LOCAL (L)",
                        "STATIC (S)",
                        "STATIC* (S*)",
                        "RIP (R)",
                        "OSPF (O)",
                        "OSPF IA (O IA)",
                        "OSPF E1 (O E1)",
                        "OSPF E2 (O E2)",
                        "EIGRP (D)",
                        "EIGRP EX (D EX)",
                        "BGP (B)",
                        "IS-IS (i)",
                        "IS-IS L1 (i L1)",
                        "IS-IS L2 (i L2)",
                        "IS-IS L1/L2 (i L1/L2)"
                    ],
                    "default_choice": "ANY",
                    "description": "Decides which routing protocol the route is expecting",
                },
                {
                    "name": "prefix",
                    "display_name": "Prefix - Network Destination",
                    "type": "CIDR-value(address_family)",
                    "description": "Destination network in CIDR notation",
                },
                {
                    "name": "administrative distance",
                    "display_name": "Administrative Distance",
                    "type": "Device",
                    "description": "[AD (trust level)/metric (cost to reach)]",
                    "requirement": "optional",
                },
                {
                    "name": "next_hop",
                    "display_name": "Next Hop",
                    "type": "value(address_family)",
                    "description": "Next device used to reach the network",
                    "requirement": "optional",
                },
                {
                    "name": "outgoing_interface",
                    "display_name": "Outgoing Interface",
                    "type": "Interface",
                    "description": "Interface used to reach the next hop",
                    "requirement": "optional",
                },
            ],
            "mutually_exclusive": [],
            "constraints": []
        },
    ]

    def test_fetch_routes(self):
        return True