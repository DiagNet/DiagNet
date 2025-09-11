from .base import DiagNetTest
from genie.testbed import load


class CannotReach(DiagNetTest):
    _required_params = ["device:device", "ping_host:IPAddress"]
    _optional_params = ["device2", "hugo"]
    _mutually_exclusive_parameters = [("device", "ping_host")]

    def test_reachability(self) -> bool:
        response: dict = self.device.parse(f"ping {self.ping_host}")
        success_rate: float = response["ping"]["statistics"]["success_rate_percent"]

        return success_rate == 0.0


if __name__ == "__main__":
    inventory = load("testbed.yaml")
    device = inventory.devices["R1"]
    device.connect(log_stdout=False)

    tester = CannotReach()
    print(tester.run(device=device, ping_host="10.0.0.2"))
