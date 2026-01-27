import ipaddress
from typing import Dict, Tuple

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class RIP_Neighbors(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #b45309;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">RIP Neighbors</h2>
            <p style="color: #fef3c7; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Validating Routing Information Sources</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>RIP_Neighbors</strong> test validates that RIP updates are actively being received from the peer.
                Since RIP is stateless, this checks the <code>Routing Information Sources</code> table to confirm the peer is alive and sending updates.
            </p>
        </section>

        <h4 style="color: #b45309; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #f59e0b; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Validation Steps
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #d97706; margin-right: 10px;">✔</span>
                <span><strong>IP Discovery:</strong> Identifies the Peer-IP on the shared link.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #d97706; margin-right: 10px;">✔</span>
                <span><strong>Update Verification:</strong> Ensures the Peer-IP is listed as a valid source in <code>show ip protocols</code>.</span>
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
    ]

    def _find_overlap_and_ips(
        self, data_a: Dict, data_b: Dict
    ) -> Tuple[str, str, str, str]:
        device_a_networks = {}
        for interface_name, details in data_a.items():
            ipv4_config = details.get("ipv4", {})
            for ip_mask, _ in ipv4_config.items():
                if "/" not in ip_mask:
                    continue
                try:
                    interface_object = ipaddress.ip_interface(ip_mask)
                    device_a_networks[interface_object.network] = (
                        interface_name,
                        str(interface_object.ip),
                    )
                except ValueError:
                    continue

        for interface_name, details in data_b.items():
            ipv4_config = details.get("ipv4", {})
            for ip_mask, _ in ipv4_config.items():
                if "/" not in ip_mask:
                    continue
                try:
                    interface_object = ipaddress.ip_interface(ip_mask)
                    target_network = interface_object.network

                    if target_network in device_a_networks:
                        int_a, ip_a = device_a_networks[target_network]
                        int_b, ip_b = interface_name, str(interface_object.ip)
                        return int_a, ip_a, int_b, ip_b
                except ValueError:
                    continue

        return "", "", "", ""

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
                "Topology Mismatch: No shared network segment found between the two devices."
            )

        return True

    @depends_on("test_discover_topology")
    def test_verify_rip_updates(self) -> bool:
        vrf_name = getattr(self, "vrf", "default") or "default"
        command = (
            f"show ip protocols vrf {vrf_name}"
            if vrf_name != "default"
            else "show ip protocols"
        )

        try:
            device_a_protocols = (
                self.device_a.get_genie_device_object().parse(command)
            )
        except Exception as exc:
            raise ValueError(
                f"Failed to parse '{command}' on device {self.device_a.name}: {exc}"
            )

        try:
            device_b_protocols = (
                self.device_b.get_genie_device_object().parse(command)
            )
        except Exception as exc:
            raise ValueError(
                f"Failed to parse '{command}' on device {self.device_b.name}: {exc}"
            )
        def extract_active_neighbors(data: Dict) -> Dict:
            try:
                return data["protocols"]["rip"]["vrf"][vrf_name]["address_family"][
                    "ipv4"
                ]["instance"]["rip"]["neighbors"]
            except KeyError:
                return {}

        neighbors_on_a = extract_active_neighbors(device_a_protocols)
        neighbors_on_b = extract_active_neighbors(device_b_protocols)

        error_messages = []

        if self.ip_b not in neighbors_on_a:
            error_messages.append(
                f"{self.device_a.name} is not receiving routing updates from {self.device_b.name}."
            )

        if self.ip_a not in neighbors_on_b:
            error_messages.append(
                f"{self.device_b.name} is not receiving routing updates from {self.device_a.name}."
            )

        if error_messages:
            raise ValueError("RIP Session Failed: " + " | ".join(error_messages))

        return True
