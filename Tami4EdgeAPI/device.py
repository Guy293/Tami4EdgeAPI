from dataclasses import dataclass


@dataclass
class Device(object):
    id: int
    name: str
    connected: bool
    psn: str
    type: str
    device_firmware: str
