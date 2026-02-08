import ipaddress
from typing import Dict, Tuple

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class RIP_Neighbors(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-warning text-dark rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-broadcast fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">RIP Neighbors</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-warning text-dark bg-opacity-75 border border-warning border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">RIP / Routing</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test validates that RIP routing updates are being exchanged between two devices.
                        It automatically finds the shared network link and confirms that the peer is listed as a valid source of routing information.
                    </p>

                    <div class="p-3 rounded border border-warning border-opacity-25 bg-warning bg-opacity-10">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures that the routers are talking to each other and sharing network routes properly.
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
                                <td class="fw-bold font-monospace">device_a <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The first device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">device_b <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The second device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF Context. Default is default</td>
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

        _, self.ip_a, _, self.ip_b = self._find_overlap_and_ips(
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
            device_a_protocols = self.device_a.get_genie_device_object().parse(command)
        except Exception as exc:
            raise ValueError(
                f"Failed to parse '{command}' on device {self.device_a.name}: {exc}"
            )

        try:
            device_b_protocols = self.device_b.get_genie_device_object().parse(command)
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
