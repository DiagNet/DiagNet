from devices.models import Device
from networktests.testcases.base import DiagNetTest, depends_on
from typing import Union

__author__ = "Luka Pacar"


class BGP_Session(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-primary text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-arrow-left-right fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">BGP Session</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-info text-dark bg-opacity-75 border border-info border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">BGP / Peering</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks the connection status between BGP neighbors.
                        It ensures the session is fully established and ready to exchange routes.
                        It also verifies that the Autonomous System numbers match your configuration.
                    </p>

                    <div class="p-3 rounded border border-info border-opacity-25 bg-info bg-opacity-10">
                        <h6 class="fw-bold text-primary-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It detects broken connections and ensures neighbors are talking to each other to prevent traffic loss.
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
                                <td class="fw-bold font-monospace">two_way_check <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Test Mode: One-Way-Check or Two-Way-Check</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">vrf</td>
                                <td class="text-body-secondary">Default VRF context. Default is default</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expected_session_state <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Target State. Default is Established</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">bgp_peer_one <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The primary BGP device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">peer_one_vrf</td>
                                <td class="text-body-secondary">VRF override for Peer 1 if different from default</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">peer_one_as</td>
                                <td class="text-body-secondary">Expected AS Number for Peer 1</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">bgp_peer_two <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Remote Peer. Device Object or IP Address</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">peer_two_vrf</td>
                                <td class="text-body-secondary">VRF override for Peer 2. Two-Way-Check only</td>
                            </tr>
                             <tr>
                                <td class="fw-bold font-monospace">peer_two_as</td>
                                <td class="text-body-secondary">Expected AS Number for Peer 2</td>
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
            "name": "two_way_check",
            "display_name": "Type of Test",
            "description": "Marks if the session is supposed to be checked on both devices or only one",
            "type": "choice",
            "choices": ["One-Way-Check", "Two-Way-Check"],
            "default_choice": "One-Way-Check",
            "requirement": "required",
        },
        {
            "name": "vrf",
            "display_name": "Default VRF",
            "type": "str",
            "default": "default",
            "requirement": "optional",
        },
        {
            "name": "expected_session_state",
            "display_name": "Expected Session State",
            "type": "choice",
            "choices": [
                "Idle",
                "Connect",
                "Active",
                "OpenSent",
                "OpenConfirm",
                "Established",
            ],
            "default_choice": "Established",
            "description": "The expected type of session state between the two peers",
            "requirement": "required",
        },
        {
            "name": "bgp_peer_one",
            "display_name": "BGP Peer 1",
            "type": "Device",
            "description": "The device from which to test the routes",
            "requirement": "required",
        },
        {
            "name": "peer_one_vrf",
            "display_name": "Peer 1 - VRF Override",
            "type": "str",
            "requirement": "optional",
            "description": "Only use if Peer 1 VRF differs from Default VRF.",
        },
        {
            "name": "peer_one_as",
            "display_name": "BGP Peer 1 - AS",
            "type": "positive-number",
            "requirement": "optional",
        },
        {
            "name": "bgp_peer_two",
            "display_name": "BGP Peer 2",
            "type": [
                "Device",
                {"name": "IPv4", "condition": {"two_way_check": "One-Way-Check"}},
                {"name": "IPv6", "condition": {"two_way_check": "One-Way-Check"}},
            ],
            "requirement": "required",
        },
        {
            "name": "peer_two_vrf",
            "display_name": "Peer 2 - VRF Override",
            "type": "str",
            "requirement": "optional",
            "description": "Only use if Peer 2 VRF differs from Default VRF.",
            "required_if": {"two_way_check": "Two-Way-Check"},
        },
        {
            "name": "peer_two_as",
            "display_name": "BGP Peer 2 - AS",
            "type": "positive-number",
            "requirement": "optional",
        },
    ]

    @staticmethod
    def _get_bgp_summary(dev: Device, vrf: str = "default"):
        genie_dev = dev.get_genie_device_object()
        if not genie_dev:
            raise ValueError(f"Connection failed: {dev.name}")

        cmd = "show bgp summary" if vrf == "default" else f"show bgp vrf {vrf} summary"
        return genie_dev.parse(cmd)

    def _to_int_str(self, val) -> Union[str, None]:
        try:
            return str(int(str(val).strip())) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _validate(
        self,
        local: Device,
        remote: Union[Device, str],
        l_as: Union[str, None],
        r_as: Union[str, None],
        vrf_override: str = None,
    ) -> bool:
        vrf = vrf_override or getattr(self, "vrf", "default") or "default"
        summary = self._get_bgp_summary(local, vrf)

        if isinstance(remote, str):
            remote_ips = [remote]
        else:
            remote_ips = (
                remote.get_all_ips()
                if hasattr(remote, "get_all_ips")
                else [remote.ip_address]
            )

        # Robust dictionary traversal for multi-platform support (IOS/XR/NX-OS)
        vrf_data = (
            summary.get("instance", {}).get("default", {}).get("vrf", {}).get(vrf, {})
        )
        if not vrf_data:
            vrf_data = summary.get("vrf", {}).get(vrf, {})

        peers = vrf_data.get("neighbor", {})
        peer_ip = next((ip for ip in remote_ips if ip in peers), None)

        if not peer_ip:
            raise ValueError(
                f"Neighbor {remote_ips} not found on {local.name} (VRF: {vrf})"
            )

        peer_data = peers[peer_ip]
        af_map = peer_data.get("address_family", {})
        if not af_map:
            raise ValueError(
                f"No address family data for neighbor {peer_ip} on {local.name}"
            )

        af_data = next(iter(af_map.values()))

        # BGP State Logic
        up_down = str(af_data.get("up_down", "")).lower()
        if up_down == "never":
            actual = "Idle"
        elif any(char.isdigit() for char in up_down):
            actual = "Established"
        else:
            actual = up_down.capitalize()

        # Attribute Validation
        if l_as and self._to_int_str(af_data.get("local_as")) != l_as:
            raise ValueError(f"Local AS mismatch on {local.name}: Expected {l_as}")

        if r_as and self._to_int_str(af_data.get("as")) != r_as:
            raise ValueError(f"Remote AS mismatch on {local.name}: Expected {r_as}")

        if actual != self.expected_session_state:
            raise ValueError(
                f"State mismatch on {local.name}: Expected {self.expected_session_state}, got {actual}"
            )

        return True

    def test_device_connection(self) -> bool:
        if not self.bgp_peer_one.can_connect():
            raise ValueError(f"Could not connect to Peer 1: {self.bgp_peer_one.name}")

        if self.two_way_check == "Two-Way-Check":
            if not isinstance(self.bgp_peer_two, Device):
                raise ValueError("Two-Way-Check requires Peer 2 to be a Device object")
            if not self.bgp_peer_two.can_connect():
                raise ValueError(
                    f"Could not connect to Peer 2: {self.bgp_peer_two.name}"
                )
        return True

    @depends_on("test_device_connection")
    def test_peering_primary(self) -> bool:
        """One-way validation from Peer 1 to Peer 2."""
        return self._validate(
            local=self.bgp_peer_one,
            remote=self.bgp_peer_two,
            l_as=self._to_int_str(getattr(self, "peer_one_as", None)),
            r_as=self._to_int_str(getattr(self, "peer_two_as", None)),
            vrf_override=getattr(self, "peer_one_vrf", None),
        )

    @depends_on("test_peering_primary")
    def test_peering_secondary(self) -> bool:
        """Validates back from Peer 2 to Peer 1 only if Type is Two-Way."""
        if self.two_way_check != "Two-Way-Check":
            return True

        return self._validate(
            local=self.bgp_peer_two,
            remote=self.bgp_peer_one,
            l_as=self._to_int_str(getattr(self, "peer_two_as", None)),
            r_as=self._to_int_str(getattr(self, "peer_one_as", None)),
            vrf_override=getattr(self, "peer_two_vrf", None),
        )
