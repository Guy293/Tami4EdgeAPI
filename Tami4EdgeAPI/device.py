from dataclasses import dataclass
from datetime import datetime


@dataclass
class Device(object):
    id: int
    name: str
    connected: bool
    psn: str
    type: str
    device_firmware: str
