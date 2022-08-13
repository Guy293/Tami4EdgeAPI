from dataclasses import dataclass
from datetime import date


@dataclass
class QualityInfo:
    last_replacement: date
    upcoming_replacement: date
    status: str

    def __post_init__(self) -> None:
        self.last_replacement = date.fromtimestamp(self.last_replacement / 1000)
        self.upcoming_replacement = date.fromtimestamp(self.upcoming_replacement / 1000)


@dataclass
class UV(QualityInfo):
    pass


@dataclass
class Filter(QualityInfo):
    milli_litters_passed: int


@dataclass
class WaterQuality(object):
    uv: UV
    filter: Filter
