import ipaddress
from typing import Dict, List, Tuple

from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class EIGRP_Neighbors(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-warning text-dark rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-diagram-2-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">EIGRP Neighbors</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-warning text-dark bg-opacity-75 border border-warning border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">EIGRP / IGP</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks your EIGRP neighbors. It automatically finds the shared connection between two devices
                        and confirms they are talking to each other. It can verify that they are fully connected or properly isolated.
                    </p>

                    <div class="p-3 rounded border border-warning border-opacity-25 bg-warning bg-opacity-10">
                        <h6 class="fw-bold text-body-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures that routers are connected and sharing routes correctly to prevent network outages.
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
                                <td class="text-body-secondary">The first EIGRP peer</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">device_b <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The second EIGRP peer</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_state <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Target State. Established or None</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">VRF context. Default is default</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">as_number</td>
                                <td class="text-body-secondary">Optional: Specific AS Number to check</td>
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

        int_a, ip_a, int_b, ip_b = self._find_overlap_and_ips(
            device_a_data, device_b_data
        )
        self.ip_a, self.ip_b = ip_a, ip_b

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
