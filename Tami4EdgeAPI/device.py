from dataclasses import dataclass

from Tami4EdgeAPI import device_metadata, water_quality
from Tami4EdgeAPI.drink import Drink


@dataclass
class Device(object):
    device_metadata: device_metadata.DeviceMetadata
    water_quality: water_quality.WaterQuality
    drinks: list[Drink]
