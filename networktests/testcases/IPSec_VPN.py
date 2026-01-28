import re
from typing import Any, Dict, List

from unicon.core.errors import SubCommandFailure, TimeoutError
from networktests.testcases.base import DiagNetTest, depends_on

__author__ = "Luka Pacar"


class IPSec_VPN(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 800px; border: 1px solid #e2e8f0; color: #1e293b;">
        <div style="background: linear-gradient(135deg, #312e81 0%, #4338ca 100%); padding: 25px; border-radius: 12px 12px 0 0; margin: -25px -25px 25px -25px; border-bottom: 4px solid #3730a3;">
            <h2 style="color: #ffffff; margin: 0; font-weight: 700; letter-spacing: -0.025em;">IPsec Tunnel Health</h2>
            <p style="color: #e0e7ff; margin: 8px 0 0 0; font-size: 1rem; font-weight: 500;">Site-to-Site Connectivity Audit</p>
        </div>

        <section style="margin-top: 10px;">
            <p style="font-size: 1.05rem; color: #475569;">
                The <strong>IPSec_VPN</strong> test performs a deep inspection of VPN connectivity.
                It validates the stability of the secure tunnel to the peer device and audits the data plane for traffic blackholes or unidirectional flow issues.
            </p>
        </section>

        <h4 style="color: #3730a3; font-size: 1.1rem; margin-top: 30px; display: flex; align-items: center;">
            <span style="background: #4338ca; width: 8px; height: 24px; border-radius: 4px; display: inline-block; margin-right: 12px;"></span>
            Test Logic
        </h4>
        <ul style="list-style: none; padding-left: 0;">
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #4338ca; margin-right: 10px;">✔</span>
                <span><strong>Robust Discovery:</strong> Automatically correlates VPN endpoints between devices, regardless of dynamic IPs.</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #4338ca; margin-right: 10px;">✔</span>
                <span><strong>State Integrity:</strong> Confirms the crypto session is fully established (ACTIVE).</span>
            </li>
            <li style="margin-bottom: 12px; display: flex; align-items: start;">
                <span style="color: #4338ca; margin-right: 10px;">✔</span>
                <span><strong>Traffic Analysis:</strong> Detects "Silent Drops" by analyzing encapsulation/decapsulation symmetry.</span>
            </li>
        </ul>
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

        # Fetch IPsec SAs mit Retry & Timeout
        raw_ipsec = ""
        try:
            # Timeout auf 60s erhöht, da show crypto... oft langsam ist
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
