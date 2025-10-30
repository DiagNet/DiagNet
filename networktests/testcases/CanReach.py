from .base import DiagNetTest
from devices.models import Device


class CanReach(DiagNetTest):
    _required_params = ["from_device:Device", "to_ip:IPv4"]

    def test_reachability(self) -> bool:
        device = Device.objects.get(name=self.from_device)
        response: dict = device.get_genie_device_object().parse(f"ping {self.to_ip}")
        success_rate: float = response["ping"]["statistics"]["success_rate_percent"]

        return success_rate >= 60.0
