from networktests.testcases.base import DiagNetTest


class CheckRoutes(DiagNetTest):
    _required_params = [
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