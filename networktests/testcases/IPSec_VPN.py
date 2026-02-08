import re
from typing import Any, Dict, List

from unicon.core.errors import SubCommandFailure, TimeoutError
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class IPSec_VPN(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-dark text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-shield-lock-fill fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">IPsec VPN</h3>
                    <div class="mt-1">
                        <span class="badge text-white" style="background-color: #00267F; border-color: #00267F;">Cisco</span>
                        <span class="badge bg-dark text-white bg-opacity-75 border border-dark border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">Security / VPN</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test checks your IPsec VPN tunnels. It confirms that the secure connection is active and checks if traffic is actually flowing through it.
                    </p>

                    <div class="p-3 rounded border border-dark border-opacity-25 bg-dark bg-opacity-10">
                        <h6 class="fw-bold text-dark-emphasis mb-1">
                            <i class="bi bi-shield-check me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            It ensures that your site-to-site connection is secure and working correctly.
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
                                <td class="fw-bold font-monospace">device <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The source device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">peer_device <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The remote device</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">expect_traffic <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">If Yes, fails if no packets have passed through</td>
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
            "name": "device",
            "display_name": "Source Device",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "peer_device",
            "display_name": "VPN Peer Device",
            "type": "device",
            "description": "The remote device terminating the VPN tunnel.",
            "requirement": "required",
        },
        {
            "name": "expect_traffic",
            "display_name": "Expect Traffic Flow",
            "type": "choice",
            "choices": ["Yes", "No"],
            "default_choice": "Yes",
            "description": "If 'Yes', fails if zero packets have passed through the tunnel.",
            "requirement": "required",
        },
    ]

    def _parse_ipsec_sa(self, raw_output: str) -> List[Dict[str, Any]]:
        sas = []
        current_sa = {}

        re_peer = re.compile(r"current_peer\s+(?P<ip>[\d\.]+)")
        re_pkts = re.compile(
            r"#pkts encaps:\s+(?P<enc>\d+),\s+#pkts encrypt:\s+\d+,\s+#pkts digest:\s+\d+"
        )
        re_decaps = re.compile(r"#pkts decaps:\s+(?P<dec>\d+),")
        re_status = re.compile(r"Status:\s+(?P<status>\w+)")

        for line in raw_output.splitlines():
            line = line.strip()

            m_peer = re_peer.search(line)
            if m_peer:
                if current_sa:
                    sas.append(current_sa)

                current_sa = {
                    "peer": m_peer.group("ip"),
                    "encaps": 0,
                    "decaps": 0,
                    "status": "UNKNOWN",
                }
                continue

            if not current_sa:
                continue

            m_pkts = re_pkts.search(line)
            if m_pkts:
                current_sa["encaps"] = int(m_pkts.group("enc"))

            m_dec = re_decaps.search(line)
            if m_dec:
                current_sa["decaps"] = int(m_dec.group("dec"))

            m_stat = re_status.search(line)
            if m_stat:
                if m_stat.group("status") == "ACTIVE":
                    current_sa["status"] = "ACTIVE"

        if current_sa:
            sas.append(current_sa)

        return sas

    def _get_peer_ips(self, device) -> List[str]:
        ips = []
        try:
            output = device.get_genie_device_object().parse("show ip interface brief")
            for intf, data in output.get("interface", {}).items():
                ip = data.get("ip_address")
                if ip and ip != "unassigned":
                    ips.append(ip)
        except Exception:
            pass
        return ips

    def test_device_connection(self) -> bool:
        for dev in [self.device, self.peer_device]:
            if not dev.can_connect():
                try:
                    dev.connect()
                except Exception:
                    raise ValueError(f"Connection failed: {dev.name}")
        return True

    @depends_on("test_device_connection")
    def test_validate_tunnel(self) -> bool:
        genie_dev = self.device.get_genie_device_object()

        raw_ipsec = ""
        try:
            raw_ipsec = genie_dev.execute("show crypto ipsec sa", timeout=60)
        except (TimeoutError, SubCommandFailure, Exception):
            raise ValueError("Operational data fetch failed")

        parsed_sas = self._parse_ipsec_sa(raw_ipsec)

        # Discover Peer IP
        peer_candidates = self._get_peer_ips(self.peer_device)
        target_sa = None

        for sa in parsed_sas:
            if sa["peer"] in peer_candidates:
                target_sa = sa
                break

        if not target_sa:
            raise ValueError(
                f"Tunnel not found. No active IPsec association detected towards {self.peer_device.name}. "
                "Check IKE Phase 1 config or Routing/ACLs."
            )

        errors = []

        # State Check
        if target_sa["status"] != "ACTIVE":
            errors.append(
                f"Tunnel negotiation incomplete (State: {target_sa['status']}). "
                "Check Phase 2 Transform Sets and Lifetimes."
            )

        # Traffic Check
        if self.expect_traffic == "Yes":
            if target_sa["encaps"] == 0 and target_sa["decaps"] == 0:
                errors.append(
                    "Tunnel is idle. No traffic is entering the tunnel (Encapsulation count is 0). "
                    "Verify 'Interesting Traffic' ACLs."
                )
            elif target_sa["encaps"] > 0 and target_sa["decaps"] == 0:
                errors.append(
                    "Unidirectional traffic flow detected. The device is sending packets but receiving none. "
                )

        if errors:
            raise ValueError(" | ".join(errors))

        return True
