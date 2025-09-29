from .base import DiagNetTest


class Test(DiagNetTest):
    _required_params = [
        "from_ip:IPv4",
        "from_device:Device",
        "from_test:str",
        "to_ip:IP",
        "to_device:Device",
    ]
    _optional_params = [
        "amount_of_times:int",
        "amount_of_times_in_seconds:int",
        "test:ipv4",
    ]
    _mutually_exclusive_parameters = [
        ("from_ip", "from_device"),
        ("from_ip", "from_test"),
        ("from_device", "from_test"),
        ("to_ip", "to_device"),
        ("amount_of_times", "amount_of_times_in_seconds"),
    ]

    def test_reachability(self) -> bool:
        return True
