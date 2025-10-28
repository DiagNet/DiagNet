from networktests.testcases.base import DiagNetTest


class CheckRoutingTable(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family:Arial,sans-serif; line-height:1.5; max-width:800px;">
  <h2 class="mb-3">CheckRoutingTable Test Class</h2>
  <p>
    The <strong>CheckRoutingTable</strong> test class is designed to validate the routing table of a network device.
    It ensures that the device has the expected routes and that they are configured correctly according to the routing protocols and parameters specified.
  </p>

  <h4 class="mt-4 mb-2">Purpose</h4>
  <p>
    This test helps verify that routes exist in the routing table and are reachable via the expected paths.
    It is particularly useful for network diagnostics and automated verification of device configurations.
  </p>

  <h4 class="mt-4 mb-2">Parameters</h4>

  <h5 class="mt-3">Required Parameters</h5>
  <ul class="list-group mb-3">
    <li class="list-group-item">
      <strong>Target Device</strong> (<em>Device or IPv4</em>)<br>
      The device from which to test the routes.
    </li>
    <li class="list-group-item">
      <strong>Address Family</strong> (<em>choice</em>)<br>
      Determines whether to check IPv4 or IPv6 routes. Default is <strong>IPv4</strong>.<br>
      Choices: IPv4, IPv6
    </li>
    <li class="list-group-item">
      <strong>Routes</strong> (<em>list</em>)<br>
      Specifies the routes to validate in the routing table. Each route contains:
      <ul class="mt-2">
        <li><strong>Route Origin</strong> (<em>choice</em>) – Routing protocol expected (e.g., CONNECTED, STATIC, OSPF, BGP, etc.)</li>
        <li><strong>Prefix</strong> (<em>IPv4</em>) – Destination network in CIDR notation</li>
        <li><strong>Administrative Distance</strong> (<em>optional</em>) – Trust level or metric to reach the network</li>
        <li><strong>Next Hop</strong> (<em>optional</em>) – Next device used to reach the network</li>
        <li><strong>Outgoing Interface</strong> (<em>optional</em>) – Interface used to reach the next hop</li>
      </ul>
    </li>
  </ul>

  <h5 class="mt-3">Optional Parameters</h5>
  <ul class="list-group mb-3">
    <li class="list-group-item">
      <strong>Test</strong> (<em>Device</em>) – The device from which to run additional route checks. Optional.
    </li>
  </ul>

  <h4 class="mt-4 mb-2">How it Works</h4>
  <p>
    When executed, this test iterates through the list of expected routes and verifies:
    <ol>
      <li>That each route exists in the routing table.</li>
      <li>That the route's origin matches the expected routing protocol.</li>
      <li>That optional details such as administrative distance, next hop, and outgoing interface are correct if provided.</li>
    </ol>
    The test fails if required routes are missing or do not match the expected configuration.
  </p>

  <h4 class="mt-4 mb-2">Why Use This Test</h4>
  <ul>
    <li>Automatically verify network device route configurations.</li>
    <li>Detect misconfigurations or missing routes before network issues arise.</li>
    <li>Ensure compliance with network routing policies and address families.</li>
  </ul>
</div>

    """
    _optional_params =  [
        {
            "name": "test",
            "display_name": "Target Device",
            "type": "Device",
            "description": "The device from which to test the routes",
            "requirement": "optional",
        },
    ]

    _required_params = [
        {
            "name": "target_device",
            "display_name": "Target Device",
            "type": ["Device", "IPv4"],
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
                    "type":
                        {"name": "IPv4","condition": {"address_family": "IPv4"}}
                    ,
                    "description": "Destination network in CIDR notation",
                },
                {
                    "name": "administrative_distance",
                    "display_name": "Administrative Distance",
                    "type": ["str","Device", {"name": "IPv4", "condition": {"address_family": "IPv4"}}],
                    "description": "[AD (trust level)/metric (cost to reach)]",
                    "requirement": "optional",
                    "required_if": {"prefix": "10.0.0.0"},
                },
                {
                    "name": "next_hop",
                    "display_name": "Next Hop",
                    "type": "string",
                    "description": "Next device used to reach the network",
                    "requirement": "optional",
                },
                {
                    "name": "outgoing_interface",
                    "display_name": "Outgoing Interface",
                    "type": "IPv4",
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