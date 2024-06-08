from dataclasses import dataclass


@dataclass
class DeviceMetadata(object):
    id: int
    name: str
    connected: bool
    psn: str
    type: str
    device_firmware: str
