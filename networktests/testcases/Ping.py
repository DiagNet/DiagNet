import re
from networktests.testcases.base import DiagNetTest, depends_on


class Ping(DiagNetTest):
    """
    <div class="card shadow-sm border-0 my-3">
        <div class="card-body p-4">

            <div class="d-flex align-items-center mb-4 border-bottom border-opacity-10 pb-3">
                <div class="bg-success text-white rounded-circle d-flex justify-content-center align-items-center shadow-sm" style="width: 50px; height: 50px;">
                    <i class="bi bi-activity fs-4"></i>
                </div>
                <div class="ms-3">
                    <h3 class="mb-0 fw-bold">Ping Connectivity Check</h3>
                    <div class="mt-1">
                        <span class="badge bg-info text-dark bg-opacity-75 border border-info border-opacity-25">Network Testcase</span>
                        <span class="badge bg-secondary bg-opacity-75 border border-secondary border-opacity-25">ICMP / Reachability</span>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <h6 class="text-uppercase text-body-secondary fw-bold small mb-2">Overview</h6>
                    <p class="text-body mb-3">
                        This test executes an <strong>ICMP Echo</strong> from a source device to a specified destination.
                        It verifies reachability and ensures the packet success rate meets the 60% threshold.
                    </p>

                    <div class="p-3 rounded border border-success border-opacity-25 bg-success bg-opacity-10">
                        <h6 class="fw-bold text-success-emphasis mb-1">
                            <i class="bi bi-check-circle-fill me-2"></i>Why run this?
                        </h6>
                        <p class="small text-body mb-0 ps-1">
                            To instantly verify network path integrity, detect packet loss, and ensure basic reachability between network nodes.
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
                                <td class="fw-bold font-monospace">source_device <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">The device initiating the ping</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">destination_hostname <span class="text-danger">*</span></td>
                                <td class="text-body-secondary">Target IP Address or Hostname</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">source_ip</td>
                                <td class="text-body-secondary">Source Interface/IP</td>
                            </tr>
                            <tr>
                                <td class="fw-bold font-monospace">count</td>
                                <td class="text-body-secondary">Packet count</td>
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
            "name": "source_device",
            "display_name": "Source Device",
            "type": "device",
            "requirement": "required",
        },
        {
            "name": "source_ip",
            "display_name": "Source IP / Interface",
            "type": "str",
            "requirement": "optional",
            "description": "Optional source IP or interface for the ping.",
        },
        {
            "name": "count",
            "display_name": "Packet Count",
            "type": "positive-number",
            "requirement": "optional",
        },
        {
            "name": "destination_hostname",
            "display_name": "Destination Hostname/IP",
            "type": "str",
            "description": "Directly specify an IP or Hostname.",
            "requirement": "required",
        },
    ]

    def test_connectivity(self) -> bool:
        if not self.source_device.can_connect():
            raise ValueError(f"Connection failed: {self.source_device.name}")
        return True

    @depends_on("test_connectivity")
    def test_ping_execution(self) -> bool:
        target_ip = self.destination_hostname
        count = getattr(self, "count", 5)
        source = getattr(self, "source_ip", None)

        cmd = f"ping {target_ip} repeat {count}"
        if source:
            cmd += f" source {source}"

        try:
            raw_output = self.source_device.get_genie_device_object().execute(cmd)
        except Exception as exc:
            raise ValueError(
                f"Ping command execution failed on device {self.source_device.name!r} "
                f"with command {cmd!r}: {exc}"
            ) from exc

        match = re.search(r"Success rate is (?P<percent>\d+) percent", raw_output)

        if not match:
            raise ValueError("Could not parse ping output.")

        success_rate = int(match.group("percent"))
        threshold = 60

        if success_rate < threshold:
            raise ValueError(
                f"Ping failed: Success rate {success_rate}% is below threshold {threshold}% "
                f"(Target: {target_ip})"
            )

        return True
