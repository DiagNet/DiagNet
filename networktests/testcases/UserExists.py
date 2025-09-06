from .base import DiagNetTest
from genie.testbed import load


class UserExists(DiagNetTest):
    _required_params = ["device", "username"]

    def test_user_exists(self) -> bool:
        response: str = self.device.execute(f"show run | inc username {self.username} ")

        return response.startswith(f"username {self.username}")


if __name__ == "__main__":
    inventory = load("testbed.yaml")
    device = inventory.devices["R1"]
    device.connect(log_stdout=False)

    tester = UserExists()
    print(tester.run(device=device, username="cisco"))
