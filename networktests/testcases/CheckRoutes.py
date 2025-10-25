from networktests.testcases.base import DiagNetTest


class CheckRoutes(DiagNetTest):
    _optional_params = [
        {
            "name": "optional_ip",
            "type": "IPv4"
        },
    ]

    _mutually_exclusive_parameters = [
        ("target", "target_ip")
    ]
    _required_params = [
        {
            "name": "type",
            "type": "choice",
            "choices": ["IPv4", "IPv6"],
            "empty_choice": "true",
            "description": "Selects if IPv4 or IPv6 Routes are checked"
        },
        {
            "name": "target",
            "type": "device"
        },
        {
            "name": "target_ip",
            "type": "IPv4"
        },
        {
            "name": "routes",
            "type": "list",
            "description": "The routes to check",
            "required": [
                {
                    "name": "destination_prefix",
                    "type": "CIDR-value(type)",
                    "forbidden_if": {"type": "IPv4"},
                    "description": "The destination network in CIDR notation"
                },
                {
                    "name": "route_source",
                    "type": "choice",
                    "choices": [
                        "ANY","CONNECTED (C)"
                    ],
                    "default_choice": "ANY",
                    "description": "The origin or protocol through which a route was learned"
                },
                {
                        "name": "routes2",
                        "type": "list",
                        "description": "The routes to check",
                        "required": [
                            {
                                "name": "destination_prefix2",
                                "type": "CIDR-value(type)",
                                "forbidden_if": {"type": "IPv4"},
                                "description": "The destination network in CIDR notation"
                            },
                            {
                                "name": "route_source2",
                                "type": "choice",
                                "choices": [
                                    "ANY","CONNECTED (C)"
                                ],
                                "default_choice": "ANY",
                                "description": "The origin or protocol through which a route was learned"
                            },
                            {
                                "name": "routes3",
                                "type": "list",
                                "description": "The routes to check",
                                "required": [
                                    {
                                        "name": "destination_prefix3",
                                        "type": "CIDR-value(type)",
                                        "required_if": {"type": "IPv4"},
                                        "description": "The destination network in CIDR notation"
                                    },
                                    {
                                        "name": "route_source3",
                                        "type": "choice",
                                        "choices": [
                                            "ANY","CONNECTED (C)"
                                        ],
                                        "empty_choice": "true",
                                        "default_choice": "ANY",
                                        "description": "The origin or protocol through which a route was learned"
                                    }
                                ],
                                "optional": [
                                    {
                                        "name": "test_param",
                                        "type": "ipv4",
                                    },
                                ],
                                "mutually_exclusive": [],
                                "constraints": ["min_length=3", "unique=true"]
                            }
                        ],
                        "optional": [],
                        "mutually_exclusive": [],
                        "constraints": ["max_length=1", "unique=true"]
                }
            ],
            "optional": [],
            "mutually_exclusive": [],
            "constraints": ["min_length=1", "unique=true"]
        }
    ]

    _required_params4 = [
        "type:choices[IPv4,IPv6]{description=Selects if IPv4 or IPv6 Routes are checked}",
        "target:device",
        [ # List
            """routes:list{description=The routes to check}""",
            [ # Required Parameters
                """destination_prefix:CIDR-value(type){description="The destination network in CIDR notation"}""",
                [ # Choice
                    "route_source:choices{description='The origin or protocol through which a route was learned'}",
                    [
                        "ANY",
                        "CONNECTED (C)",
                        "LOCAL (L)",
                        "STATIC (S)",
                        "STATIC* (S*)",
                        "RIP (R)",
                        "OSPF",
                        "OSPF IA",
                        "OSPF E1",
                        "OSPF E2",
                        "OSPF N1",
                        "OSPF N2",
                        "EIGRP (D)",
                        "EIGRP EX (D EX)",
                        "BGP (B)",
                        "BGP IGP (B)",
                        "BGP EGP (B)",
                        "IS-IS (i)",
                        "IS-IS L1 (i L1)",
                        "IS-IS L2 (i L2)",
                        "IS-IS L1/L2 (i L1/L2)",
                        "IS-IS * (i *)"
                    ],
                    "ANY" # Default Selection
                ]
            ],
            [ # Optional Parameters
                "local_preference:number[min=0, max=1000000]{description='Local Preference of the BGP Route', required_if={route_source=r'BGP.*'}}",
                "message_for_non_ospf:str{forbidden_if={route_source=r'OSPF.*'}}"
            ],
            [ # Mutually Exclusive Bindings

            ],
            [ # Constraints
                "min_length=1",
                "unique=true"
            ]
        ]
    ]
    _required_params2 = [
        """
        type:choices["IPv4","IPv6"]{description="Selects if IPv4 or IPv6 Routes are checked"},
        target:device,
        routes:list[
            required={
                destination_prefix:CIDR-value(type){description="The destination network in CIDR notation"} ,
                route_source:choices[
                        *ANY*, 
                        CONNECTED (C), 
                        LOCAL (L), 
                        STATIC (S), 
                        STATIC* (S*), 
                        RIP (R), 
                        OSPF, 
                        OSPF IA, 
                        OSPF E1, 
                        OSPF E2, 
                        OSPF N1, 
                        OSPF N2, 
                        EIGRP (D), 
                        EIGRP EX (D EX), 
                        BGP (B), 
                        BGP IGP (B), 
                        BGP EGP (B), 
                        IS-IS (i),
                        IS-IS L1 (i L1),
                        IS-IS L2 (i L2),
                        IS-IS L1/L2 (i L1/L2),
                        IS-IS * (i *)
                ]{description="The origin or protocol through which a route was learned"}, 
            }
            optional={
                local_preference:number[min=0, max=1000000]{description="Local Preference of the BGP Route", required_if={route_source=r"BGP.*"}}
                message_for_non_ospf:str{forbidden_if={route_source=r"OSPF.*"}}
            }
            mutually_exclusive={}
            constraints={
                min_length=1,
                unique=true
            }
        ]{description="The routes to check"}
        """
    ]

    def test_reachability(self) -> bool:
        return True

if __name__ == "__main__":
    d = CheckRoutes()
    print(d.get_parameters())