from dataclasses import dataclass
from datetime import datetime


@dataclass
class Device(object):
    id: int
    name: str
    connected: bool
    last_heart_beat: int
    psn: str
    type: str
    device_firmware: str

    def __post_init__(self):
        self.last_heart_beat = datetime.fromtimestamp(self.last_heart_beat / 1000)
