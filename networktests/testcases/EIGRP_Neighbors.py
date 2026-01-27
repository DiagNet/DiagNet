import ipaddress
from typing import Dict, List, Tuple

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class EIGRP_Neighbors(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #14532d;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">EIGRP Adjacency</h2>
            <p style="color: #dcfce7; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Neighbor State Verification</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>EIGRP_Neighbors</strong> test validates the formation of EIGRP adjacencies between two devices.
                It confirms that the peer's IP address is present in the local neighbor table, ensuring bidirectional control-plane connectivity.
            </p>
        </section>

        <h4 style="color: #14532d; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #16a34a; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Verification Scope
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #15803d; margin-right: 10px;">✔</span>
                <span><strong>Auto-Discovery:</strong> Detects the shared link and IP addresses of both peers.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #15803d; margin-right: 10px;">✔</span>
                <span><strong>Table Integrity:</strong> Verifies that the specific peer is listed as an active neighbor in the correct VRF.</span>
            </li>
        </ul>
    </div>
    """

    _params = [
        {
            "name": "device_a",
            "display_name": "Device A",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "device_b",
            "display_name": "Device B",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "VRF",
            "type": "str",
            "default": "default",
            "requirement": "optional",
        },
        {
            "name": "as_number",
            "display_name": "AS Number",
            "type": "positive-number",
            "description": "Optional: If set, checks only this AS. If omitted, checks all active EIGRP instances.",
            "requirement": "optional",
        },
        {
            "name": "expected_state",
            "display_name": "Expected State",
            "type": "choice",
            "choices": ["Established", "None"],
            "default_choice": "Established",
            "description": "Established: Peers must see each other. None: Peers must NOT see each other.",
            "requirement": "required",
        },
    ]

    def _find_overlap_and_ips(
        self, data_a: Dict, data_b: Dict
    ) -> Tuple[str, str, str, str]:
        device_a_networks = {}

        for intf_name, details in data_a.items():
            ipv4_config = details.get("ipv4", {})
            for ip_mask, _ in ipv4_config.items():
                if "/" not in ip_mask:
                    continue
                try:
                    interface_obj = ipaddress.ip_interface(ip_mask)
                    device_a_networks[interface_obj.network] = (
                        intf_name,
                        str(interface_obj.ip),
                    )
                except ValueError:
                    continue

        for intf_name, details in data_b.items():
            ipv4_config = details.get("ipv4", {})
            for ip_mask, _ in ipv4_config.items():
                if "/" not in ip_mask:
                    continue
                try:
                    interface_obj = ipaddress.ip_interface(ip_mask)
                    target_network = interface_obj.network

                    if target_network in device_a_networks:
                        int_a, ip_a = device_a_networks[target_network]
                        int_b, ip_b = intf_name, str(interface_obj.ip)
                        return int_a, ip_a, int_b, ip_b
                except ValueError:
                    continue

        return "", "", "", ""

    def _get_active_neighbors(self, eigrp_data: Dict, vrf_name: str) -> List[str]:
        active_neighbors = []
        instances = eigrp_data.get("eigrp_instance", {})
        target_as = getattr(self, "as_number", None)

        for as_num, as_data in instances.items():
            if target_as and str(target_as) != str(as_num):
                continue

            vrf_data = as_data.get("vrf", {}).get(vrf_name, {})
            af_data = vrf_data.get("address_family", {}).get("ipv4", {})
            eigrp_interfaces = af_data.get("eigrp_interface", {})

            for interface_data in eigrp_interfaces.values():
                neighbors = interface_data.get("eigrp_nbr", {})
                active_neighbors.extend(neighbors.keys())

        return active_neighbors

    def test_device_connection(self) -> bool:
        for device in [self.device_a, self.device_b]:
            if not device.can_connect():
                raise ValueError(f"Connection failed: {device.name}")
        return True

    @depends_on("test_device_connection")
    def test_discover_topology(self) -> bool:
        vrf_name = getattr(self, "vrf", "default") or "default"
        command = (
            f"show ip interface vrf {vrf_name}"
            if vrf_name != "default"
            else "show ip interface"
        )

        try:
            device_a_data = self.device_a.get_genie_device_object().parse(command)
            device_b_data = self.device_b.get_genie_device_object().parse(command)
        except Exception as error:
            raise ValueError(f"Topology discovery failed: {error}")

        self.int_a, self.ip_a, self.int_b, self.ip_b = self._find_overlap_and_ips(
            device_a_data, device_b_data
        )

        if not self.ip_a or not self.ip_b:
            raise ValueError(
                "Topology Mismatch: No shared subnet found between the devices."
            )

        return True

    @depends_on("test_discover_topology")
    def test_verify_adjacency(self) -> bool:
        vrf_name = getattr(self, "vrf", "default") or "default"
        command = (
            f"show ip eigrp vrf {vrf_name} neighbors detail"
            if vrf_name != "default"
            else "show ip eigrp neighbors detail"
        )

        try:
            data_a = self.device_a.get_genie_device_object().parse(command)
        except Exception as error:
            raise ValueError(
                f"EIGRP adjacency verification failed on {self.device_a.name} "
                f"while parsing '{command}': {error}"
            )

        try:
            data_b = self.device_b.get_genie_device_object().parse(command)
        except Exception as error:
            raise ValueError(
                f"EIGRP adjacency verification failed on {self.device_b.name} "
                f"while parsing '{command}': {error}"
            )

        neighbors_on_a = self._get_active_neighbors(data_a, vrf_name)
        neighbors_on_b = self._get_active_neighbors(data_b, vrf_name)

        error_messages = []

        if self.expected_state == "Established":
            if self.ip_b not in neighbors_on_a:
                error_messages.append(
                    f"{self.device_a.name} does not see neighbor {self.ip_b} (Peer B)."
                )
            if self.ip_a not in neighbors_on_b:
                error_messages.append(
                    f"{self.device_b.name} does not see neighbor {self.ip_a} (Peer A)."
                )

        elif self.expected_state == "None":
            if self.ip_b in neighbors_on_a:
                error_messages.append(
                    f"{self.device_a.name} UNEXPECTEDLY sees neighbor {self.ip_b}."
                )
            if self.ip_a in neighbors_on_b:
                error_messages.append(
                    f"{self.device_b.name} UNEXPECTEDLY sees neighbor {self.ip_a}."
                )

        if error_messages:
            raise ValueError("Adjacency Check Failed: " + " | ".join(error_messages))

        return True
