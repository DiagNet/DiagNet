from devices.models import Device
from .base import DiagNetTest


class Ping(DiagNetTest):
    """
    <div class="p-4 bg-white rounded shadow-sm" style="font-family:Arial,sans-serif; line-height:1.5; max-width:800px;">
      <h2 class="mb-3">Ping Test Class</h2>
      <p>
        The <strong>Ping</strong> test validates basic reachability between a source device and a destination
        by performing ICMP echo requests. It helps confirm that endpoints are responsive and that the
        network path between them is operational.
      </p>

      <h4 class="mt-4 mb-2">Purpose</h4>
      <p>
        This test verifies that the source device can successfully ping the destination
        (device, IPv4 address, or hostname). It is commonly used for connectivity diagnostics.
      </p>

      <h4 class="mt-4 mb-2">Parameters</h4>

      <h5 class="mt-3">Required Parameters</h5>
      <ul class="list-group mb-3">
        <li class="list-group-item">
          <strong>Source Device</strong> (<em>Device</em>)<br>
          Device initiating the ping.
        </li>
        <li class="list-group-item">
          <strong>Destination</strong> (<em>Device / IPv4 / Hostname</em>)<br>
          The target of the ping request.
        </li>
      </ul>

      <h5 class="mt-3">Optional Parameters</h5>
      <ul class="list-group mb-3">
        <li class="list-group-item"><strong>Count</strong> – Number of ICMP echo attempts.</li>
        <li class="list-group-item"><strong>Timeout</strong> – Per-ping timeout in seconds.</li>
        <li class="list-group-item"><strong>Packet Size</strong> – ICMP packet size in bytes.</li>
      </ul>

      <h4 class="mt-4 mb-2">How it Works</h4>
      <p>
        The test sends ICMP pings from the source to the destination and parses the response using
        Genie. The test passes when the success rate is at least <strong>60%</strong>.
      </p>

      <h4 class="mt-4 mb-2">Why Use This Test</h4>
      <ul>
        <li>Confirms end-to-end reachability.</li>
        <li>Quickly detects connectivity issues.</li>
        <li>Useful for health checks and automated diagnostics.</li>
      </ul>
    </div>
    """

    _params = [
        {
            "name": "source",
            "display_name": "Source Device",
            "type": "Device",
            "description": "The device from which to send the ping request",
        },
        {
            "name": "destination",
            "display_name": "Destination",
            "type": ["IPv4", "str"],
            "description": "The destination host of the ping request",
        },
        {
            "name": "count",
            "display_name": "Count",
            "type": "positive-number",
            "description": "Number of ping echo requests",
            "requirement": "optional",
        },
        {
            "name": "timeout",
            "display_name": "Timeout",
            "type": "positive-number",
            "description": "Timeout for each ping attempt (seconds)",
            "requirement": "optional",
        },
        {
            "name": "packet_size",
            "display_name": "Packet Size",
            "type": "positive-number",
            "description": "Size of the ICMP packet in bytes",
            "requirement": "optional",
        },
    ]

    def test_reachability(self) -> bool:
        try:
            destination = self.destination
            if isinstance(destination, Device):
                destination = destination.ip_address

            device = self.source.get_genie_device_object()
            response: dict = device.parse(f"ping {destination}")
            success_rate: float = response["ping"]["statistics"]["success_rate_percent"]
            device.destroy()
        except Exception as e:
            print(e)
        return success_rate >= 60.0
